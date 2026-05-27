# 最小机器人工程

这个样板展示一个机器人接入 OpenEI 所需的最小闭环：机器人描述、技能包、自定义适配器、场景文件、报告和审计回放。

## 运行场景

```bash
python -m openei scenario run examples/minimal_robot/scenario.json --report reports/minimal_robot.md
python -m openei replay examples/minimal_robot/logs/minimal_robot_audit.jsonl --report reports/minimal_robot_replay.md
```

## 校验技能包

```bash
python -m openei skill validate examples/minimal_robot/skills --report reports/minimal_robot_skills.md
```

## 文件说明

- `robot.yaml`：声明样板机器人的能力、限制、安全停止技能和技能包。
- `skills/skill.yaml`：声明两个技能，一个问候动作和一个安全停止动作。
- `adapter.py`：实现一个无硬件自定义适配器。
- `scenario.json`：把任务、机器人、技能包、适配器和期望结果组合成可验收场景。
