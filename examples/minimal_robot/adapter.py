from openei import ExecutionResult, RobotAdapter, RobotCapability, RobotStatus, SkillContext


class MinimalRobotAdapter(RobotAdapter):
    def __init__(self) -> None:
        self.connected = False
        self.executed = []

    def connect(self) -> bool:
        self.connected = True
        return True

    def status(self) -> RobotStatus:
        return RobotStatus(
            connected=self.connected,
            mode="simulation",
            name="MinimalRobotAdapter",
            details={"executed": list(self.executed)},
        )

    def discover_capabilities(self):
        return [
            RobotCapability("robot-motion", "参考机器人运动能力", ["robot-motion"]),
            RobotCapability("sample-action", "参考技能执行能力", ["sample-action"]),
        ]

    def execute_skill(self, skill, task) -> ExecutionResult:
        self.executed.append(skill.name)
        result = skill.simulate(SkillContext(task=task, adapter=self))
        return ExecutionResult(
            success=result.success,
            message=f"参考适配器已执行 {skill.name}",
            trace=[f"[参考适配器] {skill.name}"] + result.trace,
            error=result.error,
            recovery_actions=result.recovery_actions,
            structured_trace=result.structured_trace,
        )

    def stop(self) -> None:
        self.executed.append("stop")

    def close(self) -> None:
        self.connected = False
