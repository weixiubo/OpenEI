"""
Structured audit logging for task execution and replay.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


class AuditLogger:
    """Append-only JSONL audit logger."""

    def __init__(self, path: str | Path = "logs/openei_audit.jsonl", enabled: bool = True) -> None:
        self.path = Path(path)
        self.enabled = enabled

    def write(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event_type": event_type,
            "timestamp": time.time(),
            "payload": _jsonable(payload),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_events(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]


def replay_events(path: str | Path) -> Iterable[Dict[str, Any]]:
    logger = AuditLogger(path, enabled=False)
    yield from logger.read_events()
