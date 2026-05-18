#!/usr/bin/env python3
import subprocess
import time

# Kill old
subprocess.run(['pkill', '-f', 'app.py 5000'], capture_output=True)
time.sleep(1)

# Start detached
proc = subprocess.Popen(
    ['python3', 'app.py', '5000'],
    cwd='/home/user_aioc/workspace/projects/01_fundament_rf',
    stdout=open('/tmp/fundament_rf.log', 'w'),
    stderr=subprocess.STDOUT,
    start_new_session=True
)

print(f"Started PID {proc.pid}")
time.sleep(2)

# Verify
import urllib.request
try:
    with urllib.request.urlopen('http://localhost:5000/', timeout=5) as resp:
        print(f"Status: {resp.status}")
except Exception as e:
    print(f"Error: {e}")
