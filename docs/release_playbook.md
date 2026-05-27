# 发布手册

## v0.1.0 发布门槛

- `python -m pytest -q` 全部通过。
- `python -m openei quickstart --task "执行 10 秒"` 可运行。
- `python -m openei quickstart --image examples/image_input/scene.jpg --task "根据画面执行安全动作"` 可运行。
- `python -m openei skill validate skill_packages/base_motion` 通过。
- README、快速开始、技能开发、适配器开发、ROS 2 文档齐全。
- 至少有一条真实串口机器人演示视频或动图。

## 发布步骤

```bash
python -m pytest -q
python -m openei skill validate skill_packages/base_motion
git tag v0.1.0
git push origin main --tags
```

## 发布后传播

1. 发概念短文。
2. 发五分钟教程。
3. 发真实机器人视频。
4. 邀请社区贡献技能包和硬件适配器。
