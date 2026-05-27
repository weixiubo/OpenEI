"""
历史机器人控制兼容包。

该目录名保持不变，用于兼容既有导入路径。
"""

__all__ = [
    "ActionLibrary",
    "DanceAction",
    "RobotController",
    "SerialDriver",
]


def __getattr__(name):
    if name in {"ActionLibrary", "DanceAction"}:
        from .action_library import ActionLibrary, DanceAction

        return {"ActionLibrary": ActionLibrary, "DanceAction": DanceAction}[name]
    if name == "RobotController":
        from .robot_controller import RobotController

        return RobotController
    if name == "SerialDriver":
        from .serial_driver import SerialDriver

        return SerialDriver
    raise AttributeError(name)
