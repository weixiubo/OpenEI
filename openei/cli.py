"""
Unified OpenEI command line interface.
"""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path
from typing import Iterable, Optional

from .adapters import HttpRobotAdapter, MqttRobotAdapter, Ros2RobotAdapter, SerialRobotAdapter, SimRobotAdapter
from .contracts import build_contract_adapter, run_adapter_contract
from .default_skills import build_default_registry
from .providers import OpenAICompatibleModelProvider, RuleModelProvider
from .quickstart import print_report
from .replay import print_replay
from .robots import load_robot_profile, validate_robot_profile
from .runtime import OpenEIRuntime
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
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    logging.getLogger("openei").setLevel(logging.WARNING)
    runtime = _build_runtime(args)
    report = runtime.run_image(args.image, task=args.task) if args.image else runtime.run_text(args.task)
    print_report(report)
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
    if errors:
        for error in errors:
            print(f"错误: {error}")
        return 1
    print("技能包校验通过")
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


def _cmd_adapter_create(args: argparse.Namespace) -> int:
    target = Path(args.name)
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / "adapter.py"
    if file_path.exists() and not args.force:
        print(f"文件已存在: {file_path}")
        return 1
    file_path.write_text(
        '''from openei import ExecutionResult, RobotAdapter, RobotStatus


class CustomRobotAdapter(RobotAdapter):
    def connect(self) -> bool:
        return True

    def status(self) -> RobotStatus:
        return RobotStatus(True, "custom", "CustomRobotAdapter")

    def execute_skill(self, skill, task) -> ExecutionResult:
        return ExecutionResult(True, f"custom adapter executed {skill.name}")

    def stop(self) -> None:
        pass

    def close(self) -> None:
        pass
''',
        encoding="utf-8",
    )
    print(f"适配器模板已创建: {file_path}")
    return 0


def _cmd_adapter_test(args: argparse.Namespace) -> int:
    adapter = build_contract_adapter(args.adapter, url=args.url, broker=args.broker)
    report = run_adapter_contract(adapter)
    print(f"适配器契约测试: {report.adapter_name}")
    for check in report.checks:
        status = "通过" if check.success else "失败"
        detail = f" - {check.message}" if check.message else ""
        print(f"{status}: {check.name}{detail}")
    return 0 if report.success else 1


def _cmd_robot_validate(args: argparse.Namespace) -> int:
    errors = validate_robot_profile(args.path)
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
    print_replay(args.path)
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
        cmd.set_defaults(func=handler)

    skill = sub.add_parser("skill")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)
    skill_list = skill_sub.add_parser("list")
    skill_list.add_argument("--package", default=None)
    skill_list.set_defaults(func=_cmd_skill_list)
    skill_validate = skill_sub.add_parser("validate")
    skill_validate.add_argument("package")
    skill_validate.set_defaults(func=_cmd_skill_validate)
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
    create.add_argument("--force", action="store_true")
    create.set_defaults(func=_cmd_adapter_create)
    test = adapter_sub.add_parser("test")
    test.add_argument("--adapter", choices=["sim", "serial", "http", "mqtt"], default="sim")
    test.add_argument("--url", default="mock://robot")
    test.add_argument("--broker", default="mock://local")
    test.set_defaults(func=_cmd_adapter_test)

    robot = sub.add_parser("robot")
    robot_sub = robot.add_subparsers(dest="robot_command", required=True)
    validate = robot_sub.add_parser("validate")
    validate.add_argument("path")
    validate.set_defaults(func=_cmd_robot_validate)
    show = robot_sub.add_parser("show")
    show.add_argument("path")
    show.set_defaults(func=_cmd_robot_show)

    replay = sub.add_parser("replay")
    replay.add_argument("path")
    replay.set_defaults(func=_cmd_replay)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    logging.getLogger("openei").setLevel(logging.WARNING)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
