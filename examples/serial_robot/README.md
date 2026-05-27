# 串口机器人示例

先确认控制板串口路径和波特率，再运行：

```bash
SERIAL_PORT=/dev/ttyUSB0 python -m openei run --adapter serial --task "执行 10 秒"
```

如果串口不可用，串口适配器会进入模拟降级路径，便于现场排查。
