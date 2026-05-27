"""
Planning, safety evaluation, and recovery policies for the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .robots import RobotProfile
from .skills import Skill, SkillRegistry
from .tasks import RiskLevel, SafetyPolicy, Task, TaskStatus


@dataclass
class SkillPlan:
    task: Task
    skills: List[Skill]
    warnings: List[str] = field(default_factory=list)


class SafetyEvaluator:
    """Applies low-cost safety gates before execution."""

    def __init__(self, robot_profile: Optional[RobotProfile] = None) -> None:
        self.robot_profile = robot_profile

    def evaluate(self, task: Task) -> List[str]:
        warnings: List[str] = []
        duration = float(task.parameters.get("duration_seconds", 0))
        max_duration = float(task.constraints.get("max_duration_seconds", duration or 0))
        if self.robot_profile is not None:
            max_duration = min(max_duration or duration, self.robot_profile.limits.max_duration_seconds)
        if duration <= 0:
            warnings.append("任务时长必须大于 0")
        if max_duration and duration > max_duration:
            warnings.append("任务时长超过约束")
        if task.risk_level == RiskLevel.HIGH and task.safety_policy != SafetyPolicy.REQUIRE_CONFIRMATION:
            warnings.append("高风险任务需要确认策略")
        return warnings


class RulePlanner:
    """Default planner for low-cost robots and quickstarts."""

    def __init__(
        self,
        registry: SkillRegistry,
        safety: Optional[SafetyEvaluator] = None,
        robot_profile: Optional[RobotProfile] = None,
    ) -> None:
        self.registry = registry
        self.robot_profile = robot_profile
        self.safety = safety or SafetyEvaluator(robot_profile)

    def plan(self, task: Task) -> SkillPlan:
        warnings = self.safety.evaluate(task)
        matched = self.registry.match(task)
        if not matched:
            task.mark(TaskStatus.FAILED)
            return SkillPlan(task=task, skills=[], warnings=warnings + ["没有匹配到技能"])

        duration_limit = float(task.parameters.get("duration_seconds", 10))
        safe_stop_name = (
            self.robot_profile.limits.safe_stop_skill
            if self.robot_profile is not None
            else "motion.safe_stand"
        )
        stand_skill = self.registry.get(safe_stop_name) or self.registry.get("motion.safe_stand") or self.registry.get("motion.立正")
        candidates = [
            skill
            for skill in matched
            if skill.name not in {"motion.立正", "motion.safe_stand"}
            and "safe-stop" not in skill.tags
            and skill.duration_seconds <= duration_limit
        ]
        required_tags = task.parameters.get("tags") or ["robot-motion"]
        if isinstance(required_tags, str):
            required_tags = [required_tags]
        match_rank = {skill.name: index for index, skill in enumerate(matched)}
        candidates.sort(
            key=lambda item: (
                -sum(1 for tag in required_tags if tag in item.tags) if len(required_tags) > 1 else 0,
                1 if item.metadata.get("legacy_type") == "dance" else 0,
                item.risk_level.value,
                item.duration_seconds,
                match_rank.get(item.name, 9999),
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
            selected.append(matched[0])

        if stand_skill and selected[-1].name != stand_skill.name:
            selected.append(stand_skill)

        task.mark(TaskStatus.PLANNED)
        return SkillPlan(task=task, skills=selected, warnings=warnings)


class RecoveryPolicy:
    """Fixed recovery strategy for failed skill execution."""

    def decide(self, task: Task, skill: Skill, error: str) -> List[str]:
        if task.safety_policy == SafetyPolicy.REQUIRE_CONFIRMATION:
            return ["stop", "request_human_confirmation"]
        if task.risk_level == RiskLevel.HIGH:
            return ["stop"]
        return ["retry_once", "fallback_to_safe_stop"]
