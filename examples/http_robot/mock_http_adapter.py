from openei import HttpRobotAdapter, OpenEIRuntime
from openei.default_skills import build_default_registry


adapter = HttpRobotAdapter("mock://robot")
adapter.connect()
runtime = OpenEIRuntime(build_default_registry(), adapter)
report = runtime.run_text("执行 5 秒")

print(report.result.message)
print(adapter.history)
