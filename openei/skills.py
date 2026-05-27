"""
Skill abstraction and registry for robot capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .models import ExecutionResult, Task


@dataclass
class SkillContext:
    """Runtime context passed to skill handlers and simulators."""

    task: Task
    adapter: Optional[object] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


SkillCallable = Callable[[SkillContext], ExecutionResult]


@dataclass
class Skill:
    """A robot capability that can be planned, simulated, or executed."""

    name: str
    description: str
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    duration_seconds: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[SkillCallable] = None
    simulator: Optional[SkillCallable] = None

    def execute(self, context: SkillContext) -> ExecutionResult:
        if self.handler is not None:
            return self.handler(context)
        return self.simulate(context)

    def simulate(self, context: SkillContext) -> ExecutionResult:
        if self.simulator is not None:
            return self.simulator(context)
        return ExecutionResult(
            success=True,
            message=f"模拟执行技能 {self.name}",
            trace=[f"技能 {self.name} 已完成模拟执行"],
        )

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


class SkillRegistry:
    """Registers, queries, and matches robot skills."""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> Skill:
        if not skill.name:
            raise ValueError("技能名称不能为空")
        if skill.name in self._skills:
            raise ValueError(f"技能已存在: {skill.name}")
        self._skills[skill.name] = skill
        return skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def find_by_tag(self, tag: str) -> List[Skill]:
        return [skill for skill in self._skills.values() if skill.has_tag(tag)]

    def match(self, task: Task, limit: Optional[int] = None) -> List[Skill]:
        preferred = task.parameters.get("skill")
        if preferred:
            skill = self.get(str(preferred))
            return [skill] if skill else []

        required_tags = task.parameters.get("tags") or ["robot-motion"]
        if isinstance(required_tags, str):
            required_tags = [required_tags]

        matched = [
            skill
            for skill in self._skills.values()
            if any(tag in skill.tags for tag in required_tags)
        ]
        matched.sort(key=lambda item: (item.duration_seconds, item.name))
        if limit is not None:
            return matched[:limit]
        return matched
