# 更新记录

## v0.2.0

`v0.2.0` 强化无硬件开发体验，让开发者可以通过报告、场景、模板和持续集成验证技能、适配器和任务链路。

### 新增能力

- 报告输出：`quickstart`、`skill validate`、`adapter test`、`robot validate`、`replay` 支持 Markdown 和 JSON 报告。
- 场景运行器：`scenario run` 可以加载任务、机器人描述、技能包、适配器和期望结果，形成可重复验收场景。
- 最小机器人工程：`examples/minimal_robot` 提供机器人描述、技能包、自定义适配器、场景文件和教程。
- 模型解析命令：`model parse` 支持文本和图像任务解析。
- 模板生成：`skill create` 和 `adapter create --kind` 生成可校验、可测试的扩展模板。
- 持续集成：覆盖测试、快速开始、图像任务、样板场景、模型解析、技能校验、机器人校验、适配器契约和审计回放。

### 验收命令

```bash
python -m pytest -q
python -m openei quickstart --task "执行 10 秒" --report reports/quickstart.md
python -m openei scenario run examples/minimal_robot/scenario.json --report reports/minimal_robot.md
python -m openei model parse --task "执行 10 秒" --provider rule
python -m openei skill validate examples/minimal_robot/skills --report reports/skills.md
python -m openei adapter test --adapter sim --report reports/adapter.md
python -m openei replay logs/openei_audit.jsonl --report reports/replay.md
```

## v0.1.0-alpha

`v0.1.0-alpha` 固化 OpenEI 的轻量级具身 Agent 运行时能力，面向低成本真实机器人和无硬件开发场景提供稳定入口。

### 新增能力

- 事件模型：统一文本、语音、音频、图像、视频和传感器输入。
- 任务模型：描述目标、类型、参数、约束、风险等级、安全策略和期望结果。
- 技能系统：支持默认技能库、`skill.yaml` 技能包、技能校验、安装、列表和运行。
- 适配器层：提供模拟器、串口、HTTP、MQTT 和可选 ROS 2 适配器。
- 运行时：完成任务解析、技能规划、安全检查、执行调度、失败恢复和结果反馈。
- 审计日志：以 JSONL 记录任务解析、规划、技能执行、结果和恢复动作。
- 任务回放：通过 `python -m openei replay logs/openei_audit.jsonl` 只读复盘执行链路。
- 机器人描述文件：通过 `robot.yaml` 声明能力、限制、安全停止技能、适配器和技能包。
- 适配器契约测试：通过 `python -m openei adapter test --adapter sim` 验证适配器接口完整性。
- 模型提供方：保留无密钥规则模式，并支持通过环境变量接入 OpenAI 兼容模型服务。

### 验收命令

```bash
python -m pytest -q
python -m openei quickstart --task "执行 10 秒"
python -m openei quickstart --image examples/image_input/scene.jpg --task "根据画面执行安全动作"
python -m openei skill validate skill_packages/base_motion
python -m openei robot validate robot.yaml
python -m openei adapter test --adapter sim
python -m openei adapter test --adapter http --url mock://robot
python -m openei adapter test --adapter mqtt --broker mock://local
python -m openei replay logs/openei_audit.jsonl
```
