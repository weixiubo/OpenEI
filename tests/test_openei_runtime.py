from openei import (
    ExecutionResult,
    OpenEIRuntime,
    PerceptionEvent,
    RobotStatus,
    SerialRobotAdapter,
    SimRobotAdapter,
    Skill,
    SkillRegistry,
    Task,
    TaskStatus,
)


def test_task_and_perception_event_models():
    event = PerceptionEvent.text("执行 10 秒", source="test")
    task = Task(goal="执行 10 秒", source=event.source)

    assert event.modality == "text"
    assert event.content == "执行 10 秒"
    assert task.status == TaskStatus.PENDING
    assert task.task_id


def test_skill_registry_registers_and_matches():
    registry = SkillRegistry()
    skill = Skill(
        name="motion.test",
        description="测试技能",
        duration_seconds=1.0,
        tags=["robot-motion"],
    )

    registry.register(skill)
    matches = registry.match(Task(goal="执行 1 秒", parameters={"tags": ["robot-motion"]}))

    assert registry.get("motion.test") is skill
    assert matches == [skill]


def test_sim_robot_adapter_executes_skill():
    adapter = SimRobotAdapter()
    adapter.connect()
    skill = Skill(
        name="motion.test",
        description="测试技能",
        simulator=lambda context: ExecutionResult(
            success=True,
            message="ok",
            trace=["模拟技能完成"],
        ),
    )

    result = adapter.execute_skill(skill, Task(goal="执行"))
    status = adapter.status()

    assert result.success is True
    assert "模拟技能完成" in result.trace
    assert isinstance(status, RobotStatus)
    assert status.connected is True


def test_serial_robot_adapter_sends_skill_sequence():
    class FakeDriver:
        def __init__(self):
            self.commands = []

        def get_status(self):
            return {
                "connected": True,
                "mode": "simulation",
                "last_error": "",
            }

        def send_action_command(self, seq):
            self.commands.append(seq)
            return True

        def close(self):
            pass

    driver = FakeDriver()
    adapter = SerialRobotAdapter(driver=driver, wait_for_completion=False)
    skill = Skill(
        name="motion.test",
        description="测试技能",
        duration_seconds=0.1,
        metadata={"seq": "123"},
    )

    result = adapter.execute_skill(skill, Task(goal="执行"))

    assert result.success is True
    assert driver.commands == ["123"]


def test_runtime_parses_text_and_runs_simulation():
    runtime = OpenEIRuntime.from_defaults(sim=True)
    report = runtime.run_text("执行 10 秒")

    assert report.task.parameters["duration_seconds"] == 10
    assert report.task.status == TaskStatus.SUCCEEDED
    assert report.result.success is True
    assert report.skills
    assert any("模拟硬件" in item for item in report.result.trace)


def test_runtime_keeps_text_task_without_api_key_or_hardware():
    runtime = OpenEIRuntime.from_defaults(sim=True)
    report = runtime.run_text("帮我执行五秒")

    assert report.task.parameters["duration_seconds"] == 5
    assert report.result.success is True
    assert report.result.error is None
