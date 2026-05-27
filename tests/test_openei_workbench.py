import json
from pathlib import Path

from openei import run_scenario
from openei.cli import main as cli_main


def test_minimal_robot_scenario_runs():
    report = run_scenario("examples/minimal_robot/scenario.json")

    assert report.passed is True
    assert [skill.name for skill in report.runtime_report.skills] == ["minimal.wave", "minimal.safe_stand"]


def test_cli_reports_and_model_parse(tmp_path):
    quickstart_report = tmp_path / "quickstart.json"
    scenario_report = tmp_path / "scenario.md"
    skills_report = tmp_path / "skills.md"
    adapter_report = tmp_path / "adapter.md"
    robot_report = tmp_path / "robot.md"
    model_report = tmp_path / "model.md"
    replay_report = tmp_path / "replay.md"

    assert cli_main(["quickstart", "--task", "执行 10 秒", "--report", str(quickstart_report)]) == 0
    quickstart_data = json.loads(quickstart_report.read_text(encoding="utf-8"))
    assert quickstart_data["success"] is True

    assert cli_main(["scenario", "run", "examples/minimal_robot/scenario.json", "--report", str(scenario_report)]) == 0
    assert "minimal.wave" in scenario_report.read_text(encoding="utf-8")

    assert cli_main(["model", "parse", "--task", "执行 10 秒", "--provider", "rule", "--report", str(model_report)]) == 0
    assert "模型解析报告" in model_report.read_text(encoding="utf-8")

    assert cli_main(["skill", "validate", "examples/minimal_robot/skills", "--report", str(skills_report)]) == 0
    assert "minimal.safe_stand" in skills_report.read_text(encoding="utf-8")

    assert cli_main(["adapter", "test", "--adapter", "sim", "--report", str(adapter_report)]) == 0
    assert "适配器契约测试报告" in adapter_report.read_text(encoding="utf-8")

    assert cli_main(["robot", "validate", "examples/minimal_robot/robot.yaml", "--report", str(robot_report)]) == 0
    assert "Minimal Robot" in robot_report.read_text(encoding="utf-8")

    assert cli_main([
        "replay",
        "examples/minimal_robot/logs/minimal_robot_audit.jsonl",
        "--report",
        str(replay_report),
    ]) == 0
    assert "minimal.wave" in replay_report.read_text(encoding="utf-8")


def test_template_create_commands(tmp_path):
    skill_dir = tmp_path / "new_skill_pack"
    adapter_dir = tmp_path / "new_adapter"

    assert cli_main(["skill", "create", str(skill_dir)]) == 0
    assert (skill_dir / "skill.yaml").exists()
    assert cli_main(["skill", "validate", str(skill_dir)]) == 0

    assert cli_main(["adapter", "create", str(adapter_dir), "--kind", "mqtt"]) == 0
    adapter_code = (adapter_dir / "adapter.py").read_text(encoding="utf-8")
    assert "mqtt-template" in adapter_code
