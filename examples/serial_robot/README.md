# 串口机器人示例

先确认控制板串口路径和波特率，再运行：

```bash
SERIAL_PORT=/dev/ttyUSB0 python -m openei run --adapter serial --task "执行 10 秒"
```

如果串口不可用，旧串口驱动会保留模拟降级行为，便于现场排查。
