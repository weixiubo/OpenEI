# 技能开发

OpenEI 把机器人能力抽象成 `Skill`。同一个技能既可以在模拟器中验证，也可以通过适配器发送到真实硬件。

## 技能结构

一个技能包含：

- `name`：全局唯一名称。
- `description`：技能能力说明。
- `parameters_schema`：参数定义。
- `preconditions`：执行前置条件。
- `duration_seconds`：预计执行时长。
- `tags`：匹配标签，例如 `robot-motion`、`gesture`。
- `metadata`：硬件序号、来源文件、设备参数等扩展信息。
- `handler`：真实执行函数。
- `simulator`：模拟执行函数。

## 最小示例

```python
from openei import ExecutionResult, Skill, SkillContext, SkillRegistry


def simulate_wave(context: SkillContext) -> ExecutionResult:
    return ExecutionResult(
        success=True,
        message="模拟挥手完成",
        trace=["调用挥手技能", f"任务目标: {context.task.goal}"],
    )


registry = SkillRegistry()
registry.register(
    Skill(
        name="motion.wave",
        description="让机器人执行挥手动作",
        duration_seconds=2.0,
        tags=["robot-motion", "gesture"],
        simulator=simulate_wave,
    )
)
```

## 声明式技能包

技能包使用 `skill.yaml` 声明。该文件采用可直接解析的结构化写法：

```json
{
  "name": "my-skills",
  "version": "0.1.0",
  "skills": [
    {
      "name": "motion.wave",
      "description": "让机器人挥手",
      "duration_seconds": 2.0,
      "tags": ["robot-motion", "gesture"],
      "risk_level": "low",
      "metadata": {"seq": "009"}
    }
  ]
}
```

校验和查看：

```bash
python -m openei skill validate skill_packages/base_motion
python -m openei skill validate skill_packages/base_motion --report reports/base_motion.md
python -m openei skill list --package skill_packages/base_motion
```

## 创建技能包

```bash
python -m openei skill create my_skills
python -m openei skill validate my_skills --report reports/my_skills.md
```

生成的 `skill.yaml` 可以直接校验和加载，再按机器人能力补充技能名称、标签、风险等级和硬件元数据。

## 内置技能包

内置动作数据会被包装为统一的 `Skill`：

- `seq` 写入 `metadata`，供串口适配器下发。
- `time_ms` 转成 `duration_seconds`，供规划器估算时长。
- `type`、`energy` 写入 `tags`，供任务匹配扩展。

这样可以把控制板动作编号、技能元数据和运行时调度统一到同一套技能系统。仓库还提供 `skill_packages/` 下的官方技能包样例，用于展示生态化扩展方式。

## 匹配策略

`SkillRegistry.match(task)` 采用标签匹配：

- 未指定标签时匹配 `robot-motion`。
- 如果 `task.parameters["skill"]` 指定了技能名，则优先精确匹配。
- 如果 `task.parameters["tags"]` 指定了标签，则按标签查询技能。

同一接口可以承接模型规划、技能评分、风险过滤和上下文记忆。
