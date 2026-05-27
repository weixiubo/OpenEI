"""
Robot profile loading and validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class RobotLimits:
    max_duration_seconds: int = 60
    safe_stop_skill: str = "motion.safe_stand"


@dataclass
class RobotAdapterSpec:
    name: str
    mode: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RobotProfile:
    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    limits: RobotLimits = field(default_factory=RobotLimits)
    adapters: List[RobotAdapterSpec] = field(default_factory=list)
    skill_packages: List[str] = field(default_factory=list)
    source: str = "robot.yaml"

    def adapter_names(self) -> List[str]:
        return [adapter.name for adapter in self.adapters]


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value.strip("\"'")


def _load_robot_yaml(path: Path) -> Dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    data: Dict[str, Any] = {}
    current_key = ""
    current_list_item: Dict[str, Any] | None = None

    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        if indent == 0:
            key, _, value = line.partition(":")
            current_key = key.strip()
            current_list_item = None
            if value.strip():
                data[current_key] = _parse_scalar(value)
            else:
                data[current_key] = []
            continue

        if not current_key:
            continue

        if line.startswith("- "):
            value = line[2:].strip()
            if ":" in value:
                item_key, _, item_value = value.partition(":")
                current_list_item = {item_key.strip(): _parse_scalar(item_value)}
                data.setdefault(current_key, []).append(current_list_item)
            else:
                data.setdefault(current_key, []).append(_parse_scalar(value))
            continue

        key, _, value = line.partition(":")
        if isinstance(data.get(current_key), list) and current_list_item is not None:
            current_list_item[key.strip()] = _parse_scalar(value)
        elif isinstance(data.get(current_key), dict):
            data[current_key][key.strip()] = _parse_scalar(value)
        else:
            existing = data.get(current_key)
            if existing == []:
                data[current_key] = {}
            if isinstance(data[current_key], dict):
                data[current_key][key.strip()] = _parse_scalar(value)

    return data


def load_robot_profile(path: str | Path = "robot.yaml") -> RobotProfile:
    profile_path = Path(path)
    data = _load_robot_yaml(profile_path)
    limits_data = dict(data.get("limits") or {})
    adapters_data = list(data.get("adapters") or [])

    return RobotProfile(
        name=str(data.get("name") or ""),
        description=str(data.get("description") or ""),
        capabilities=[str(item) for item in data.get("capabilities", [])],
        limits=RobotLimits(
            max_duration_seconds=int(limits_data.get("max_duration_seconds", 60)),
            safe_stop_skill=str(limits_data.get("safe_stop_skill", "motion.safe_stand")),
        ),
        adapters=[
            RobotAdapterSpec(
                name=str(item.get("name", "")),
                mode=str(item.get("mode", "")),
                metadata={key: value for key, value in item.items() if key not in {"name", "mode"}},
            )
            for item in adapters_data
        ],
        skill_packages=[str(item) for item in data.get("skill_packages", [])],
        source=str(profile_path),
    )


def validate_robot_profile(path: str | Path = "robot.yaml") -> List[str]:
    errors: List[str] = []
    profile_path = Path(path)
    if not profile_path.exists():
        return [f"机器人描述文件不存在: {profile_path}"]

    try:
        profile = load_robot_profile(profile_path)
    except Exception as exc:
        return [f"机器人描述文件无法解析: {exc}"]

    if not profile.name:
        errors.append("缺少机器人名称")
    if not profile.capabilities:
        errors.append("至少需要声明一个能力")
    if profile.limits.max_duration_seconds <= 0:
        errors.append("最大任务时长必须大于 0")
    if not profile.limits.safe_stop_skill:
        errors.append("缺少安全停止技能")
    if not profile.adapters:
        errors.append("至少需要声明一个适配器")

    adapter_names = set()
    for adapter in profile.adapters:
        if not adapter.name:
            errors.append("适配器缺少名称")
        if adapter.name in adapter_names:
            errors.append(f"适配器名称重复: {adapter.name}")
        adapter_names.add(adapter.name)
        if not adapter.mode:
            errors.append(f"适配器缺少模式: {adapter.name}")

    for package in profile.skill_packages:
        package_path = Path(package)
        if not package_path.is_absolute():
            package_path = profile_path.parent / package_path
        if not package_path.exists():
            errors.append(f"技能包路径不存在: {package}")

    return errors
