from .execute_command import ShellStartTool, ShellRunTool

ShellStartTool().execute("test")
cmd = """curl -s https://api.ipify.org"""
print(cmd)
print(ShellRunTool().execute(cmd))
