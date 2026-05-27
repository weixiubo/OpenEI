# 模型提供方

OpenEI 通过 `ModelProvider` 把输入事件解析为 `Task`。内置规则模式无需密钥，适合本地验证和离线运行。

## 内置提供方

- `RuleModelProvider`：规则解析，支持文本、语音转写、图像文件、传感器事件。
- `CloudModelProvider`：云端模型接口，使用同一任务输出协议。
- `LocalModelProvider`：本地模型接口，使用同一任务输出协议。
- `OpenAICompatibleModelProvider`：接入 OpenAI 兼容接口，支持文本和图像任务解析。

## OpenAI 兼容接口

通过环境变量配置模型服务：

```bash
export OPENEI_MODEL_BASE_URL=https://example.com/v1
export OPENEI_MODEL_API_KEY=your_api_key
export OPENEI_MODEL_NAME=gpt-4o-mini
python -m openei quickstart --provider openai --task "执行 10 秒"
```

未配置环境变量时，命令仍会使用本地规则模式完成任务解析。

## 设计边界

模型提供方只负责理解输入和生成任务，不直接控制机器人。机器人控制必须经过规划器、安全策略和适配器。

## 接入要求

接入真实多模态模型时，应保持 `parse_event(event) -> Task` 接口稳定，并补充以下测试：

- 空输入和异常输入。
- 高风险任务识别。
- 图像输入转任务。
- 模型不可用时回退到规则模式。
