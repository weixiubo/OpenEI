from pathlib import Path

from openei import OpenEIRuntime


image_path = Path(__file__).parent / "scene.jpg"
runtime = OpenEIRuntime.from_defaults(sim=True)
report = runtime.run_image(str(image_path), task="根据画面执行安全动作")

print(report.task.goal)
print(report.task.task_type.value)
print(report.result.message)
