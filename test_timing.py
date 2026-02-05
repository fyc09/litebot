from iribot.tools.execute_command import ShellSession
import time

session = ShellSession()
time.sleep(0.5)

print("=== Sending curl command ===")
session.write("curl -s https://api.ipify.org")
print("=== Curl command sent ===")

# Try to read immediately (should be empty)
output1 = session.read(wait_ms=0, max_chars=50000)
print(f"Immediate read - stdout: {repr(output1['stdout'])}, stderr: {repr(output1['stderr'])}")

print("=== Waiting 1 second ===")
time.sleep(1)

# Read after 1 second
output2 = session.read(wait_ms=1000, max_chars=50000)
print(f"After 1s - stdout: {repr(output2['stdout'])}, stderr: {repr(output2['stderr'])}")

print("=== Waiting another 2 seconds ===")
time.sleep(2)

# Read again after total 3 seconds
output3 = session.read(wait_ms=1000, max_chars=50000)
print(f"After 3s total - stdout: {repr(output3['stdout'])}, stderr: {repr(output3['stderr'])}")

print("=== Sending echo marker ===")
session.write("echo DONE")
time.sleep(1)

output4 = session.read(wait_ms=1000, max_chars=50000)
print(f"After marker - stdout: {repr(output4['stdout'])}, stderr: {repr(output4['stderr'])}")

session.terminate()
