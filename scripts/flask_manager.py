#!/usr/bin/env python3
"""
Flask Manager - Global Flask project management
Usage: flask_manager.py <command> [options]

Commands:
    start <project> [port] [--watchdog]  - Start project on port (default 5000)
    stop <project>                       - Stop project
    status [project]                     - Show status (all or specific)
    restart <project>                    - Restart project
    list                                 - List available projects
"""
import os, sys, time, signal, subprocess, argparse
from pathlib import Path

WORKSPACE = Path("/home/user_aioc/workspace")
LOG_DIR = Path("/tmp")
PID_DIR = Path("/tmp")
DEFAULT_PORT = '5000'

class FlaskManager:
    def __init__(self):
        self.projects = self._discover_projects()

    def _discover_projects(self):
        projects = {}
        for d in WORKSPACE.iterdir():
            if d.is_dir() and (d / "app.py").exists():
                projects[d.name] = d
        return projects

    def _pid_file(self, name):
        return PID_DIR / f"flask_{name}.pid"

    def _log_file(self, name):
        return LOG_DIR / f"flask_{name}.log"

    def is_running(self, name):
        pf = self._pid_file(name)
        if pf.exists():
            try:
                pid = int(pf.read_text().strip())
                os.kill(pid, 0)
                return True
            except:
                pf.unlink()
        return False

    def start(self, name, port=DEFAULT_PORT, watchdog=False):
        if name not in self.projects:
            print(f"Project '{name}' not found")
            return False
        if self.is_running(name):
            print(f"Project '{name}' already running")
            return True

        proj_dir = self.projects[name]
        py_exe = sys.executable
        for cand in [proj_dir / ".venv" / "bin" / "python", proj_dir / "venv" / "bin" / "python"]:
            if cand.exists():
                py_exe = str(cand)
                break

        log_file = self._log_file(name)

        if watchdog:
            script = LOG_DIR / f"watchdog_{name}.py"
            script.write_text(f"""
import subprocess, sys, time, signal, os
def handler(sig, frame): pass
signal.signal(signal.SIGTERM, handler)
def run():
    return subprocess.Popen(["{py_exe}", "app.py", "{port}"],
        stdout=open("{log_file}",'a'), stderr=subprocess.STDOUT,
        cwd="{proj_dir}", start_new_session=True)
if __name__ == '__main__':
    proc = run()
    while True:
        proc.wait(); time.sleep(1)
        if proc.poll() is not None:
            print("Restarting..."); proc = run()
""")
            proc = subprocess.Popen([sys.executable, str(script)],
                stdout=open(log_file, 'a'), stderr=subprocess.STDOUT,
                cwd=proj_dir, start_new_session=True)
        else:
            proc = subprocess.Popen(
                [py_exe, "app.py", port],
                stdout=open(log_file, 'a'), stderr=subprocess.STDOUT,
                cwd=proj_dir, start_new_session=True
            )
            time.sleep(2)

        self._pid_file(name).write_text(str(proc.pid))
        print(f"Started {name} on :{port} (PID: {proc.pid})" + (" [watchdog]" if watchdog else ""))
        return True

    def stop(self, name):
        if not self.is_running(name):
            print(f"Project '{name}' not running")
            return True
        pid_file = self._pid_file(name)
        try:
            os.kill(int(pid_file.read_text()), signal.SIGTERM)
            time.sleep(1)
            pid_file.unlink()
            print(f"Stopped {name}")
        except:
            subprocess.run(["pkill", "-f", f"python.*app.py"], capture_output=True)
            try:
                pid_file.unlink()
                print(f"Stopped {name} (by pattern)")
            except:
                pass
        return True

    def status(self, name=None):
        if name:
            pf = self._pid_file(name)
            if pf.exists() and self.is_running(name):
                print(f"{name}: running (PID: {pf.read_text().strip()})")
            else:
                print(f"{name}: not running")
        else:
            print("Flask projects:")
            for p in sorted(self.projects):
                print(f"  {p}: {'running' if self.is_running(p) else 'stopped'}")
        return True

    def restart(self, name, port=DEFAULT_PORT):
        self.stop(name)
        time.sleep(1)
        return self.start(name, port)

    def list_projects(self):
        print("Available projects:")
        for p in sorted(self.projects):
            print(f"  {p}")
        return True

def main():
    parser = argparse.ArgumentParser(description="Flask Manager")
    sub = parser.add_subparsers(dest="cmd")

    start = sub.add_parser("start", help="Start project")
    start.add_argument("project")
    start.add_argument("port", nargs="?", default=DEFAULT_PORT)
    start.add_argument("--watchdog", action="store_true")

    stop = sub.add_parser("stop", help="Stop project")
    stop.add_argument("project")

    status = sub.add_parser("status", help="Show status")
    status.add_argument("project", nargs="?")

    restart = sub.add_parser("restart", help="Restart project")
    restart.add_argument("project")
    restart.add_argument("port", nargs="?", default=DEFAULT_PORT)

    sub.add_parser("list", help="List projects")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    mgr = FlaskManager()
    if args.cmd == "start":
        mgr.start(args.project, args.port, args.watchdog)
    elif args.cmd == "stop":
        mgr.stop(args.project)
    elif args.cmd == "status":
        mgr.status(args.project)
    elif args.cmd == "restart":
        mgr.restart(args.project, args.port)
    elif args.cmd == "list":
        mgr.list_projects()

if __name__ == "__main__":
    main()
