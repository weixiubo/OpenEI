# ROS 2 可选接入

OpenEI 默认不依赖 ROS 2，避免新用户第一步就被复杂环境挡住。但 ROS 2 作为一等公民适配方向保留在 `Ros2RobotAdapter` 和 `examples/ros2_template/` 中。

## 使用方式

1. 在 ROS 2 环境中安装 `rclpy`。
2. 继承 `Ros2RobotAdapter`。
3. 在 `execute_skill` 中把 `Skill` 转成 topic、service 或 action 调用。
4. 保持 `ExecutionResult` 结构化返回。

## 模板

```bash
python -m openei adapter create my_ros_robot
```

或参考：

```text
examples/ros2_template/robot_adapter.py
```

## 边界

ROS 2 适配器不负责自然语言理解，也不负责技能规划。它只把已经规划好的技能安全地发送到 ROS 2 机器人。
