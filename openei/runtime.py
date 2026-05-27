"""
OpenEI lightweight embodied agent runtime.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from config import TransportMode
from utils.helpers import extract_duration_from_text

from .adapters import RobotAdapter, SerialRobotAdapter, SimRobotAdapter
from .default_skills import build_default_registry
from .models import ExecutionResult, PerceptionEvent, RiskLevel, Task, TaskStatus
from .skills import Skill, SkillRegistry


@dataclass
class RuntimeReport:
    """Structured report returned by one runtime pass."""

    event: PerceptionEvent
    task: Task
    skills: List[Skill]
    result: ExecutionResult


class OpenEIRuntime:
    """Input event -> task -> skill plan -> adapter execution."""

    def __init__(self, registry: SkillRegistry, adapter: RobotAdapter) -> None:
        self.registry = registry
        self.adapter = adapter

    @classmethod
    def from_defaults(
        cls,
        sim: bool = True,
        actions_file: Optional[str] = None,
        transport: TransportMode = TransportMode.AUTO,
    ) -> "OpenEIRuntime":
        registry = build_default_registry(actions_file)
        adapter: RobotAdapter
        if sim:
            adapter = SimRobotAdapter()
        else:
            adapter = SerialRobotAdapter(transport=transport)
        adapter.connect()
        return cls(registry=registry, adapter=adapter)

    def parse_event(self, event: PerceptionEvent) -> Task:
        text = str(event.content).strip()
        duration_seconds = extract_duration_from_text(text)
        if duration_seconds is None:
            duration_seconds = int(event.metadata.get("duration_seconds", 10))

        risk_level = RiskLevel.LOW
        if duration_seconds > 30:
            risk_level = RiskLevel.MEDIUM
        if duration_seconds > 60:
            risk_level = RiskLevel.HIGH

        return Task(
            goal=text or "执行机器人任务",
            parameters={
                "duration_seconds": duration_seconds,
                "tags": ["robot-motion"],
            },
            constraints={
                "max_duration_seconds": duration_seconds,
                "requires_hardware": False,
            },
            risk_level=risk_level,
            source=event.source,
        )

    def plan(self, task: Task) -> List[Skill]:
        duration_limit = float(task.parameters.get("duration_seconds", 10))
        matched = self.registry.match(task)
        if not matched:
            task.mark(TaskStatus.FAILED)
            return []

        stand_skill = self.registry.get("motion.立正")
        candidates = [
            skill
            for skill in matched
            if skill.name != "motion.立正" and skill.duration_seconds <= duration_limit
        ]
        candidates.sort(
            key=lambda item: (
                1 if item.metadata.get("legacy_type") == "dance" else 0,
                item.duration_seconds,
                item.name,
            )
        )

        selected: List[Skill] = []
        elapsed = 0.0
        for skill in candidates:
            if elapsed + skill.duration_seconds > duration_limit:
                continue
            selected.append(skill)
            elapsed += skill.duration_seconds
            if elapsed >= duration_limit * 0.65:
                break

        if not selected:
            shortest = matched[0]
            selected.append(shortest)
            elapsed += shortest.duration_seconds

        if stand_skill and selected[-1].name != stand_skill.name:
            selected.append(stand_skill)

        task.mark(TaskStatus.PLANNED)
        return selected

    def execute(self, task: Task, skills: List[Skill]) -> ExecutionResult:
        if not skills:
            task.mark(TaskStatus.FAILED)
            return ExecutionResult(
                success=False,
                message="没有匹配到可执行技能",
                error="empty plan",
            )

        task.mark(TaskStatus.RUNNING)
        started_at = time.perf_counter()
        trace: List[str] = []

        for index, skill in enumerate(skills, start=1):
            trace.append(f"[计划] 第 {index} 步: {skill.name}")
            result = self.adapter.execute_skill(skill, task)
            trace.extend(result.trace)
            if not result.success:
                task.mark(TaskStatus.FAILED)
                return ExecutionResult(
                    success=False,
                    message=f"技能执行失败: {skill.name}",
                    elapsed_seconds=time.perf_counter() - started_at,
                    trace=trace,
                    error=result.error or result.message,
                )

        task.mark(TaskStatus.SUCCEEDED)
        return ExecutionResult(
            success=True,
            message="任务已完成",
            elapsed_seconds=time.perf_counter() - started_at,
            trace=trace,
        )

    def run_event(self, event: PerceptionEvent) -> RuntimeReport:
        task = self.parse_event(event)
        skills = self.plan(task)
        result = self.execute(task, skills)
        return RuntimeReport(event=event, task=task, skills=skills, result=result)

    def run_text(self, text: str, source: str = "cli") -> RuntimeReport:
        return self.run_event(PerceptionEvent.text(text, source=source))
