# 304 阿里云 NLS 测试说明

## 用途

该文档记录历史语音供应商替换实验的测试方式。实验目标是验证阿里云 NLS 能否作为 OpenEI 语音识别适配层的候选实现。

## 环境变量

```dotenv
ALIYUN_ACCESS_KEY_ID=your_aliyun_access_key_id_here
ALIYUN_ACCESS_KEY_SECRET=your_aliyun_access_key_secret_here
ALIYUN_APP_KEY=your_aliyun_app_key_here
ALIYUN_REGION=cn-wuhan
```

## 测试步骤

1. 安装实验依赖。

```bash
pip install aliyun-python-sdk-core requests python-dotenv
```

2. 配置环境变量。

3. 运行测试脚本。

```bash
python archive/code/spike-304-aliyun/aliyun_nls_test.py
```

## 预期验证点

- 能成功获取供应商访问令牌。
- 能提交 PCM 音频并获得文本结果。
- 失败时能返回明确错误信息。
- 不影响主线 `SpeechRecognizer` 的外层接口设计。

## 当前结论

该实验保留为供应商适配参考。当前主线没有启用阿里云 NLS；如需启用，应在主线语音识别模块中实现可配置供应商选择，并补充端到端测试。
