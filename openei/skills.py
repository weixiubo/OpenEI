"""
Skill abstraction, validation, registry, and skill package loading.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from .results import ExecutionResult
from .tasks import RiskLevel, Task


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
    postconditions: List[str] = field(default_factory=list)
    duration_seconds: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    adapter_requirements: List[str] = field(default_factory=list)
    version: str = "0.1.0"
    handler: Optional[SkillCallable] = None
    simulator: Optional[SkillCallable] = None

    def __post_init__(self) -> None:
        if not isinstance(self.risk_level, RiskLevel):
            self.risk_level = RiskLevel(str(self.risk_level))

    def validate_parameters(self, parameters: Optional[Dict[str, Any]] = None) -> List[str]:
        values = parameters or {}
        errors: List[str] = []
        for key, spec in self.parameters_schema.items():
            if isinstance(spec, dict) and spec.get("required") and key not in values:
                errors.append(f"缺少必填参数: {key}")
        return errors

    def check_preconditions(self, context: SkillContext) -> List[str]:
        errors = self.validate_parameters(context.task.parameters)
        if self.adapter_requirements and context.adapter is not None:
            mode = getattr(context.adapter.status(), "mode", "")
            if mode not in self.adapter_requirements and "any" not in self.adapter_requirements:
                errors.append(f"适配器模式不满足要求: {mode}")
        return errors

    def execute(self, context: SkillContext) -> ExecutionResult:
        errors = self.check_preconditions(context)
        if errors:
            return ExecutionResult(False, "技能前置条件不满足", error="; ".join(errors))
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


@dataclass
class SkillPackage:
    """A declarative collection of robot skills."""

    name: str
    version: str
    description: str = ""
    skills: List[Skill] = field(default_factory=list)
    source: Optional[Path] = None


def _load_manifest(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path} 需要使用 JSON 兼容的 skill.yaml 格式；当前未引入额外 YAML 依赖"
        ) from exc


def _skill_from_manifest(item: Dict[str, Any], package: SkillPackage) -> Skill:
    metadata = dict(item.get("metadata") or {})
    metadata.setdefault("package", package.name)
    metadata.setdefault("source", str(package.source) if package.source else "skill.yaml")
    return Skill(
        name=str(item["name"]),
        description=str(item.get("description", "")),
        parameters_schema=dict(item.get("parameters_schema") or {}),
        preconditions=list(item.get("preconditions") or []),
        postconditions=list(item.get("postconditions") or []),
        duration_seconds=float(item.get("duration_seconds", 1.0)),
        tags=list(item.get("tags") or ["robot-motion"]),
        metadata=metadata,
        risk_level=RiskLevel(str(item.get("risk_level", RiskLevel.LOW.value))),
        adapter_requirements=list(item.get("adapter_requirements") or ["any"]),
        version=str(item.get("version", package.version)),
    )


def load_skill_package(path: str | Path) -> SkillPackage:
    root = Path(path)
    manifest_path = root / "skill.yaml" if root.is_dir() else root
    data = _load_manifest(manifest_path)
    package = SkillPackage(
        name=str(data["name"]),
        version=str(data.get("version", "0.1.0")),
        description=str(data.get("description", "")),
        source=manifest_path,
    )
    package.skills = [_skill_from_manifest(item, package) for item in data.get("skills", [])]
    return package


class SkillRegistry:
    """Registers, queries, matches, and validates robot skills."""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}
        self._packages: Dict[str, SkillPackage] = {}

    def register(self, skill: Skill) -> Skill:
        if not skill.name:
            raise ValueError("技能名称不能为空")
        if skill.name in self._skills:
            raise ValueError(f"技能已存在: {skill.name}")
        self._skills[skill.name] = skill
        return skill

    def register_many(self, skills: Iterable[Skill]) -> None:
        for skill in skills:
            self.register(skill)

    def load_package(self, path: str | Path) -> SkillPackage:
        package = load_skill_package(path)
        self.register_many(package.skills)
        self._packages[package.name] = package
        return package

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def list_packages(self) -> List[SkillPackage]:
        return list(self._packages.values())

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
        matched.sort(
            key=lambda item: (
                -sum(1 for tag in required_tags if tag in item.tags),
                item.risk_level.value,
                item.duration_seconds,
                item.name,
            )
        )
        if limit is not None:
            return matched[:limit]
        return matched

    @staticmethod
    def validate_package(path: str | Path) -> List[str]:
        errors: List[str] = []
        try:
            package = load_skill_package(path)
        except Exception as exc:
            return [str(exc)]
        if not package.skills:
            errors.append("技能包至少需要包含一个技能")
        seen = set()
        for skill in package.skills:
            if skill.name in seen:
                errors.append(f"技能重复: {skill.name}")
            seen.add(skill.name)
            if not skill.description:
                errors.append(f"技能缺少描述: {skill.name}")
            if skill.duration_seconds <= 0:
                errors.append(f"技能时长必须大于 0: {skill.name}")
        return errors
