"""
Command line quickstart for the OpenEI simulator.
"""

from __future__ import annotations

import argparse
import logging

from .runtime import OpenEIRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenEI five-minute simulator")
    parser.add_argument("--task", default="执行 10 秒", help="自然语言任务")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.getLogger("openei").setLevel(logging.WARNING)
    runtime = OpenEIRuntime.from_defaults(sim=True)
    report = runtime.run_text(args.task)

    print("OpenEI 五分钟模拟器")
    print("=" * 32)
    print(f"输入事件: {report.event.modality} / {report.event.content}")
    print(f"任务目标: {report.task.goal}")
    print(f"任务状态: {report.task.status.value}")
    print(f"时长约束: {report.task.parameters.get('duration_seconds')} 秒")
    print()
    print("匹配技能:")
    for index, skill in enumerate(report.skills, start=1):
        print(f"  {index}. {skill.name} ({skill.duration_seconds:.1f} 秒)")
    print()
    print("模拟执行日志:")
    for item in report.result.trace:
        print(f"  {item}")
    print()
    print(f"执行结果: {report.result.message}")


if __name__ == "__main__":
    main()
