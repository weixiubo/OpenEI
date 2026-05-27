# 可观测性与审计

OpenEI 的运行时会把任务解析、规划、技能执行和结果写入 JSONL 审计日志。

日志路径：

```bash
logs/openei_audit.jsonl
```

## 审计事件

- `task.parsed`
- `task.planned`
- `task.started`
- `skill.started`
- `skill.finished`
- `task.succeeded`
- `task.failed`

## 回放

```bash
python -m openei replay logs/openei_audit.jsonl
```

输出会按时间顺序展示任务解析、技能序列、技能完成、任务结果、失败原因和恢复动作。回放只读取日志，不重新执行任务，也不会触发硬件。

需要在代码中读取日志时，可以使用：

```python
from openei import replay_events

for event in replay_events("logs/openei_audit.jsonl"):
    print(event["event_type"], event["payload"])
```

## 设计原则

- 审计日志不写入仓库。
- 每条执行结果都有 `audit_id`。
- 失败时记录恢复动作，例如重试、降级、停止或人工确认。
