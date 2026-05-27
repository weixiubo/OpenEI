"""
Adapter contract checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .adapters import HttpRobotAdapter, MqttRobotAdapter, RobotAdapter, SerialRobotAdapter, SimRobotAdapter
from .results import ExecutionResult
from .skills import Skill
from .tasks import Task


@dataclass
class ContractCheck:
    name: str
    success: bool
    message: str = ""


@dataclass
class ContractReport:
    adapter_name: str
    checks: List[ContractCheck] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(check.success for check in self.checks)

    def add(self, name: str, success: bool, message: str = "") -> None:
        self.checks.append(ContractCheck(name, success, message))


class _MockSerialDriver:
    def __init__(self) -> None:
        self.commands: List[str] = []
        self.closed = False

    def get_status(self) -> dict:
        return {"connected": True, "mode": "simulation", "last_error": ""}

    def send_action_command(self, seq: str) -> bool:
        self.commands.append(str(seq))
        return True

    def close(self) -> None:
        self.closed = True


def build_contract_adapter(adapter: str, url: str = "mock://robot", broker: str = "mock://local") -> RobotAdapter:
    if adapter == "http":
        return HttpRobotAdapter(url)
    if adapter == "mqtt":
        return MqttRobotAdapter(broker)
    if adapter == "serial":
        return SerialRobotAdapter(driver=_MockSerialDriver(), wait_for_completion=False)
    return SimRobotAdapter()


def run_adapter_contract(adapter: RobotAdapter) -> ContractReport:
    report = ContractReport(adapter.__class__.__name__)
    task = Task(goal="契约测试任务", parameters={"duration_seconds": 1, "tags": ["robot-motion"]})
    skill = Skill(
        name="contract.ping",
        description="适配器契约测试技能",
        duration_seconds=0.1,
        tags=["robot-motion"],
        metadata={"seq": "001"},
        simulator=lambda context: ExecutionResult(True, "契约测试技能完成", trace=["contract skill ok"]),
    )

    try:
        report.add("connect", bool(adapter.connect()))
    except Exception as exc:
        report.add("connect", False, str(exc))

    try:
        status = adapter.status()
        report.add("status", bool(status.name and status.mode), f"{status.name}/{status.mode}")
    except Exception as exc:
        report.add("status", False, str(exc))

    try:
        capabilities = adapter.discover_capabilities()
        report.add("discover_capabilities", isinstance(capabilities, list), str(len(capabilities)))
    except Exception as exc:
        report.add("discover_capabilities", False, str(exc))

    try:
        result = adapter.execute_skill(skill, task)
        report.add("execute_skill", result.success, result.message)
    except Exception as exc:
        report.add("execute_skill", False, str(exc))

    try:
        adapter.emergency_stop()
        report.add("emergency_stop", True)
    except Exception as exc:
        report.add("emergency_stop", False, str(exc))

    try:
        adapter.close()
        report.add("close", True)
    except Exception as exc:
        report.add("close", False, str(exc))

    return report
