#!/usr/bin/env python3
import os
import subprocess
import sys

def start_server(name, cwd, cmd):
    """Start a server detached from terminal"""
    log_file = open(f'/tmp/{name}.log', 'a')
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,  # This calls setsid()
        close_fds=True
    )
    log_file.close()
    print(f"Started {name} with PID {proc.pid}")
    return proc.pid

# Kill old servers
os.system("pkill -f 'app.py 5000' 2>/dev/null")
os.system("pkill -f 'main.py 5002' 2>/dev/null")
os.system("sleep 2")

# Start servers
start_server('fundament_rf', '/home/user_aioc/workspace/projects/01_fundament_rf', ['python3', 'app.py', '5000'])
start_server('graphs_candle', '/home/user_aioc/workspace/projects/02_graphs_candle', ['venv_uv/bin/python3', 'main.py', '5002'])

print("Servers started")
