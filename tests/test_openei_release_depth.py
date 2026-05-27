from pathlib import Path

from openei import (
    AuditLogger,
    OpenAICompatibleModelProvider,
    OpenEIRuntime,
    PerceptionEvent,
    RobotProfile,
    load_robot_profile,
    run_adapter_contract,
    summarize_replay,
    validate_robot_profile,
)
from openei.cli import main as cli_main
from openei.contracts import build_contract_adapter
from openei.default_skills import build_default_registry
from openei.providers import RuleModelProvider
from openei.adapters import SimRobotAdapter


def test_robot_profile_loads_and_validates():
    profile = load_robot_profile("robot.yaml")

    assert isinstance(profile, RobotProfile)
    assert profile.name == "OpenEI Reference Robot"
    assert "robot-motion" in profile.capabilities
    assert validate_robot_profile("robot.yaml") == []


def test_robot_profile_participates_in_runtime_limits(tmp_path):
    runtime = OpenEIRuntime(
        build_default_registry(),
        SimRobotAdapter(),
        robot_profile=load_robot_profile("robot.yaml"),
        audit_logger=AuditLogger(tmp_path / "audit.jsonl"),
    )
    runtime.adapter.connect()
    report = runtime.run_text("执行 10 秒")

    assert report.result.success is True
    assert report.skills[-1].name == "motion.safe_stand"


def test_replay_summarizes_audit_log(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    runtime = OpenEIRuntime(
        build_default_registry(),
        SimRobotAdapter(),
        audit_logger=AuditLogger(audit_path),
    )
    runtime.adapter.connect()
    runtime.run_text("执行 5 秒")

    summary = summarize_replay(audit_path)

    assert any("任务解析" in line for line in summary)
    assert any("技能序列" in line for line in summary)
    assert any("任务结果" in line for line in summary)


def test_adapter_contracts_cover_mock_adapters():
    for name in ["sim", "serial", "http", "mqtt"]:
        report = run_adapter_contract(build_contract_adapter(name))
        assert report.success is True


def test_openai_compatible_provider_uses_mock_client():
    provider = OpenAICompatibleModelProvider(
        client=lambda event: {
            "goal": "执行安全问候",
            "duration_seconds": 6,
            "tags": ["vision-trigger", "robot-motion"],
            "risk_level": "low",
            "task_type": "vision_triggered",
        }
    )
    task = provider.parse_event(PerceptionEvent.image("scene.jpg", "执行安全问候"))

    assert task.goal == "执行安全问候"
    assert task.task_type.value == "vision_triggered"
    assert task.parameters["duration_seconds"] == 6


def test_openai_compatible_provider_without_config_uses_rule_provider(monkeypatch):
    monkeypatch.delenv("OPENEI_MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("OPENEI_MODEL_API_KEY", raising=False)
    provider = OpenAICompatibleModelProvider(fallback=RuleModelProvider())
    task = provider.parse_event(PerceptionEvent.text("执行 7 秒"))

    assert task.parameters["duration_seconds"] == 7


def test_cli_robot_contract_and_replay(tmp_path, capsys):
    assert cli_main(["robot", "validate", "robot.yaml"]) == 0
    assert "校验通过" in capsys.readouterr().out

    assert cli_main(["robot", "show", "robot.yaml"]) == 0
    assert "OpenEI Reference Robot" in capsys.readouterr().out

    assert cli_main(["adapter", "test", "--adapter", "sim"]) == 0
    assert "适配器契约测试" in capsys.readouterr().out

    audit_path = tmp_path / "audit.jsonl"
    runtime = OpenEIRuntime(
        build_default_registry(),
        SimRobotAdapter(),
        audit_logger=AuditLogger(audit_path),
    )
    runtime.adapter.connect()
    runtime.run_text("执行 5 秒")

    assert cli_main(["replay", str(audit_path)]) == 0
    assert "审计事件数" in capsys.readouterr().out
