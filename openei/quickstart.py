"""
Command line quickstart for the OpenEI simulator.
"""

from __future__ import annotations

import argparse
import logging

from .runtime import OpenEIRuntime, RuntimeReport


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenEI five-minute simulator")
    parser.add_argument("--task", default="执行 10 秒", help="自然语言任务")
    parser.add_argument("--image", default=None, help="可选图像路径，用于视觉触发任务")
    parser.add_argument("--audit-log", default="logs/openei_audit.jsonl", help="审计日志路径")
    return parser


def print_report(report: RuntimeReport) -> None:
    print("OpenEI 快速验证模拟器")
    print("=" * 32)
    print(f"输入事件: {report.event.modality} / {report.event.content}")
    print(f"任务目标: {report.task.goal}")
    print(f"任务类型: {report.task.task_type.value}")
    print(f"任务状态: {report.task.status.value}")
    print(f"风险等级: {report.task.risk_level.value}")
    print(f"时长约束: {report.task.parameters.get('duration_seconds')} 秒")
    if report.warnings:
        print("安全提示:")
        for item in report.warnings:
            print(f"  - {item}")
    print()
    print("匹配技能:")
    for index, skill in enumerate(report.skills, start=1):
        print(f"  {index}. {skill.name} ({skill.duration_seconds:.1f} 秒)")
    print()
    print("模拟执行日志:")
    for item in report.result.trace:
        print(f"  {item}")
    print()
    print(f"审计编号: {report.result.audit_id}")
    print(f"执行结果: {report.result.message}")


def main() -> None:
    args = build_parser().parse_args()
    logging.getLogger("openei").setLevel(logging.WARNING)
    runtime = OpenEIRuntime.from_defaults(sim=True, audit_path=args.audit_log)
    report = runtime.run_image(args.image, task=args.task) if args.image else runtime.run_text(args.task)
    print_report(report)


if __name__ == "__main__":
    main()
