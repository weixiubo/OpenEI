# 演示视频脚本

## 标题

机器人版 OpenClaw：五分钟让 Agent 调用低成本机器人的身体能力

## 镜头顺序

1. 打开仓库首页，展示一句话定位和五分钟命令。
2. 运行 `python -m openei quickstart --task "执行 10 秒"`，展示无硬件闭环。
3. 运行 `python -m openei skill list`，展示技能包。
4. 切到串口机器人，运行 `python -m openei run --adapter serial --task "执行 10 秒"`。
5. 展示机器人真实执行和审计日志。
6. 展示 `examples/ros2_template/`，说明 ROS 2 是可选适配方向。

## 核心话术

- OpenClaw 让 Agent 调用软件工具。
- OpenEI 让 Agent 调用真实机器人的身体能力。
- 默认轻量，不要求 ROS 2。
- 需要 ROS 2 时，可以通过适配器接入。
