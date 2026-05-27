"""
Robot adapter interface and built-in simulation / serial adapters.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import TransportMode
from dance.serial_driver import SerialDriver

from .models import ExecutionResult, Task
from .skills import Skill, SkillContext


@dataclass
class RobotStatus:
    """Adapter-neutral robot status snapshot."""

    connected: bool
    mode: str
    name: str
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


class SimRobotAdapter(RobotAdapter):
    """No-hardware adapter used by the five-minute quickstart."""

    def __init__(self, name: str = "OpenEI Simulator") -> None:
        self.name = name
        self.connected = False
        self.logs: List[str] = []

    def connect(self) -> bool:
        self.connected = True
        self.logs.append("模拟机器人已连接")
        return True

    def status(self) -> RobotStatus:
        return RobotStatus(
            connected=self.connected,
            mode="simulation",
            name=self.name,
            details={"log_count": len(self.logs)},
        )

    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        if not self.connected:
            self.connect()

        started_at = time.perf_counter()
        context = SkillContext(task=task, adapter=self, metadata={"mode": "simulation"})
        result = skill.simulate(context)
        elapsed = time.perf_counter() - started_at
        trace = [f"[模拟硬件] 调用技能 {skill.name}"] + result.trace
        self.logs.extend(trace)
        return ExecutionResult(
            success=result.success,
            message=result.message,
            elapsed_seconds=elapsed,
            trace=trace,
            error=result.error,
        )

    def stop(self) -> None:
        self.logs.append("模拟机器人已停止当前任务")

    def close(self) -> None:
        self.connected = False
        self.logs.append("模拟机器人连接已关闭")


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
            details=status,
        )

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
