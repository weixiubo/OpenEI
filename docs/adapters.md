# 机器人适配器

`RobotAdapter` 是 OpenEI 与机器人硬件之间的边界。运行时只依赖这个接口，不直接依赖具体串口、网口或控制板实现。

## 接口约定

适配器需要实现：

```python
class RobotAdapter:
    def connect(self) -> bool:
        ...

    def status(self) -> RobotStatus:
        ...

    def execute_skill(self, skill: Skill, task: Task) -> ExecutionResult:
        ...

    def stop(self) -> None:
        ...

    def close(self) -> None:
        ...
```

适配器还可以覆盖：

- `discover_capabilities()`
- `health_check()`
- `emergency_stop()`

## 内置适配器

### SimRobotAdapter

模拟适配器用于无硬件快速验证：

- 不连接真实机器人。
- 不阻塞真实动作完成。
- 输出技能名、控制序号、预计耗时和任务目标。
- 适合作为快速开始入口和持续集成测试入口。

### SerialRobotAdapter

串口适配器负责把技能序列下发到串口控制板：

- 使用 `dance.serial_driver.SerialDriver`。
- 从技能 `metadata["seq"]` 读取控制板动作序号。
- 通过 `send_action_command(seq)` 下发到底层控制板。
- 支持自动检测、真实模式和模拟模式。

### HttpRobotAdapter

用于接入提供 REST 接口的低成本控制器。开发阶段可以使用 `mock://robot`：

```bash
python -m openei run --adapter http --url mock://robot --task "执行 5 秒"
```

### MqttRobotAdapter

用于接入 MQTT 控制板或远程机器人。开发阶段可以使用 `mock://local`：

```bash
python -m openei run --adapter mqtt --broker mock://local --task "执行 5 秒"
```

### Ros2RobotAdapter

ROS 2 通过可选适配器模板接入。详见 [ROS 2 可选接入](ros2.md)。

## 契约测试

适配器契约测试会检查连接、状态、能力发现、技能执行、急停和关闭流程：

```bash
python -m openei adapter test --adapter sim
python -m openei adapter test --adapter http --url mock://robot
python -m openei adapter test --adapter mqtt --broker mock://local
python -m openei adapter test --adapter serial
python -m openei adapter test --adapter sim --report reports/adapter.md
```

串口契约测试使用模拟驱动，不依赖真实串口设备。

## 创建适配器模板

```bash
python -m openei adapter create my_robot --kind sim
python -m openei adapter create my_http_robot --kind http
python -m openei adapter create my_mqtt_robot --kind mqtt
python -m openei adapter create my_serial_robot --kind serial
```

生成的模板实现连接、状态、能力发现、技能执行、停止和关闭接口，可以直接接入契约测试。

## 新机器人接入建议

1. 先写一个只打印日志的模拟适配器，确认任务和技能规划可用。
2. 再实现真实连接逻辑，例如串口、网口、蓝牙或控制 SDK。
3. 把硬件动作编号、速度、角度、关节限制写到技能 `metadata`。
4. 在 `execute_skill` 中做参数校验和失败返回，不要让异常穿透运行时。
5. 为适配器补单元测试，至少覆盖连接、状态、执行成功、执行失败和关闭。

## 适配器边界

适配器只处理硬件差异，不负责理解自然语言，也不负责决定任务目标。这样换机器人时不用重写感知层和任务层。
