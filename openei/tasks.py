"""
Task intermediate representation and safety metadata.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    GENERAL = "general"
    MOTION = "motion"
    INSPECTION = "inspection"
    VISION_TRIGGERED = "vision_triggered"
    SENSOR_TRIGGERED = "sensor_triggered"
    SAFETY = "safety"


class SafetyPolicy(str, Enum):
    NORMAL = "normal"
    REQUIRE_CONFIRMATION = "require_confirmation"
    STOP_ON_FAILURE = "stop_on_failure"
    SIMULATION_ONLY = "simulation_only"


@dataclass
class Task:
    """Task IR shared by planners, model providers, and adapters."""

    goal: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    source: str = "user"
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.MOTION
    context: Dict[str, Any] = field(default_factory=dict)
    safety_policy: SafetyPolicy = SafetyPolicy.NORMAL
    expected_result: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.risk_level, RiskLevel):
            self.risk_level = RiskLevel(str(self.risk_level))
        if not isinstance(self.status, TaskStatus):
            self.status = TaskStatus(str(self.status))
        if not isinstance(self.task_type, TaskType):
            self.task_type = TaskType(str(self.task_type))
        if not isinstance(self.safety_policy, SafetyPolicy):
            self.safety_policy = SafetyPolicy(str(self.safety_policy))

    def mark(self, status: TaskStatus) -> None:
        self.status = status
