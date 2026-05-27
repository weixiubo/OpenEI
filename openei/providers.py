"""
Model provider abstraction for rule-based, cloud, and local task parsing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from utils.helpers import extract_duration_from_text

from .events import Modality, PerceptionEvent
from .tasks import RiskLevel, SafetyPolicy, Task, TaskType


class ModelProvider(ABC):
    name = "provider"

    @abstractmethod
    def parse_event(self, event: PerceptionEvent) -> Task:
        raise NotImplementedError


def _risk_from_duration(duration_seconds: int) -> RiskLevel:
    if duration_seconds > 60:
        return RiskLevel.HIGH
    if duration_seconds > 30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


class RuleModelProvider(ModelProvider):
    """No-key parser used by quickstarts, tests, and offline demos."""

    name = "rule"

    def parse_event(self, event: PerceptionEvent) -> Task:
        if event.modality in {Modality.IMAGE.value, Modality.VIDEO.value}:
            return self._parse_visual_event(event)
        if event.modality == Modality.SENSOR.value:
            return self._parse_sensor_event(event)
        return self._parse_text_like_event(event)

    def _parse_text_like_event(self, event: PerceptionEvent) -> Task:
        text = str(event.content).strip()
        duration_seconds = extract_duration_from_text(text)
        if duration_seconds is None:
            duration_seconds = int(event.metadata.get("duration_seconds", 10))
        risk_level = _risk_from_duration(duration_seconds)
        safety_policy = SafetyPolicy.REQUIRE_CONFIRMATION if risk_level == RiskLevel.HIGH else SafetyPolicy.NORMAL
        return Task(
            goal=text or "执行机器人任务",
            parameters={"duration_seconds": duration_seconds, "tags": ["robot-motion"]},
            constraints={"max_duration_seconds": duration_seconds, "requires_hardware": False},
            risk_level=risk_level,
            source=event.source,
            task_type=TaskType.MOTION,
            context={"provider": self.name, "modality": event.modality},
            safety_policy=safety_policy,
            expected_result="机器人完成安全动作序列",
        )

    def _parse_visual_event(self, event: PerceptionEvent) -> Task:
        payload: Dict[str, Any] = dict(event.content or {})
        prompt = str(payload.get("prompt") or event.metadata.get("task") or "根据画面执行安全动作")
        path = str(payload.get("path") or "")
        duration_seconds = int(event.metadata.get("duration_seconds", 10))
        if path and not Path(path).exists():
            safety_policy = SafetyPolicy.SIMULATION_ONLY
        else:
            safety_policy = SafetyPolicy.NORMAL
        return Task(
            goal=prompt,
            parameters={
                "duration_seconds": duration_seconds,
                "tags": ["vision-trigger", "robot-motion"],
                "image_path": path,
            },
            constraints={"max_duration_seconds": duration_seconds, "requires_hardware": False},
            risk_level=RiskLevel.LOW,
            source=event.source,
            task_type=TaskType.VISION_TRIGGERED,
            context={"provider": self.name, "modality": event.modality, "image_path": path},
            safety_policy=safety_policy,
            expected_result="机器人根据视觉输入选择安全技能",
        )

    def _parse_sensor_event(self, event: PerceptionEvent) -> Task:
        return Task(
            goal="根据传感器状态执行安全任务",
            parameters={"duration_seconds": 5, "tags": ["sensor-trigger", "robot-motion"]},
            constraints={"max_duration_seconds": 5, "requires_hardware": False},
            risk_level=RiskLevel.LOW,
            source=event.source,
            task_type=TaskType.SENSOR_TRIGGERED,
            context={"provider": self.name, "readings": event.content},
            expected_result="机器人完成传感器触发动作",
        )


class CloudModelProvider(ModelProvider):
    """Cloud model placeholder with an explicit safe fallback."""

    name = "cloud"

    def __init__(self, fallback: Optional[ModelProvider] = None) -> None:
        self.fallback = fallback or RuleModelProvider()

    def parse_event(self, event: PerceptionEvent) -> Task:
        task = self.fallback.parse_event(event)
        task.context["provider"] = self.name
        task.context["provider_note"] = "cloud provider is not configured; rule fallback used"
        return task


class LocalModelProvider(ModelProvider):
    """Local model placeholder with the same public contract."""

    name = "local"

    def __init__(self, fallback: Optional[ModelProvider] = None) -> None:
        self.fallback = fallback or RuleModelProvider()

    def parse_event(self, event: PerceptionEvent) -> Task:
        task = self.fallback.parse_event(event)
        task.context["provider"] = self.name
        task.context["provider_note"] = "local model is not configured; rule fallback used"
        return task
