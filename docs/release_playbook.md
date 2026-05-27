# 发布手册

## v0.2.0 检查项

- `python -m pytest -q` 全部通过。
- `python -m openei quickstart --task "执行 10 秒" --report reports/quickstart.md` 可运行。
- `python -m openei quickstart --image examples/image_input/scene.jpg --task "根据画面执行安全动作" --report reports/image.md` 可运行。
- `python -m openei scenario run examples/minimal_robot/scenario.json --report reports/minimal_robot.md` 通过。
- `python -m openei model parse --task "执行 10 秒" --provider rule --report reports/model.md` 通过。
- `python -m openei skill validate examples/minimal_robot/skills --report reports/skills.md` 通过。
- `python -m openei robot validate robot.yaml --report reports/robot.md` 通过。
- `python -m openei adapter test --adapter sim --report reports/adapter.md` 通过。
- `python -m openei replay logs/openei_audit.jsonl --report reports/replay.md` 可读取审计日志。
- README、快速开始、技能开发、适配器开发、场景运行、模型提供方、可观测性和公开接口契约文档齐全。

## 发布步骤

```bash
python -m pytest -q
python -m openei quickstart --task "执行 10 秒" --report reports/quickstart.md
python -m openei quickstart --image examples/image_input/scene.jpg --task "根据画面执行安全动作" --report reports/image.md
python -m openei scenario run examples/minimal_robot/scenario.json --report reports/minimal_robot.md
python -m openei model parse --task "执行 10 秒" --provider rule --report reports/model.md
python -m openei skill validate examples/minimal_robot/skills --report reports/skills.md
python -m openei robot validate robot.yaml --report reports/robot.md
python -m openei adapter test --adapter sim --report reports/adapter.md
python -m openei replay logs/openei_audit.jsonl --report reports/replay.md
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

## 发布资产

1. README 首屏展示定位、架构图、五分钟命令和模拟日志。
2. 文档覆盖快速开始、技能开发、适配器开发、场景运行、模型提供方、可观测性和 ROS 2 接入。
3. 示例覆盖文本任务、图像任务、最小机器人工程、串口机器人、HTTP 机器人、MQTT 机器人和 ROS 2 模板。
