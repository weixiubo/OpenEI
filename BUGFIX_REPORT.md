# 运行诊断修复记录

## 1. 输入设备枚举检测

- 文件：`voice/recording.py`
- 函数：`VoiceRecorder._resolve_input_device_index`
- 变更：在设备选择前输出可用输入设备列表，打印所有 `maxInputChannels > 0` 的设备 `index/name`，便于现场定位真实麦克风。

关键代码：

```python
logger.info("=== 系统可用输入设备列表 ===")
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info.get("maxInputChannels", 0) > 0:
        logger.info("[检测] Index: %d, Name: %s", i, info.get("name", ""))
logger.info("============================")
```

同时保留了既有外接输出设备过滤，避免把播放设备误选为输入源：

```python
if "usb2.0 device" in name_lower:
    logger.debug("忽略外接输出设备: %s", name)
    continue
```

## 2. 语音反馈播放器选择日志

- 文件：`voice/text_to_speech.py`
- 函数：`_play_audio(self, file_path: Path)`
- 变更：在运行时记录最终选择的底层播放器，便于排查端侧音频输出问题。

播放器检测顺序：

- `mpg123`
- `mpv`
- `ffplay`
- `aplay`

关键日志：

```python
logger.info("TTS 选择播放器: %s", player)
```

说明：实际设备最终命中哪一个播放器，以终端日志 `TTS 选择播放器: ...` 为准。
