"""
Unified task and result models for the OpenEI runtime.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    """Task risk level used by planners and adapters."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Lifecycle state for a task moving through the runtime."""

    PENDING = "pending"
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PerceptionEvent:
    """Normalized input from text, voice, audio, vision, or sensors."""

    modality: str
    content: Any
    source: str = "user"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    @classmethod
    def text(
        cls,
        content: str,
        source: str = "cli",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PerceptionEvent":
        return cls(
            modality="text",
            content=content,
            source=source,
            metadata=metadata or {},
        )


@dataclass
class Task:
    """Task intermediate representation shared by planners and adapters."""

    goal: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    source: str = "user"
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def mark(self, status: TaskStatus) -> None:
        self.status = status


@dataclass
class ExecutionResult:
    """Adapter-neutral execution result."""

    success: bool
    message: str
    elapsed_seconds: float = 0.0
    trace: List[str] = field(default_factory=list)
    error: Optional[str] = None
