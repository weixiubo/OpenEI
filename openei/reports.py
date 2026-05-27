"""
Report rendering helpers for command line verification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .contracts import ContractReport
from .runtime import RuntimeReport
from .skills import load_skill_package
from .tasks import Task


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


def write_report(path: str | Path | None, title: str, payload: Dict[str, Any], markdown_lines: Iterable[str]) -> None:
    if not path:
        return
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.suffix.lower() == ".json":
        data = {"title": title, **_jsonable(payload)}
        report_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    text = "\n".join([f"# {title}", "", *markdown_lines]).rstrip() + "\n"
    report_path.write_text(text, encoding="utf-8")


def runtime_payload(report: RuntimeReport) -> Dict[str, Any]:
    return {
        "success": report.result.success,
        "event": report.event,
        "task": report.task,
        "skills": [
            {
                "name": skill.name,
                "description": skill.description,
                "duration_seconds": skill.duration_seconds,
                "risk_level": skill.risk_level,
                "tags": skill.tags,
                "adapter_requirements": skill.adapter_requirements,
            }
            for skill in report.skills
        ],
        "warnings": report.warnings,
        "result": report.result,
    }


def runtime_markdown(report: RuntimeReport) -> List[str]:
    lines = [
        f"- 结果：{'通过' if report.result.success else '失败'}",
        f"- 任务：{report.task.goal}",
        f"- 类型：{report.task.task_type.value}",
        f"- 风险：{report.task.risk_level.value}",
        f"- 审计编号：{report.result.audit_id}",
        "",
        "## 技能序列",
    ]
    lines.extend(f"{index}. `{skill.name}`，{skill.duration_seconds:.1f} 秒" for index, skill in enumerate(report.skills, 1))
    if report.warnings:
        lines.extend(["", "## 安全提示"])
        lines.extend(f"- {item}" for item in report.warnings)
    lines.extend(["", "## 执行轨迹"])
    lines.extend(f"- {item}" for item in report.result.trace)
    return lines


def contract_payload(report: ContractReport) -> Dict[str, Any]:
    return {
        "success": report.success,
        "adapter_name": report.adapter_name,
        "checks": report.checks,
    }


def contract_markdown(report: ContractReport) -> List[str]:
    lines = [
        f"- 结果：{'通过' if report.success else '失败'}",
        f"- 适配器：{report.adapter_name}",
        "",
        "## 检查项",
    ]
    for check in report.checks:
        lines.append(f"- {'通过' if check.success else '失败'}：`{check.name}` {check.message}".rstrip())
    return lines


def skill_validation_payload(package_path: str | Path, errors: List[str]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "success": not errors,
        "package_path": str(package_path),
        "errors": errors,
        "skills": [],
    }
    try:
        package = load_skill_package(package_path)
    except Exception:
        return payload
    payload.update({"package": package.name, "version": package.version, "description": package.description})
    payload["skills"] = [
        {
            "name": skill.name,
            "description": skill.description,
            "duration_seconds": skill.duration_seconds,
            "risk_level": skill.risk_level.value,
            "tags": skill.tags,
            "adapter_requirements": skill.adapter_requirements,
            "executable": not skill.validate_parameters({}),
        }
        for skill in package.skills
    ]
    return payload


def validation_markdown(title: str, target: str, success: bool, errors: List[str], details: Iterable[str] = ()) -> List[str]:
    lines = [
        f"- 对象：`{target}`",
        f"- 结果：{'通过' if success else '失败'}",
    ]
    if errors:
        lines.extend(["", "## 问题"])
        lines.extend(f"- {item}" for item in errors)
    detail_lines = list(details)
    if detail_lines:
        lines.extend(["", f"## {title}"])
        lines.extend(detail_lines)
    return lines


def task_payload(task: Task) -> Dict[str, Any]:
    return {
        "task": task,
        "success": True,
    }


def task_markdown(task: Task) -> List[str]:
    return [
        f"- 目标：{task.goal}",
        f"- 类型：{task.task_type.value}",
        f"- 风险：{task.risk_level.value}",
        f"- 安全策略：{task.safety_policy.value}",
        f"- 参数：`{json.dumps(_jsonable(task.parameters), ensure_ascii=False)}`",
        f"- 期望结果：{task.expected_result or ''}",
    ]


def replay_payload(path: str | Path, lines: List[str]) -> Dict[str, Any]:
    return {
        "success": bool(lines),
        "log_path": str(path),
        "summary": lines,
    }


def replay_markdown(path: str | Path, lines: List[str]) -> List[str]:
    return [
        f"- 日志：`{path}`",
        "",
        "## 回放摘要",
        *[f"- {line}" for line in lines],
    ]
