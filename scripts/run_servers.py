#!/usr/bin/env python3
import subprocess
import sys
import time

# Start all three servers
servers = [
    ("fundament_rf", "/home/user_aioc/workspace/projects/01_fundament_rf", ["python3", "app.py", "5000"]),
    ("demo_charts_ascii", "/home/user_aioc/workspace/projects/03_demo_charts_ascii", ["python3", "app.py", "5001"]),
    ("graphs_candle", "/home/user_aioc/workspace/projects/02_graphs_candle", ["venv_uv/bin/python3", "main.py", "5002"]),
]

procs = []
for name, cwd, cmd in servers:
    print(f"Starting {name}...")
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs.append((name, p))
    time.sleep(2)

print("All servers started. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping servers...")
    for name, p in procs:
        p.terminate()
        print(f"Stopped {name}")
