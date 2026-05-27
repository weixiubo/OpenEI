# 场景运行

场景文件把任务、机器人描述、技能包、适配器和期望结果组合成一个可重复验收的开发闭环。它适合用来验证新技能、新适配器和样板工程。

## 运行样板场景

```bash
python -m openei scenario run examples/minimal_robot/scenario.json --report reports/minimal_robot.md
```

场景运行会执行：

- 加载机器人描述。
- 加载默认技能库和场景技能包。
- 创建场景指定的适配器。
- 解析任务并生成技能序列。
- 执行技能并写入审计日志。
- 校验期望技能和期望结果。

## 场景文件结构

```json
{
  "name": "minimal-robot-workbench",
  "robot": "robot.yaml",
  "provider": "rule",
  "audit_log": "logs/minimal_robot_audit.jsonl",
  "adapter": {"type": "custom", "path": "adapter.py", "class": "MinimalRobotAdapter"},
  "skill_packages": ["skills"],
  "task": {
    "text": "执行样板机器人问候",
    "parameters": {"skill": "minimal.wave", "duration_seconds": 4}
  },
  "expect": {
    "success": true,
    "contains_skills": ["minimal.wave", "minimal.safe_stand"]
  }
}
```

路径默认相对场景文件所在目录解析。

## 报告和回放

```bash
python -m openei scenario run examples/minimal_robot/scenario.json --report reports/minimal_robot.md
python -m openei replay examples/minimal_robot/logs/minimal_robot_audit.jsonl --report reports/minimal_robot_replay.md
```

报告用于查看本次任务、技能序列、执行轨迹和期望结果；回放只读取审计日志，不重新执行任务。
