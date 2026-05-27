from openei import ExecutionResult, RobotStatus, Ros2RobotAdapter


class DemoRos2Adapter(Ros2RobotAdapter):
    """Replace execute_skill with ROS 2 topic/action calls in a real robot."""

    def execute_skill(self, skill, task) -> ExecutionResult:
        if not self.connected:
            return ExecutionResult(False, "ROS 2 未连接", error=self.last_error)
        return ExecutionResult(
            True,
            f"ROS 2 模板收到技能 {skill.name}",
            trace=[f"[ROS2 TEMPLATE] {skill.name}"],
        )

    def status(self) -> RobotStatus:
        status = super().status()
        status.details["template"] = "examples/ros2_template"
        return status
