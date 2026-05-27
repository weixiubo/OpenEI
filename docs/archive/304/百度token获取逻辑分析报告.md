# 百度语音访问令牌逻辑分析报告

## 分析目标

本文记录主线百度语音服务的访问令牌获取逻辑，并为后续语音供应商适配提供接口对照。该文档属于历史分析材料，关注点是语音识别适配层，不涉及任务调度和硬件执行层的改动。

## 当前主线调用链

```text
VoiceAssistant
  -> VoiceRecorder.record(...)
  -> SpeechRecognizer.recognize(audio_data, sample_rate)
  -> 百度语音 token 接口
  -> 百度语音识别接口
  -> 结构化文本结果
  -> 意图解析与任务执行链路
```

## 百度 token 获取逻辑

主线通过 `BAIDU_API_KEY` 和 `BAIDU_SECRET_KEY` 请求访问令牌：

```python
response = requests.post(
    token_url,
    params={
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key,
    },
    timeout=10,
)
```

获取到的 `access_token` 会缓存在识别器实例中，并设置本地过期时间，避免每次识别都请求 token。

## 环境变量

```dotenv
BAIDU_API_KEY=your_baidu_api_key_here
BAIDU_SECRET_KEY=your_baidu_secret_key_here
```

## 与供应商替换的关系

- 上层只依赖 `recognize(audio_data, sample_rate) -> (bool, str)`。
- 供应商鉴权、请求格式、错误码解析都应封装在语音识别适配层内部。
- 切换供应商时不应修改意图解析、技能调度或硬件控制模块。

## 迁移注意事项

- 阿里云等供应商可能需要 AccessKey、AppKey、Region 或 SDK 初始化。
- 如果供应商采用异步回调，应在适配层内部封装为同步返回，保持上层接口稳定。
- 迁移前必须补充鉴权失败、网络失败、空音频、短音频和正常识别的回归测试。

## 结论

百度 token 逻辑集中在语音识别模块内部，边界清晰。后续如需更换供应商，应新增供应商适配实现或配置化选择，而不是改动 OpenEI 的任务建模和执行闭环。
