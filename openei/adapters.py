"""
Robot adapter interface and built-in simulation, serial, network, and ROS 2 adapters.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import TransportMode
from dance.serial_driver import SerialDriver

from .results import ExecutionResult
from .skills import Skill, SkillContext
from .tasks import Task


@dataclass
class RobotCapability:
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RobotStatus:
    """Adapter-neutral robot status snapshot."""

    connected: bool
    mode: str
    name: str
    healthy: bool = True
    battery_percent: Optional[float] = None
    current_task_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class RobotAdapter(ABC):
    """Base adapter contract for simulated or physical robots."""

    @abstractmethod
    def connect(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> RobotStatus:
        raise NotImplementedError

    @abstractmethod
    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    def discover_capabilities(self) -> List[RobotCapability]:
        return []

    def health_check(self) -> RobotStatus:
        return self.status()

    def emergency_stop(self) -> None:
        self.stop()


class SimRobotAdapter(RobotAdapter):
    """No-hardware adapter used by quickstarts and tests."""

    def __init__(self, name: str = "OpenEI Simulator") -> None:
        self.name = name
        self.connected = False
        self.logs: List[str] = []
        self.status_events: List[Dict[str, Any]] = []
        self.current_task_id: Optional[str] = None

    def _emit(self, event: str, **metadata: Any) -> None:
        payload = {"event": event, "timestamp": time.time(), **metadata}
        self.status_events.append(payload)
        self.logs.append(f"[模拟状态] {event}: {metadata}" if metadata else f"[模拟状态] {event}")

    def connect(self) -> bool:
        self.connected = True
        self._emit("connected", mode="simulation")
        return True

    def status(self) -> RobotStatus:
        return RobotStatus(
            connected=self.connected,
            mode="simulation",
            name=self.name,
            healthy=True,
            current_task_id=self.current_task_id,
            details={"log_count": len(self.logs), "event_count": len(self.status_events)},
        )

    def discover_capabilities(self) -> List[RobotCapability]:
        return [
            RobotCapability("robot-motion", "模拟机器人基础运动能力", ["robot-motion"]),
            RobotCapability("gesture", "模拟手势动作能力", ["gesture"]),
            RobotCapability("vision-trigger", "模拟视觉触发任务能力", ["vision-trigger"]),
        ]

    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        if not self.connected:
            self.connect()

        started_at = time.perf_counter()
        self.current_task_id = task.task_id
        self._emit("skill_started", task_id=task.task_id, skill=skill.name)
        context = SkillContext(task=task, adapter=self, metadata={"mode": "simulation"})
        result = skill.simulate(context)
        elapsed = time.perf_counter() - started_at
        self._emit("skill_finished", task_id=task.task_id, skill=skill.name, success=result.success)
        trace = [f"[模拟硬件] 调用技能 {skill.name}"] + result.trace
        self.logs.extend(trace)
        self.current_task_id = None
        return ExecutionResult(
            success=result.success,
            message=result.message,
            elapsed_seconds=elapsed,
            trace=trace,
            error=result.error,
            recovery_actions=result.recovery_actions,
            structured_trace=result.structured_trace,
        )

    def stop(self) -> None:
        self._emit("stopped", task_id=self.current_task_id)
        self.current_task_id = None

    def close(self) -> None:
        self.connected = False
        self._emit("closed")


class SerialRobotAdapter(RobotAdapter):
    """Adapter wrapper around the existing serial command transport."""

    def __init__(
        self,
        driver: Optional[SerialDriver] = None,
        transport: TransportMode = TransportMode.AUTO,
        wait_for_completion: bool = True,
    ) -> None:
        self.driver = driver or SerialDriver(transport=transport)
        self.wait_for_completion = wait_for_completion

    def connect(self) -> bool:
        return self.driver.get_status()["mode"] in {"hardware", "simulation"}

    def status(self) -> RobotStatus:
        status = self.driver.get_status()
        return RobotStatus(
            connected=bool(status["connected"]),
            mode=status["mode"],
            name="SerialRobotAdapter",
            healthy=status["mode"] in {"hardware", "simulation"},
            details=status,
        )

    def discover_capabilities(self) -> List[RobotCapability]:
        return [RobotCapability("robot-motion", "串口控制板动作序号执行能力", ["robot-motion"])]

    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        started_at = time.perf_counter()
        seq = skill.metadata.get("seq")
        if seq is None:
            return skill.execute(SkillContext(task=task, adapter=self))

        ok = self.driver.send_action_command(str(seq))
        if ok and self.wait_for_completion:
            time.sleep(max(0.0, skill.duration_seconds))

        elapsed = time.perf_counter() - started_at
        trace = [
            f"[串口适配器] 技能 {skill.name}",
            f"[串口适配器] 下发序号 {seq}",
        ]
        return ExecutionResult(
            success=ok,
            message=f"技能 {skill.name} 已下发" if ok else f"技能 {skill.name} 下发失败",
            elapsed_seconds=elapsed,
            trace=trace,
            error=None if ok else self.driver.get_status().get("last_error", "serial failed"),
        )

    def stop(self) -> None:
        self.driver.send_action_command("001")

    def close(self) -> None:
        self.driver.close()


class HttpRobotAdapter(RobotAdapter):
    """HTTP adapter for low-cost controllers that expose REST endpoints."""

    def __init__(self, base_url: str, timeout_seconds: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.connected = False
        self._mock = self.base_url.startswith("mock://")
        self.history: List[Dict[str, Any]] = []

    def _request(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._mock:
            record = {"path": path, "payload": payload or {}}
            self.history.append(record)
            return {"ok": True, "mock": True, **record}

        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if payload is not None else "GET",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8")
        return json.loads(body) if body else {"ok": True}

    def connect(self) -> bool:
        try:
            self._request("/status")
            self.connected = True
            return True
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            self.connected = False
            return False

    def status(self) -> RobotStatus:
        return RobotStatus(
            connected=self.connected,
            mode="http-mock" if self._mock else "http",
            name="HttpRobotAdapter",
            healthy=self.connected,
            details={"base_url": self.base_url},
        )

    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        payload = {
            "task_id": task.task_id,
            "skill": skill.name,
            "parameters": task.parameters,
            "metadata": skill.metadata,
        }
        try:
            response = self._request("/execute", payload)
            ok = bool(response.get("ok", True))
            return ExecutionResult(
                ok,
                f"HTTP 技能 {skill.name} 已执行" if ok else f"HTTP 技能 {skill.name} 执行失败",
                trace=[f"[HTTP] {skill.name}", json.dumps(response, ensure_ascii=False)],
                error=None if ok else str(response),
            )
        except Exception as exc:
            return ExecutionResult(False, f"HTTP 技能 {skill.name} 执行失败", error=str(exc))

    def stop(self) -> None:
        self._request("/stop", {})

    def close(self) -> None:
        self.connected = False


class MqttRobotAdapter(RobotAdapter):
    """MQTT adapter with a mock mode and optional paho-mqtt support."""

    def __init__(self, broker_url: str = "mock://local", topic: str = "openei/robot/commands") -> None:
        self.broker_url = broker_url
        self.topic = topic
        self.connected = False
        self.published: List[Dict[str, Any]] = []
        self._mock = broker_url.startswith("mock://")

    def connect(self) -> bool:
        if self._mock:
            self.connected = True
            return True
        try:
            import paho.mqtt.client  # type: ignore  # noqa: F401
        except ImportError:
            self.connected = False
            return False
        self.connected = True
        return True

    def status(self) -> RobotStatus:
        return RobotStatus(
            connected=self.connected,
            mode="mqtt-mock" if self._mock else "mqtt",
            name="MqttRobotAdapter",
            healthy=self.connected,
            details={"broker_url": self.broker_url, "topic": self.topic},
        )

    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        payload = {
            "task_id": task.task_id,
            "skill": skill.name,
            "parameters": task.parameters,
            "metadata": skill.metadata,
        }
        self.published.append({"topic": self.topic, "payload": payload})
        return ExecutionResult(
            success=self.connected,
            message=f"MQTT 技能 {skill.name} 已发布" if self.connected else "MQTT 未连接",
            trace=[f"[MQTT] {self.topic} <- {skill.name}"],
            error=None if self.connected else "mqtt not connected",
        )

    def stop(self) -> None:
        self.published.append({"topic": self.topic, "payload": {"command": "stop"}})

    def close(self) -> None:
        self.connected = False


class Ros2RobotAdapter(RobotAdapter):
    """Optional ROS 2 adapter template; rclpy is not a default dependency."""

    def __init__(self, node_name: str = "openei_robot_adapter") -> None:
        self.node_name = node_name
        self.connected = False
        self.last_error = ""

    def connect(self) -> bool:
        try:
            import rclpy  # type: ignore  # noqa: F401
        except ImportError:
            self.last_error = "rclpy 未安装；请按 ROS 2 文档安装后再启用该适配器"
            self.connected = False
            return False
        self.connected = True
        return True

    def status(self) -> RobotStatus:
        return RobotStatus(
            connected=self.connected,
            mode="ros2",
            name="Ros2RobotAdapter",
            healthy=self.connected,
            details={"node_name": self.node_name, "last_error": self.last_error},
        )

    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        if not self.connected:
            return ExecutionResult(False, "ROS 2 适配器未连接", error=self.last_error)
        return ExecutionResult(
            True,
            f"ROS 2 技能模板已接收 {skill.name}",
            trace=[f"[ROS2] {skill.name}"],
        )

    def stop(self) -> None:
        pass

    def close(self) -> None:
        self.connected = False
