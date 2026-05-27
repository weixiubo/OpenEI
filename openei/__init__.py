"""
OpenEI framework layer.

This package provides the lightweight embodied agent runtime used by the
quickstart simulator and future hardware adapters.
"""

from .adapters import (
    HttpRobotAdapter,
    MqttRobotAdapter,
    RobotAdapter,
    RobotCapability,
    RobotStatus,
    Ros2RobotAdapter,
    SerialRobotAdapter,
    SimRobotAdapter,
)
from .audit import AuditLogger, replay_events
from .events import Modality, PerceptionEvent
from .planning import RecoveryPolicy, RulePlanner, SafetyEvaluator, SkillPlan
from .providers import CloudModelProvider, LocalModelProvider, ModelProvider, RuleModelProvider
from .results import ExecutionResult, ExecutionStep
from .runtime import OpenEIRuntime, RuntimeReport
from .skills import Skill, SkillContext, SkillPackage, SkillRegistry, load_skill_package
from .tasks import RiskLevel, SafetyPolicy, Task, TaskStatus, TaskType

__all__ = [
    "AuditLogger",
    "CloudModelProvider",
    "ExecutionResult",
    "ExecutionStep",
    "HttpRobotAdapter",
    "LocalModelProvider",
    "Modality",
    "ModelProvider",
    "MqttRobotAdapter",
    "OpenEIRuntime",
    "PerceptionEvent",
    "RecoveryPolicy",
    "RiskLevel",
    "RobotAdapter",
    "RobotCapability",
    "RobotStatus",
    "Ros2RobotAdapter",
    "RuleModelProvider",
    "RulePlanner",
    "RuntimeReport",
    "SafetyEvaluator",
    "SafetyPolicy",
    "SerialRobotAdapter",
    "SimRobotAdapter",
    "Skill",
    "SkillContext",
    "SkillPackage",
    "SkillPlan",
    "SkillRegistry",
    "Task",
    "TaskStatus",
    "TaskType",
    "load_skill_package",
    "replay_events",
]
