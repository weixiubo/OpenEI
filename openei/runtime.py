"""
OpenEI lightweight embodied agent runtime.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from config import TransportMode

from .adapters import RobotAdapter, SerialRobotAdapter, SimRobotAdapter
from .audit import AuditLogger
from .default_skills import build_default_registry
from .events import PerceptionEvent
from .planning import RecoveryPolicy, RulePlanner, SkillPlan
from .providers import ModelProvider, RuleModelProvider
from .results import ExecutionResult
from .skills import Skill, SkillRegistry
from .tasks import Task, TaskStatus


@dataclass
class RuntimeReport:
    """Structured report returned by one runtime pass."""

    event: PerceptionEvent
    task: Task
    skills: List[Skill]
    result: ExecutionResult
    warnings: List[str] = field(default_factory=list)


class OpenEIRuntime:
    """Input event -> task -> skill plan -> adapter execution."""

    def __init__(
        self,
        registry: SkillRegistry,
        adapter: RobotAdapter,
        provider: Optional[ModelProvider] = None,
        planner: Optional[RulePlanner] = None,
        recovery: Optional[RecoveryPolicy] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        self.registry = registry
        self.adapter = adapter
        self.provider = provider or RuleModelProvider()
        self.planner = planner or RulePlanner(registry)
        self.recovery = recovery or RecoveryPolicy()
        self.audit_logger = audit_logger or AuditLogger()

    @classmethod
    def from_defaults(
        cls,
        sim: bool = True,
        actions_file: Optional[str] = None,
        transport: TransportMode = TransportMode.AUTO,
        audit_path: str = "logs/openei_audit.jsonl",
        audit_enabled: bool = True,
    ) -> "OpenEIRuntime":
        registry = build_default_registry(actions_file)
        adapter: RobotAdapter
        if sim:
            adapter = SimRobotAdapter()
        else:
            adapter = SerialRobotAdapter(transport=transport)
        adapter.connect()
        return cls(
            registry=registry,
            adapter=adapter,
            audit_logger=AuditLogger(audit_path, enabled=audit_enabled),
        )

    def parse_event(self, event: PerceptionEvent) -> Task:
        task = self.provider.parse_event(event)
        self.audit_logger.write("task.parsed", {"event": event, "task": task})
        return task

    def plan(self, task: Task) -> List[Skill]:
        plan = self.build_plan(task)
        return plan.skills

    def build_plan(self, task: Task) -> SkillPlan:
        plan = self.planner.plan(task)
        self.audit_logger.write(
            "task.planned",
            {
                "task": task,
                "skills": [skill.name for skill in plan.skills],
                "warnings": plan.warnings,
            },
        )
        return plan

    def execute(self, task: Task, skills: List[Skill]) -> ExecutionResult:
        if not skills:
            task.mark(TaskStatus.FAILED)
            result = ExecutionResult(False, "没有匹配到可执行技能", error="empty plan")
            self.audit_logger.write("task.failed", {"task": task, "result": result})
            return result

        task.mark(TaskStatus.RUNNING)
        started_at = time.perf_counter()
        trace: List[str] = []

        self.audit_logger.write("task.started", {"task": task, "adapter": self.adapter.status()})
        for index, skill in enumerate(skills, start=1):
            trace.append(f"[执行序列] 第 {index} 步: {skill.name}")
            self.audit_logger.write("skill.started", {"task": task, "skill": skill.name})
            result = self.adapter.execute_skill(skill, task)
            trace.extend(result.trace)
            if not result.success:
                task.mark(TaskStatus.FAILED)
                recovery_actions = self.recovery.decide(task, skill, result.error or result.message)
                if "fallback_to_safe_stop" in recovery_actions or "stop" in recovery_actions:
                    self.adapter.emergency_stop()
                failed = ExecutionResult(
                    success=False,
                    message=f"技能执行失败: {skill.name}",
                    elapsed_seconds=time.perf_counter() - started_at,
                    trace=trace,
                    error=result.error or result.message,
                    recovery_actions=recovery_actions,
                )
                self.audit_logger.write(
                    "task.failed",
                    {"task": task, "skill": skill.name, "result": failed},
                )
                return failed
            self.audit_logger.write("skill.finished", {"task": task, "skill": skill.name, "result": result})

        task.mark(TaskStatus.SUCCEEDED)
        final = ExecutionResult(
            success=True,
            message="任务已完成",
            elapsed_seconds=time.perf_counter() - started_at,
            trace=trace,
        )
        self.audit_logger.write("task.succeeded", {"task": task, "result": final})
        return final

    def run_event(self, event: PerceptionEvent) -> RuntimeReport:
        task = self.parse_event(event)
        plan = self.build_plan(task)
        result = self.execute(task, plan.skills)
        return RuntimeReport(
            event=event,
            task=task,
            skills=plan.skills,
            result=result,
            warnings=plan.warnings,
        )

    def run_text(self, text: str, source: str = "cli") -> RuntimeReport:
        return self.run_event(PerceptionEvent.text(text, source=source))

    def run_image(self, image_path: str, task: str = "根据画面执行安全动作") -> RuntimeReport:
        return self.run_event(PerceptionEvent.image(image_path, prompt=task, source="cli"))
