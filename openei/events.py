"""
Unified perception events for text, voice, audio, vision, and sensors.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class Modality(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    SENSOR = "sensor"


@dataclass
class PerceptionEvent:
    """Normalized input emitted by a channel or perception adapter."""

    modality: str
    content: Any
    source: str = "user"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.modality = self.modality.value if isinstance(self.modality, Modality) else str(self.modality)

    @classmethod
    def text(
        cls,
        content: str,
        source: str = "cli",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PerceptionEvent":
        return cls(Modality.TEXT.value, content, source=source, metadata=metadata or {})

    @classmethod
    def voice(
        cls,
        transcript: str,
        source: str = "voice",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PerceptionEvent":
        return cls(Modality.VOICE.value, transcript, source=source, metadata=metadata or {})

    @classmethod
    def audio(
        cls,
        features: Dict[str, Any],
        source: str = "audio",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PerceptionEvent":
        return cls(Modality.AUDIO.value, features, source=source, metadata=metadata or {})

    @classmethod
    def image(
        cls,
        path: str | Path,
        prompt: str = "",
        source: str = "image",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PerceptionEvent":
        payload = {"path": str(path), "prompt": prompt}
        return cls(Modality.IMAGE.value, payload, source=source, metadata=metadata or {})

    @classmethod
    def video(
        cls,
        path: str | Path,
        prompt: str = "",
        source: str = "video",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PerceptionEvent":
        payload = {"path": str(path), "prompt": prompt}
        return cls(Modality.VIDEO.value, payload, source=source, metadata=metadata or {})

    @classmethod
    def sensor(
        cls,
        readings: Dict[str, Any],
        source: str = "sensor",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PerceptionEvent":
        return cls(Modality.SENSOR.value, readings, source=source, metadata=metadata or {})
