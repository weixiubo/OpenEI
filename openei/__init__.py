"""
OpenEI framework layer.

This package provides the lightweight embodied agent runtime used by the
quickstart simulator and future hardware adapters.
"""

from .adapters import RobotAdapter, RobotStatus, SerialRobotAdapter, SimRobotAdapter
from .models import ExecutionResult, PerceptionEvent, RiskLevel, Task, TaskStatus
from .runtime import OpenEIRuntime, RuntimeReport
from .skills import Skill, SkillContext, SkillRegistry

__all__ = [
    "ExecutionResult",
    "OpenEIRuntime",
    "PerceptionEvent",
    "RiskLevel",
    "RobotAdapter",
    "RobotStatus",
    "RuntimeReport",
    "SerialRobotAdapter",
    "SimRobotAdapter",
    "Skill",
    "SkillContext",
    "SkillRegistry",
    "Task",
    "TaskStatus",
]
