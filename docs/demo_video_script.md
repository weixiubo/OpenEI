# 演示视频脚本

## 标题

OpenEI：低成本机器人具身智能体运行时

## 镜头顺序

1. 打开仓库首页，展示项目定位和快速验证命令。
2. 运行 `python -m openei quickstart --task "执行 10 秒"`，展示无硬件闭环。
3. 运行 `python -m openei skill list`，展示技能包。
4. 切到串口机器人，运行 `python -m openei run --adapter serial --task "执行 10 秒"`。
5. 展示机器人真实执行和审计日志。
6. 展示 `examples/ros2_template/`，说明 ROS 2 是可选适配方向。

## 核心话术

- OpenEI 将多模态输入转化为可审计、可回放的机器人任务链路。
- 同一运行时可覆盖模拟器、串口控制板和网络适配器。
- 核心运行时保持轻量，ROS 2 通过适配器接入。
- 需要 ROS 2 时，可以通过适配器接入。
