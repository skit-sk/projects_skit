import subprocess, sys, time, os, signal

WORKSPACE = '/home/user_aioc/workspace'
CMD = sys.argv[1] if len(sys.argv) > 1 else 'start'
PROJECT = sys.argv[2] if len(sys.argv) > 2 else 'fundament_rf'
PORT = sys.argv[3] if len(sys.argv) > 3 else '5000'
PROJECT_DIR = os.path.join(WORKSPACE, PROJECT)
PID_FILE = f'/tmp/flask_runner_{PROJECT}.pid'

def log(msg):
    print(f'[flask-runner] {msg}')

def handler(signum, frame):
    log(f'Stopping {PROJECT}...')
    kill_flask()
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)
signal.signal(signal.SIGINT, handler)

def kill_flask():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            log(f'Killed PID {pid}')
            os.unlink(PID_FILE)
        except:
            pass
    time.sleep(1)

def is_running():
    if not os.path.exists(PID_FILE):
        return False
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except:
        os.unlink(PID_FILE)
        return False

def run():
    log(f'Starting {PROJECT} on port {PORT}...')
    logf = open(f'/tmp/flask_runner_{PROJECT}.log', 'a')
    proc = subprocess.Popen(
        [sys.executable, 'app.py', PORT],
        stdout=logf, stderr=subprocess.STDOUT, cwd=PROJECT_DIR
    )
    with open(PID_FILE, 'w') as f:
        f.write(str(proc.pid))
    return proc, logf

def cmd_start():
    if is_running():
        log(f'{PROJECT} already running (PID: {open(PID_FILE).read().strip()})')
        return
    kill_flask()
    time.sleep(1)
    proc, logf = run()
    log(f'Started {PROJECT} (PID: {proc.pid})')
    try:
        while True:
            if proc.poll() is not None:
                log(f'Crashed (code: {proc.returncode}), restarting...')
                logf.close()
                kill_flask()
                time.sleep(2)
                proc, logf = run()
                log(f'Restarted {PROJECT} (PID: {proc.pid})')
            time.sleep(1)
    except KeyboardInterrupt:
        handler(signal.SIGINT, None)

def cmd_stop():
    if is_running():
        kill_flask()
        log(f'{PROJECT} stopped')
    else:
        log(f'{PROJECT} not running')

def cmd_status():
    log(f'{PROJECT}: {"running" if is_running() else "stopped"}')

def cmd_restart():
    cmd_stop()
    time.sleep(1)
    cmd_start()

commands = {'start': cmd_start, 'stop': cmd_stop, 'status': cmd_status, 'restart': cmd_restart}

if __name__ == '__main__':
    if CMD in commands:
        commands[CMD]()
    else:
        log(f'Usage: python runner.py <start|stop|status|restart> [project] [port]')
        sys.exit(1)
