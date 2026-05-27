# OpenEI

OpenEI 是面向低成本真实机器人的轻量级具身 Agent 运行时原型。它把文本、语音、音频、视觉、传感器等输入统一成任务事件，再经过任务解析、技能规划、执行调度和机器人适配器，变成真实或模拟机器人的身体能力调用。

一句话定位：OpenClaw 让 Agent 调用软件工具，OpenEI 让 Agent 调用真实机器人的身体能力。

```mermaid
flowchart LR
    A[多模态输入] --> B[PerceptionEvent]
    B --> C[Task 任务中间表示]
    C --> D[SkillRegistry 技能匹配]
    D --> E[运行时调度器]
    E --> F[RobotAdapter]
    F --> G[模拟器或真实机器人]
    G --> H[ExecutionResult]
    H --> C
```

## 五分钟模拟器

不需要 API key，不需要真实硬件，先跑完整闭环：

```bash
pip install -r requirements.txt
python -m openei.quickstart --task "执行 10 秒"
```

示例输出：

```text
OpenEI 五分钟模拟器
输入事件: text / 执行 10 秒
任务目标: 执行 10 秒
任务状态: succeeded
时长约束: 10 秒

匹配技能:
  1. motion.挥左拳 (3.1 秒)
  2. motion.挥右拳 (3.6 秒)
  3. motion.立正 (2.0 秒)

模拟执行日志:
  [计划] 第 1 步: motion.挥左拳
  [模拟硬件] 调用技能 motion.挥左拳
  控制序号: 007
```

## 为什么不是传统机器人脚本

传统脚本通常把“输入命令、动作编号、硬件通信”写成固定流程，换输入源、换模型、换机器人都要改主逻辑。OpenEI 的目标是把这几层拆开：

- 输入层只负责产生 `PerceptionEvent`，后续可以接文本、语音、视觉或传感器。
- 任务层把用户目标、参数、约束、风险等级和状态统一成 `Task`。
- 技能层把机器人能力抽象成可注册、可查询、可模拟、可执行的 `Skill`。
- 适配层用 `RobotAdapter` 屏蔽真实硬件、串口通信和模拟执行差异。
- 运行时负责把事件转成任务，再把任务规划成技能序列并收集 `ExecutionResult`。

## 核心能力

- 多模态接入：当前已有文本、语音和音频链路，框架层用统一事件承接后续视觉、传感器和多模型输入。
- 任务中间表示：`Task` 记录目标、参数、约束、风险等级、来源、状态和创建时间。
- 技能系统：`SkillRegistry` 支持技能注册、查询、标签匹配和默认技能包加载。
- 执行运行时：`OpenEIRuntime` 实现 `输入事件 -> 任务解析 -> 技能规划 -> 适配器执行 -> 结果反馈`。
- 硬件适配：内置 `SimRobotAdapter` 和 `SerialRobotAdapter`，无硬件可模拟，有硬件可复用现有串口控制逻辑。
- 兼容旧工程：保留 `dance/` 历史目录名、CSV 技能元数据和原有语音命令，避免破坏已有演示和测试。

## 常规启动

Linux / Orange Pi 推荐：

```bash
bash scripts/run_demo.sh
```

Windows 本地验证：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

手动启动：

```bash
python main.py --profile demo --transport auto --recording-mode smart_vad
```

运行模式：

- `--profile demo`：演示档位，启用启动自检、状态面板和高风险任务确认。
- `--profile dev`：开发档位，保留更直接的本地调试体验。
- `--transport auto`：优先连接真实硬件，失败后自动切换模拟执行。
- `--transport real`：强制真实硬件模式。
- `--transport sim`：强制模拟执行模式。
- `--recording-mode smart_vad`：默认智能录音模式。
- `--no-tts`：禁用语音播报，仅输出文本反馈。

## 目录说明

- `openei/`：新增框架层，包含任务模型、技能系统、机器人适配器、运行时和快速模拟器。
- `config/`：运行配置、音频参数、硬件通信参数和运行档位。
- `core/`：感知特征处理、时序分析和连续技能序列调度逻辑。
- `dance/`：历史命名保留的机器人技能库、控制器和串口驱动模块。
- `voice/`：录音、语音识别、语音合成、意图解析和交互运行时。
- `data/`：机器人技能元数据。
- `docs/`：架构、快速开始、技能开发、适配器开发和演示材料。
- `tests/`：单元测试和回归测试。

## 文档

- [架构说明](docs/architecture.md)
- [快速开始](docs/quickstart.md)
- [技能开发](docs/skills.md)
- [机器人适配器](docs/adapters.md)
- [长期路线](ROADMAP.md)

## 工程建议

- 新用户先跑 `python -m openei.quickstart --task "执行 10 秒"`，确认无硬件闭环可用。
- 再用 `--transport sim` 验证完整语音和任务链路。
- 接入真实机器人前，先检查串口权限、设备路径和供电状态。
- 现场网络不稳定时，对话能力会降级为固定反馈，不影响任务执行主链路。
