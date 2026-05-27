# 技能开发

OpenEI 把机器人能力抽象成 `Skill`。技能可以先支持模拟执行，再逐步接入真实硬件。

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

## 默认技能包

当前默认技能包来自 `data/actions.csv`。每一行动作元数据会被包装为一个 `Skill`：

- `seq` 写入 `metadata`，供串口适配器下发。
- `time_ms` 转成 `duration_seconds`，供规划器估算时长。
- `type`、`energy` 写入 `tags`，供后续任务匹配扩展。

这样既保留原控制板动作编号，又能把历史动作库迁移进通用技能系统。

## 匹配策略

第一阶段的 `SkillRegistry.match(task)` 采用标签匹配：

- 默认匹配 `robot-motion`。
- 如果 `task.parameters["skill"]` 指定了技能名，则优先精确匹配。
- 如果 `task.parameters["tags"]` 指定了标签，则按标签查询技能。

后续可以在不破坏技能接口的情况下加入模型规划、技能评分、风险过滤和上下文记忆。
