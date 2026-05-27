# 贡献指南

OpenEI 欢迎三类贡献：

- 技能包：新增 `skill.yaml` 和对应示例。
- 机器人适配器：新增串口、HTTP、MQTT、ROS 2 或厂商 SDK 适配。
- 文档和演示：补充快速开始、真机视频、硬件接线说明。

## 本地检查

```bash
python -m pytest -q
python -m openei skill validate skill_packages/base_motion
```

## 设计要求

- 保持默认快速开始不需要 API key 和真实硬件。
- 新硬件必须提供模拟或 mock 路径。
- 适配器必须支持 `stop()` 或 `emergency_stop()`。
- 不提交真实密钥、日志和本地录音文件。
