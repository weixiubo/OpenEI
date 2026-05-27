from openei import OpenEIRuntime


runtime = OpenEIRuntime.from_defaults(sim=True)
report = runtime.run_text("执行 10 秒")

print(report.result.message)
for line in report.result.trace:
    print(line)
