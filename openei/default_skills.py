"""
Default robot skill package backed by the existing action metadata CSV.
"""

from __future__ import annotations

from typing import Optional

from config import settings
from dance.action_library import ActionLibrary, DanceAction

from .results import ExecutionResult
from .skills import Skill, SkillContext, SkillRegistry


def _skill_name(action: DanceAction) -> str:
    return f"motion.{action.label}"


def create_action_skill(action: DanceAction) -> Skill:
    """Wrap a legacy action row as an OpenEI skill."""

    def simulate(context: SkillContext) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            message=f"模拟完成机器人技能 {action.label}",
            trace=[
                f"技能名: motion.{action.label}",
                f"控制序号: {action.seq}",
                f"预计耗时: {action.duration_seconds:.1f} 秒",
                f"任务目标: {context.task.goal}",
            ],
        )

    return Skill(
        name=_skill_name(action),
        description=f"机器人基础动作技能: {action.title or action.label}",
        parameters_schema={
            "seq": "底层控制板动作序号",
            "duration_seconds": "预计执行时长",
        },
        preconditions=["机器人已连接或模拟器已启动"],
        duration_seconds=action.duration_seconds,
        tags=["robot-motion", action.type, action.energy],
        adapter_requirements=["any"],
        metadata={
            "seq": action.seq,
            "label": action.label,
            "title": action.title,
            "legacy_type": action.type,
            "source": "data/actions.csv",
        },
        simulator=simulate,
    )


def build_default_registry(actions_file: Optional[str] = None) -> SkillRegistry:
    registry = SkillRegistry()
    library = ActionLibrary(actions_file)
    for action in library.get_all_actions():
        registry.register(create_action_skill(action))
    packages_root = settings.project_root / "skill_packages"
    if packages_root.exists():
        for manifest in sorted(packages_root.glob("*/skill.yaml")):
            try:
                registry.load_package(manifest)
            except ValueError:
                continue
    return registry
