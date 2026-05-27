"""
Execution result and structured trace models.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionStep:
    name: str
    status: str
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Adapter-neutral execution result."""

    success: bool
    message: str
    elapsed_seconds: float = 0.0
    trace: List[str] = field(default_factory=list)
    error: Optional[str] = None
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recovery_actions: List[str] = field(default_factory=list)
    structured_trace: List[ExecutionStep] = field(default_factory=list)

    def add_step(self, name: str, status: str, message: str = "", **metadata: Any) -> None:
        self.structured_trace.append(
            ExecutionStep(name=name, status=status, message=message, metadata=metadata)
        )
        if message:
            self.trace.append(message)
