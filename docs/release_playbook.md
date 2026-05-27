# 发布手册

## v0.1.0-alpha 检查项

- `python -m pytest -q` 全部通过。
- `python -m openei quickstart --task "执行 10 秒"` 可运行。
- `python -m openei quickstart --image examples/image_input/scene.jpg --task "根据画面执行安全动作"` 可运行。
- `python -m openei skill validate skill_packages/base_motion` 通过。
- `python -m openei robot validate robot.yaml` 通过。
- `python -m openei adapter test --adapter sim` 通过。
- `python -m openei adapter test --adapter http --url mock://robot` 通过。
- `python -m openei adapter test --adapter mqtt --broker mock://local` 通过。
- `python -m openei replay logs/openei_audit.jsonl` 可读取审计日志。
- README、快速开始、技能开发、适配器开发、模型提供方、可观测性和 ROS 2 文档齐全。

## 发布步骤

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
git tag v0.1.0-alpha
git push origin main
git push origin v0.1.0-alpha
```

## 发布资产

1. README 首屏展示定位、架构图、五分钟命令和模拟日志。
2. 文档覆盖快速开始、技能开发、适配器开发、模型提供方、可观测性和 ROS 2 接入。
3. 示例覆盖文本任务、图像任务、串口机器人、HTTP 机器人、MQTT 机器人和 ROS 2 模板。
