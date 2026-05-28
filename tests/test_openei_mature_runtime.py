from pathlib import Path

from openei import (
    AuditLogger,
    ExecutionResult,
    HttpRobotAdapter,
    Modality,
    MqttRobotAdapter,
    OpenEIRuntime,
    PerceptionEvent,
    RobotAdapter,
    RobotStatus,
    Ros2RobotAdapter,
    RuleModelProvider,
    Skill,
    SkillRegistry,
    TaskStatus,
    replay_events,
)
from openei.default_skills import build_default_registry
from openei.cli import main as cli_main


def test_standard_modalities_and_rule_provider_image_task():
    event = PerceptionEvent.image("examples/image_input/scene.jpg", prompt="根据画面执行安全动作")
    task = RuleModelProvider().parse_event(event)

    assert event.modality == Modality.IMAGE.value
    assert task.task_type.value == "vision_triggered"
    assert "vision-trigger" in task.parameters["tags"]


def test_skill_package_validate_and_load():
    package_path = Path("skill_packages/base_motion")
    errors = SkillRegistry.validate_package(package_path)
    registry = SkillRegistry()
    package = registry.load_package(package_path)

    assert errors == []
    assert package.name == "base-motion"
    assert registry.get("motion.safe_stand") is not None


def test_image_runtime_prefers_vision_skill(tmp_path):
    runtime = OpenEIRuntime(
        build_default_registry(),
        MqttRobotAdapter("mock://local"),
        audit_logger=AuditLogger(tmp_path / "audit.jsonl"),
    )
    runtime.adapter.connect()
    report = runtime.run_image("examples/image_input/scene.jpg", "根据画面执行安全动作")

    assert report.result.success is True
    assert report.skills[0].name == "vision.safe_greeting"


def test_http_and_mqtt_adapters_mock_execution():
    registry = build_default_registry()
    task = RuleModelProvider().parse_event(PerceptionEvent.text("执行 5 秒"))
    skill = registry.match(task)[0]

    http = HttpRobotAdapter("mock://robot")
    mqtt = MqttRobotAdapter("mock://local")
    assert http.connect() is True
    assert mqtt.connect() is True

    assert http.execute_skill(skill, task).success is True
    assert mqtt.execute_skill(skill, task).success is True
    assert http.history
    assert mqtt.published


def test_ros2_adapter_is_optional_when_rclpy_missing():
    adapter = Ros2RobotAdapter()
    connected = adapter.connect()
    status = adapter.status()

    assert connected in {True, False}
    assert status.mode == "ros2"
    if not connected:
        assert "rclpy" in status.details["last_error"]


def test_audit_log_and_replay(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    runtime = OpenEIRuntime(
        build_default_registry(),
        MqttRobotAdapter("mock://local"),
        audit_logger=AuditLogger(audit_path),
    )
    runtime.adapter.connect()
    report = runtime.run_text("执行 5 秒")
    events = list(replay_events(audit_path))

    assert report.task.status == TaskStatus.SUCCEEDED
    assert any(event["event_type"] == "task.succeeded" for event in events)


def test_failure_recovery_triggers_emergency_stop(tmp_path):
    class FailingAdapter(RobotAdapter):
        def __init__(self):
            self.stopped = False

        def connect(self):
            return True

        def status(self):
            return RobotStatus(True, "test", "FailingAdapter")

        def execute_skill(self, skill, task):
            return ExecutionResult(False, "failed", error="boom")

        def stop(self):
            self.stopped = True

        def close(self):
            pass

    adapter = FailingAdapter()
    registry = SkillRegistry()
    registry.register(Skill("motion.fail", "失败技能", tags=["robot-motion"]))
    runtime = OpenEIRuntime(registry, adapter, audit_logger=AuditLogger(tmp_path / "audit.jsonl"))

    report = runtime.run_text("执行 5 秒")

    assert report.result.success is False
    assert "fallback_to_safe_stop" in report.result.recovery_actions
    assert adapter.stopped is True


def test_cli_skill_validate_and_quickstart(capsys):
    assert cli_main(["skill", "validate", "skill_packages/base_motion"]) == 0
    assert "校验通过" in capsys.readouterr().out

    assert cli_main(["quickstart", "--task", "执行 5 秒"]) == 0
    assert "OpenEI 快速验证模拟器" in capsys.readouterr().out
