#!/usr/bin/env python3
"""Flask daemon wrapper with auto-restart."""

import os
import sys
import time
import signal
import subprocess
import atexit

WORKDIR = "/home/user_aioc/workspace/projects/02_graphs_candle"
PYTHON = "./venv/bin/python"
MAIN = "main.py"
PIDFILE = "/tmp/flask_daemon.pid"
LOGFILE = "/tmp/flask_daemon.log"

class Daemon:
    def __init__(self, pidfile, logfile):
        self.pidfile = pidfile
        self.logfile = logfile
        
    def log(self, msg):
        with open(self.logfile, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    
    def pid_running(self):
        try:
            with open(self.pidfile) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return pid
        except:
            return None
    
    def start(self):
        if self.pid_running():
            print(f"Flask already running (PID: {self.pid_running()})")
            return
        
        self.log("Starting Flask...")
        
        # Start subprocess
        self.proc = subprocess.Popen(
            [PYTHON, MAIN],
            cwd=WORKDIR,
            stdout=open(self.logfile, 'a'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        
        with open(self.pidfile, 'w') as f:
            f.write(str(self.proc.pid))
        
        self.log(f"Flask started (PID: {self.proc.pid})")
        print(f"Flask started on http://localhost:5000")
        print(f"Log: {self.logfile}")
    
    def stop(self):
        pid = self.pid_running()
        if pid:
            self.log(f"Stopping Flask (PID: {pid})...")
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                os.kill(pid, signal.SIGKILL)
            except:
                pass
            os.remove(self.pidfile)
            self.log("Flask stopped")
            print("Flask stopped")
        else:
            print("Flask not running")
    
    def restart(self):
        self.stop()
        time.sleep(1)
        self.start()
    
    def status(self):
        pid = self.pid_running()
        if pid:
            print(f"Flask running (PID: {pid})")
        else:
            print("Flask not running")

if __name__ == "__main__":
    daemon = Daemon(PIDFILE, LOGFILE)
    
    if len(sys.argv) < 2:
        print("Usage: flask_daemon.py start|stop|restart|status")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "start":
        daemon.start()
    elif cmd == "stop":
        daemon.stop()
    elif cmd == "restart":
        daemon.restart()
    elif cmd == "status":
        daemon.status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
