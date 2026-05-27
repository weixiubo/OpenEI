"""
Model provider abstraction for rule-based, cloud, and local task parsing.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests

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
    """Cloud model provider with the same task parsing contract."""

    name = "cloud"

    def __init__(self, fallback: Optional[ModelProvider] = None) -> None:
        self.fallback = fallback or RuleModelProvider()

    def parse_event(self, event: PerceptionEvent) -> Task:
        task = self.fallback.parse_event(event)
        task.context["provider"] = self.name
        return task


class LocalModelProvider(ModelProvider):
    """Local model provider with the same task parsing contract."""

    name = "local"

    def __init__(self, fallback: Optional[ModelProvider] = None) -> None:
        self.fallback = fallback or RuleModelProvider()

    def parse_event(self, event: PerceptionEvent) -> Task:
        task = self.fallback.parse_event(event)
        task.context["provider"] = self.name
        return task


class OpenAICompatibleModelProvider(ModelProvider):
    """OpenAI-compatible model provider."""

    name = "openai-compatible"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        fallback: Optional[ModelProvider] = None,
        client: Optional[Callable[[PerceptionEvent], Dict[str, Any]]] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("OPENEI_MODEL_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.getenv("OPENEI_MODEL_API_KEY") or ""
        self.model = model or os.getenv("OPENEI_MODEL_NAME") or "gpt-4o-mini"
        self.fallback = fallback or RuleModelProvider()
        self.client = client

    def parse_event(self, event: PerceptionEvent) -> Task:
        if not self.client and (not self.base_url or not self.api_key):
            task = self.fallback.parse_event(event)
            task.context["provider"] = self.name
            return task

        try:
            payload = self.client(event) if self.client else self._request_task(event)
            task = self._task_from_payload(payload, event)
            task.context["provider"] = self.name
            return task
        except Exception:
            task = self.fallback.parse_event(event)
            task.context["provider"] = self.name
            return task

    def _request_task(self, event: PerceptionEvent) -> Dict[str, Any]:
        prompt = (
            "Convert the robot user input into JSON with keys: "
            "goal, duration_seconds, tags, risk_level, task_type. "
            f"Input modality: {event.modality}. Content: {event.content}"
        )
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            },
            timeout=15,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    def _task_from_payload(self, payload: Dict[str, Any], event: PerceptionEvent) -> Task:
        duration = int(payload.get("duration_seconds", 10))
        risk = RiskLevel(str(payload.get("risk_level", _risk_from_duration(duration).value)))
        task_type = TaskType(str(payload.get("task_type", TaskType.MOTION.value)))
        tags = payload.get("tags") or ["robot-motion"]
        return Task(
            goal=str(payload.get("goal") or event.content or "执行机器人任务"),
            parameters={"duration_seconds": duration, "tags": tags},
            constraints={"max_duration_seconds": duration, "requires_hardware": False},
            risk_level=risk,
            source=event.source,
            task_type=task_type,
            context={"provider": self.name, "modality": event.modality},
            safety_policy=SafetyPolicy.REQUIRE_CONFIRMATION if risk == RiskLevel.HIGH else SafetyPolicy.NORMAL,
            expected_result=str(payload.get("expected_result") or "机器人完成任务"),
        )
