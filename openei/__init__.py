"""
OpenEI framework layer.

This package provides the lightweight embodied agent runtime for simulation,
hardware adapters, skills, task execution, and audit replay.
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
from .contracts import ContractCheck, ContractReport, run_adapter_contract
from .events import Modality, PerceptionEvent
from .planning import RecoveryPolicy, RulePlanner, SafetyEvaluator, SkillPlan
from .providers import (
    CloudModelProvider,
    LocalModelProvider,
    ModelProvider,
    OpenAICompatibleModelProvider,
    RuleModelProvider,
)
from .replay import print_replay, summarize_replay
from .reports import write_report
from .results import ExecutionResult, ExecutionStep
from .runtime import OpenEIRuntime, RuntimeReport
from .scenario import ScenarioRunReport, run_scenario
from .robots import RobotAdapterSpec, RobotLimits, RobotProfile, load_robot_profile, validate_robot_profile
from .skills import Skill, SkillContext, SkillPackage, SkillRegistry, load_skill_package
from .tasks import RiskLevel, SafetyPolicy, Task, TaskStatus, TaskType

__all__ = [
    "AuditLogger",
    "CloudModelProvider",
    "ContractCheck",
    "ContractReport",
    "ExecutionResult",
    "ExecutionStep",
    "HttpRobotAdapter",
    "LocalModelProvider",
    "Modality",
    "ModelProvider",
    "MqttRobotAdapter",
    "OpenEIRuntime",
    "OpenAICompatibleModelProvider",
    "PerceptionEvent",
    "RecoveryPolicy",
    "RiskLevel",
    "RobotAdapter",
    "RobotAdapterSpec",
    "RobotCapability",
    "RobotLimits",
    "RobotProfile",
    "RobotStatus",
    "Ros2RobotAdapter",
    "RuleModelProvider",
    "RulePlanner",
    "RuntimeReport",
    "SafetyEvaluator",
    "SafetyPolicy",
    "ScenarioRunReport",
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
    "load_robot_profile",
    "print_replay",
    "run_adapter_contract",
    "run_scenario",
    "replay_events",
    "summarize_replay",
    "validate_robot_profile",
    "write_report",
]
