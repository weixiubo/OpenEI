# 五分钟快速开始

本页目标是让新用户不接硬件、不配置密钥，也能跑通 OpenEI 的任务闭环。

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 运行模拟器

```bash
python -m openei quickstart --task "执行 10 秒"
```

这个命令会完成：

- 把文本输入标准化为 `PerceptionEvent`。
- 从输入中解析时长约束并生成 `Task`。
- 从默认技能包中匹配技能序列。
- 用 `SimRobotAdapter` 输出模拟硬件调用日志。
- 返回 `ExecutionResult` 并写入审计日志。

## 3. 预期输出

```text
OpenEI 五分钟模拟器
输入事件: text / 执行 10 秒
任务目标: 执行 10 秒
任务类型: motion
任务状态: succeeded
风险等级: low
时长约束: 10 秒

匹配技能:
  1. motion.挥左拳 (3.1 秒)
  2. motion.挥右拳 (3.6 秒)
  3. motion.safe_stand (2.0 秒)

执行结果: 任务已完成
```

## 4. 下一步

- 修改任务文本，例如 `执行五秒`、`帮我执行 15 秒`。
- 运行图像输入样例：`python -m openei quickstart --image examples/image_input/scene.jpg --task "根据画面执行安全动作"`。
- 查看技能包：`python -m openei skill list`。
- 查看 [技能开发](skills.md)，新增一个自己的机器人技能。
- 查看 [机器人适配器](adapters.md)，把模拟执行换成真实硬件执行。
