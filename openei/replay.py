"""
Audit log replay utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .audit import replay_events


def summarize_replay(path: str | Path) -> List[str]:
    lines: List[str] = []
    events = list(replay_events(path))
    if not events:
        return [f"没有可回放的审计事件: {path}"]

    lines.append(f"审计事件数: {len(events)}")
    for event in events:
        event_type = event.get("event_type", "")
        payload: Dict = event.get("payload", {})
        if event_type == "task.parsed":
            task = payload.get("task", {})
            lines.append(f"任务解析: {task.get('goal', '')} ({task.get('task_type', '')})")
        elif event_type == "task.planned":
            skills = ", ".join(payload.get("skills", []))
            lines.append(f"技能序列: {skills}")
        elif event_type == "skill.finished":
            lines.append(f"技能完成: {payload.get('skill', '')}")
        elif event_type == "task.succeeded":
            result = payload.get("result", {})
            lines.append(f"任务结果: {result.get('message', '成功')}")
        elif event_type == "task.failed":
            result = payload.get("result", {})
            error = result.get("error") or result.get("message", "失败")
            recovery = ", ".join(result.get("recovery_actions", []))
            lines.append(f"任务失败: {error}")
            if recovery:
                lines.append(f"恢复动作: {recovery}")
    return lines


def print_replay(path: str | Path) -> None:
    for line in summarize_replay(path):
        print(line)
