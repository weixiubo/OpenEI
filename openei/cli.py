"""
Unified OpenEI command line interface.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Iterable, Optional

from .adapters import HttpRobotAdapter, MqttRobotAdapter, Ros2RobotAdapter, SerialRobotAdapter, SimRobotAdapter
from .contracts import build_contract_adapter, run_adapter_contract
from .default_skills import build_default_registry
from .events import PerceptionEvent
from .providers import OpenAICompatibleModelProvider, RuleModelProvider
from .quickstart import print_report
from .replay import print_replay
from .reports import (
    contract_markdown,
    contract_payload,
    replay_markdown,
    replay_payload,
    runtime_markdown,
    runtime_payload,
    skill_validation_payload,
    task_markdown,
    task_payload,
    validation_markdown,
    write_report,
)
from .robots import load_robot_profile, validate_robot_profile
from .runtime import OpenEIRuntime
from .scenario import run_scenario, scenario_markdown, scenario_payload
from .skills import SkillRegistry


def _build_provider(args: argparse.Namespace):
    if getattr(args, "provider", "rule") == "openai":
        return OpenAICompatibleModelProvider()
    return RuleModelProvider()


def _build_runtime(args: argparse.Namespace) -> OpenEIRuntime:
    if getattr(args, "adapter", "sim") == "serial":
        adapter = SerialRobotAdapter(wait_for_completion=False)
    elif getattr(args, "adapter", "sim") == "http":
        adapter = HttpRobotAdapter(getattr(args, "url", "mock://robot"))
    elif getattr(args, "adapter", "sim") == "mqtt":
        adapter = MqttRobotAdapter(getattr(args, "broker", "mock://local"))
    elif getattr(args, "adapter", "sim") == "ros2":
        adapter = Ros2RobotAdapter()
    else:
        adapter = SimRobotAdapter()
    adapter.connect()
    robot_path = getattr(args, "robot", "robot.yaml")
    robot_profile = load_robot_profile(robot_path) if robot_path and Path(robot_path).exists() else None
    return OpenEIRuntime(
        build_default_registry(),
        adapter,
        provider=_build_provider(args),
        robot_profile=robot_profile,
    )


def _cmd_quickstart(args: argparse.Namespace) -> int:
    logging.getLogger("openei").setLevel(logging.WARNING)
    runtime = _build_runtime(args)
    report = runtime.run_image(args.image, task=args.task) if args.image else runtime.run_text(args.task)
    print_report(report)
    write_report(args.report, "OpenEI 运行报告", runtime_payload(report), runtime_markdown(report))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    logging.getLogger("openei").setLevel(logging.WARNING)
    runtime = _build_runtime(args)
    report = runtime.run_image(args.image, task=args.task) if args.image else runtime.run_text(args.task)
    print_report(report)
    write_report(args.report, "OpenEI 运行报告", runtime_payload(report), runtime_markdown(report))
    return 0 if report.result.success else 1


def _cmd_skill_list(args: argparse.Namespace) -> int:
    registry = build_default_registry()
    if args.package:
        registry.load_package(args.package)
    for skill in registry.list_skills():
        tags = ",".join(skill.tags)
        print(f"{skill.name}\t{skill.duration_seconds:.1f}s\t{skill.risk_level.value}\t{tags}")
    return 0


def _cmd_skill_validate(args: argparse.Namespace) -> int:
    errors = SkillRegistry.validate_package(args.package)
    payload = skill_validation_payload(args.package, errors)
    details = [
        f"- `{item['name']}`：{item['risk_level']}，标签 {', '.join(item['tags'])}"
        for item in payload.get("skills", [])
    ]
    write_report(
        args.report,
        "技能包校验报告",
        payload,
        validation_markdown("技能清单", args.package, not errors, errors, details),
    )
    if errors:
        for error in errors:
            print(f"错误: {error}")
        return 1
    print("技能包校验通过")
    return 0


def _cmd_skill_create(args: argparse.Namespace) -> int:
    target = Path(args.path)
    target.mkdir(parents=True, exist_ok=True)
    manifest = target / "skill.yaml"
    if manifest.exists() and not args.force:
        print(f"文件已存在: {manifest}")
        return 1
    package_name = args.name or target.name.replace("_", "-")
    data = {
        "name": package_name,
        "version": "0.1.0",
        "description": "机器人技能包",
        "skills": [
            {
                "name": f"{package_name}.sample",
                "description": "执行一个可模拟、可适配的机器人技能",
                "duration_seconds": 2.0,
                "tags": ["robot-motion"],
                "risk_level": "low",
                "adapter_requirements": ["any"],
                "metadata": {"seq": "001", "category": "sample"},
            }
        ],
    }
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"技能包模板已创建: {manifest}")
    return 0


def _cmd_skill_install(args: argparse.Namespace) -> int:
    src = Path(args.package)
    dst_root = Path.home() / ".openei" / "skills"
    dst_root.mkdir(parents=True, exist_ok=True)
    dst = dst_root / src.name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"技能包已安装: {dst}")
    return 0


def _cmd_skill_run(args: argparse.Namespace) -> int:
    runtime = OpenEIRuntime(build_default_registry(), SimRobotAdapter())
    runtime.adapter.connect()
    report = runtime.run_text(args.task)
    print_report(report)
    return 0 if report.result.success else 1


def _adapter_template(kind: str) -> str:
    base = '''from openei import ExecutionResult, RobotAdapter, RobotCapability, RobotStatus, SkillContext


class CustomRobotAdapter(RobotAdapter):
    def __init__(self) -> None:
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def status(self) -> RobotStatus:
        return RobotStatus(self.connected, "{mode}", "CustomRobotAdapter")

    def discover_capabilities(self):
        return [RobotCapability("robot-motion", "自定义机器人运动能力", ["robot-motion"])]

    def execute_skill(self, skill, task) -> ExecutionResult:
        result = skill.simulate(SkillContext(task=task, adapter=self))
        return ExecutionResult(
            success=result.success,
            message=f"自定义适配器已执行 {{skill.name}}",
            trace=[f"[自定义适配器] {{skill.name}}"] + result.trace,
            error=result.error,
        )

    def stop(self) -> None:
        self.connected = False

    def close(self) -> None:
        self.connected = False
'''
    modes = {
        "sim": "custom-sim",
        "serial": "serial-template",
        "http": "http-template",
        "mqtt": "mqtt-template",
    }
    return base.format(mode=modes.get(kind, "custom-sim"))


def _cmd_adapter_create(args: argparse.Namespace) -> int:
    target = Path(args.name)
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / "adapter.py"
    if file_path.exists() and not args.force:
        print(f"文件已存在: {file_path}")
        return 1
    file_path.write_text(_adapter_template(args.kind), encoding="utf-8")
    print(f"适配器模板已创建: {file_path}")
    return 0


def _cmd_adapter_test(args: argparse.Namespace) -> int:
    adapter = build_contract_adapter(args.adapter, url=args.url, broker=args.broker)
    report = run_adapter_contract(adapter)
    write_report(args.report, "适配器契约测试报告", contract_payload(report), contract_markdown(report))
    print(f"适配器契约测试: {report.adapter_name}")
    for check in report.checks:
        status = "通过" if check.success else "失败"
        detail = f" - {check.message}" if check.message else ""
        print(f"{status}: {check.name}{detail}")
    return 0 if report.success else 1


def _cmd_robot_validate(args: argparse.Namespace) -> int:
    errors = validate_robot_profile(args.path)
    details = []
    if not errors:
        profile = load_robot_profile(args.path)
        details = [
            f"- 名称：{profile.name}",
            f"- 能力：{', '.join(profile.capabilities)}",
            f"- 适配器：{', '.join(profile.adapter_names())}",
            f"- 安全停止技能：{profile.limits.safe_stop_skill}",
        ]
    write_report(
        args.report,
        "机器人描述校验报告",
        {"success": not errors, "path": args.path, "errors": errors},
        validation_markdown("机器人描述", args.path, not errors, errors, details),
    )
    if errors:
        for error in errors:
            print(f"错误: {error}")
        return 1
    print("机器人描述校验通过")
    return 0


def _cmd_robot_show(args: argparse.Namespace) -> int:
    profile = load_robot_profile(args.path)
    print(f"名称: {profile.name}")
    print(f"能力: {', '.join(profile.capabilities)}")
    print(f"最大任务时长: {profile.limits.max_duration_seconds} 秒")
    print(f"安全停止技能: {profile.limits.safe_stop_skill}")
    print(f"适配器: {', '.join(profile.adapter_names())}")
    print(f"技能包: {', '.join(profile.skill_packages)}")
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    from .replay import summarize_replay

    lines = summarize_replay(args.path)
    write_report(args.report, "审计回放报告", replay_payload(args.path, lines), replay_markdown(args.path, lines))
    print_replay(args.path)
    return 0


def _cmd_model_parse(args: argparse.Namespace) -> int:
    provider = _build_provider(args)
    event = PerceptionEvent.image(args.image, prompt=args.task, source="cli") if args.image else PerceptionEvent.text(args.task, source="cli")
    task = provider.parse_event(event)
    print(f"任务目标: {task.goal}")
    print(f"任务类型: {task.task_type.value}")
    print(f"风险等级: {task.risk_level.value}")
    print(f"任务参数: {json.dumps(task.parameters, ensure_ascii=False)}")
    write_report(args.report, "模型解析报告", task_payload(task), task_markdown(task))
    return 0


def _cmd_scenario_run(args: argparse.Namespace) -> int:
    report = run_scenario(args.path)
    write_report(args.report, "场景运行报告", scenario_payload(report), scenario_markdown(report))
    print(f"场景: {report.name}")
    print(f"结果: {'通过' if report.passed else '失败'}")
    print(f"任务: {report.runtime_report.task.goal}")
    print("技能序列:")
    for skill in report.runtime_report.skills:
        print(f"  - {skill.name}")
    if report.issues:
        print("问题:")
        for issue in report.issues:
            print(f"  - {issue}")
    return 0 if report.passed else 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openei", description="OpenEI 具身 Agent 运行时")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, handler in {"quickstart": _cmd_quickstart, "run": _cmd_run}.items():
        cmd = sub.add_parser(name)
        cmd.add_argument("--task", default="执行 10 秒")
        cmd.add_argument("--image", default=None)
        cmd.add_argument("--adapter", choices=["sim", "serial", "http", "mqtt", "ros2"], default="sim")
        cmd.add_argument("--url", default="mock://robot")
        cmd.add_argument("--broker", default="mock://local")
        cmd.add_argument("--provider", choices=["rule", "openai"], default="rule")
        cmd.add_argument("--robot", default="robot.yaml")
        cmd.add_argument("--report", default=None)
        cmd.set_defaults(func=handler)

    skill = sub.add_parser("skill")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)
    skill_list = skill_sub.add_parser("list")
    skill_list.add_argument("--package", default=None)
    skill_list.set_defaults(func=_cmd_skill_list)
    skill_validate = skill_sub.add_parser("validate")
    skill_validate.add_argument("package")
    skill_validate.add_argument("--report", default=None)
    skill_validate.set_defaults(func=_cmd_skill_validate)
    skill_create = skill_sub.add_parser("create")
    skill_create.add_argument("path")
    skill_create.add_argument("--name", default=None)
    skill_create.add_argument("--force", action="store_true")
    skill_create.set_defaults(func=_cmd_skill_create)
    skill_install = skill_sub.add_parser("install")
    skill_install.add_argument("package")
    skill_install.set_defaults(func=_cmd_skill_install)
    skill_run = skill_sub.add_parser("run")
    skill_run.add_argument("--task", default="执行 10 秒")
    skill_run.set_defaults(func=_cmd_skill_run)

    adapter = sub.add_parser("adapter")
    adapter_sub = adapter.add_subparsers(dest="adapter_command", required=True)
    create = adapter_sub.add_parser("create")
    create.add_argument("name")
    create.add_argument("--kind", choices=["sim", "serial", "http", "mqtt"], default="sim")
    create.add_argument("--force", action="store_true")
    create.set_defaults(func=_cmd_adapter_create)
    test = adapter_sub.add_parser("test")
    test.add_argument("--adapter", choices=["sim", "serial", "http", "mqtt"], default="sim")
    test.add_argument("--url", default="mock://robot")
    test.add_argument("--broker", default="mock://local")
    test.add_argument("--report", default=None)
    test.set_defaults(func=_cmd_adapter_test)

    robot = sub.add_parser("robot")
    robot_sub = robot.add_subparsers(dest="robot_command", required=True)
    validate = robot_sub.add_parser("validate")
    validate.add_argument("path")
    validate.add_argument("--report", default=None)
    validate.set_defaults(func=_cmd_robot_validate)
    show = robot_sub.add_parser("show")
    show.add_argument("path")
    show.set_defaults(func=_cmd_robot_show)

    replay = sub.add_parser("replay")
    replay.add_argument("path")
    replay.add_argument("--report", default=None)
    replay.set_defaults(func=_cmd_replay)

    model = sub.add_parser("model")
    model_sub = model.add_subparsers(dest="model_command", required=True)
    parse = model_sub.add_parser("parse")
    parse.add_argument("--task", default="执行 10 秒")
    parse.add_argument("--image", default=None)
    parse.add_argument("--provider", choices=["rule", "openai"], default="rule")
    parse.add_argument("--report", default=None)
    parse.set_defaults(func=_cmd_model_parse)

    scenario = sub.add_parser("scenario")
    scenario_sub = scenario.add_subparsers(dest="scenario_command", required=True)
    scenario_run = scenario_sub.add_parser("run")
    scenario_run.add_argument("path")
    scenario_run.add_argument("--report", default=None)
    scenario_run.set_defaults(func=_cmd_scenario_run)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    logging.getLogger("openei").setLevel(logging.WARNING)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
