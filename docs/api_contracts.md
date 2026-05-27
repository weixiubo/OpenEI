# 公开接口契约

OpenEI 的公共接口围绕“输入事件、任务、技能、适配器、执行结果、机器人描述、技能包、场景文件”展开。开发者扩展项目时应优先依赖这些接口。

## 核心对象

- `PerceptionEvent`：统一文本、语音、音频、图像、视频和传感器输入。
- `Task`：描述目标、参数、约束、风险等级、安全策略和期望结果。
- `Skill`：描述机器人能力，支持参数校验、前置条件、模拟执行和真实执行。
- `RobotAdapter`：屏蔽硬件差异，提供连接、状态、技能执行、停止、关闭和急停接口。
- `ExecutionResult`：返回成功状态、消息、耗时、轨迹、错误和恢复动作。

## 声明文件

- `robot.yaml`：声明机器人能力、限制、安全停止技能、适配器和技能包。
- `skill.yaml`：声明技能包名称、版本、技能、标签、风险等级和适配器要求。
- `scenario.json`：声明可重复运行的任务场景、适配器、技能包和期望结果。

## 命令入口

```bash
python -m openei quickstart --task "执行 10 秒"
python -m openei scenario run examples/minimal_robot/scenario.json
python -m openei skill validate examples/minimal_robot/skills
python -m openei adapter test --adapter sim
python -m openei robot validate robot.yaml
python -m openei model parse --task "执行 10 秒" --provider rule
python -m openei replay logs/openei_audit.jsonl
```
