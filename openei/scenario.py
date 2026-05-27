"""
Scenario runner for no-hardware robot development.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .adapters import HttpRobotAdapter, MqttRobotAdapter, RobotAdapter, Ros2RobotAdapter, SerialRobotAdapter, SimRobotAdapter
from .audit import AuditLogger
from .default_skills import build_default_registry
from .events import PerceptionEvent
from .providers import OpenAICompatibleModelProvider, RuleModelProvider
from .reports import runtime_markdown, runtime_payload
from .robots import load_robot_profile
from .runtime import OpenEIRuntime, RuntimeReport
from .tasks import RiskLevel, SafetyPolicy, TaskType


@dataclass
class ScenarioRunReport:
    name: str
    scenario_path: str
    runtime_report: RuntimeReport
    passed: bool
    issues: List[str] = field(default_factory=list)
    expected: Dict[str, Any] = field(default_factory=dict)


def _resolve(root: Path, value: str | None) -> Optional[Path]:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path


def _load_custom_adapter(path: Path, class_name: str) -> RobotAdapter:
    spec = importlib.util.spec_from_file_location("openei_custom_adapter", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"适配器无法加载: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adapter_class = getattr(module, class_name)
    adapter = adapter_class()
    if not isinstance(adapter, RobotAdapter):
        raise ValueError(f"适配器类必须继承 RobotAdapter: {class_name}")
    return adapter


def _build_adapter(root: Path, adapter_spec: Dict[str, Any]) -> RobotAdapter:
    adapter_type = str(adapter_spec.get("type", "sim"))
    if adapter_type == "http":
        return HttpRobotAdapter(str(adapter_spec.get("url", "mock://robot")))
    if adapter_type == "mqtt":
        return MqttRobotAdapter(str(adapter_spec.get("broker", "mock://local")))
    if adapter_type == "serial":
        return SerialRobotAdapter(wait_for_completion=False)
    if adapter_type == "ros2":
        return Ros2RobotAdapter()
    if adapter_type == "custom":
        path = _resolve(root, str(adapter_spec.get("path", "adapter.py")))
        return _load_custom_adapter(path or root / "adapter.py", str(adapter_spec.get("class", "CustomRobotAdapter")))
    return SimRobotAdapter(str(adapter_spec.get("name", "OpenEI Scenario Simulator")))


def _build_provider(provider: str):
    if provider == "openai":
        return OpenAICompatibleModelProvider()
    return RuleModelProvider()


def _apply_task_overrides(task_config: Dict[str, Any], task) -> None:
    task.parameters.update(dict(task_config.get("parameters") or {}))
    task.constraints.update(dict(task_config.get("constraints") or {}))
    task.context.update(dict(task_config.get("context") or {}))
    if "risk_level" in task_config:
        task.risk_level = RiskLevel(str(task_config["risk_level"]))
    if "task_type" in task_config:
        task.task_type = TaskType(str(task_config["task_type"]))
    if "safety_policy" in task_config:
        task.safety_policy = SafetyPolicy(str(task_config["safety_policy"]))
    if "expected_result" in task_config:
        task.expected_result = str(task_config["expected_result"])


def _evaluate_expectations(runtime_report: RuntimeReport, expected: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    expected_success = bool(expected.get("success", True))
    if runtime_report.result.success != expected_success:
        issues.append(f"执行结果不符合预期: {runtime_report.result.success}")

    skill_names = [skill.name for skill in runtime_report.skills]
    contains = list(expected.get("contains_skills") or [])
    for skill_name in contains:
        if skill_name not in skill_names:
            issues.append(f"缺少期望技能: {skill_name}")

    exact = expected.get("skills")
    if exact and skill_names != list(exact):
        issues.append(f"技能序列不符合预期: {', '.join(skill_names)}")

    message_contains = expected.get("message_contains")
    if message_contains and str(message_contains) not in runtime_report.result.message:
        issues.append(f"结果消息不包含: {message_contains}")
    return issues


def run_scenario(path: str | Path) -> ScenarioRunReport:
    scenario_path = Path(path)
    root = scenario_path.parent
    data = json.loads(scenario_path.read_text(encoding="utf-8"))
    name = str(data.get("name") or scenario_path.stem)

    registry = build_default_registry()
    for package in data.get("skill_packages", []):
        package_path = _resolve(root, str(package))
        registry.load_package(package_path or package)

    adapter = _build_adapter(root, dict(data.get("adapter") or {"type": "sim"}))
    adapter.connect()
    robot_path = _resolve(root, data.get("robot"))
    audit_path = _resolve(root, data.get("audit_log") or "logs/scenario_audit.jsonl")
    runtime = OpenEIRuntime(
        registry=registry,
        adapter=adapter,
        provider=_build_provider(str(data.get("provider", "rule"))),
        robot_profile=load_robot_profile(robot_path) if robot_path and robot_path.exists() else None,
        audit_logger=AuditLogger(audit_path or "logs/scenario_audit.jsonl"),
    )

    task_config = dict(data.get("task") or {})
    if task_config.get("image"):
        image_path = _resolve(root, str(task_config["image"]))
        event = PerceptionEvent.image(image_path or task_config["image"], prompt=str(task_config.get("text", "")), source="scenario")
    else:
        event = PerceptionEvent.text(str(task_config.get("text", "执行 10 秒")), source="scenario")

    task = runtime.parse_event(event)
    _apply_task_overrides(task_config, task)
    plan = runtime.build_plan(task)
    result = runtime.execute(task, plan.skills)
    runtime_report = RuntimeReport(event=event, task=task, skills=plan.skills, result=result, warnings=plan.warnings)
    expected = dict(data.get("expect") or {})
    issues = _evaluate_expectations(runtime_report, expected)
    return ScenarioRunReport(
        name=name,
        scenario_path=str(scenario_path),
        runtime_report=runtime_report,
        passed=not issues,
        issues=issues,
        expected=expected,
    )


def scenario_payload(report: ScenarioRunReport) -> Dict[str, Any]:
    return {
        "success": report.passed,
        "name": report.name,
        "scenario_path": report.scenario_path,
        "issues": report.issues,
        "expected": report.expected,
        "runtime": runtime_payload(report.runtime_report),
    }


def scenario_markdown(report: ScenarioRunReport) -> List[str]:
    lines = [
        f"- 场景：{report.name}",
        f"- 文件：`{report.scenario_path}`",
        f"- 结果：{'通过' if report.passed else '失败'}",
    ]
    if report.issues:
        lines.extend(["", "## 问题"])
        lines.extend(f"- {item}" for item in report.issues)
    lines.extend(["", "## 运行详情", *runtime_markdown(report.runtime_report)])
    return lines
