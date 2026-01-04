"""
Simple development watcher to auto-restart app.py when .py files change.
Run: python dev_run.py
"""
import os
import sys
import time
import subprocess

IGNORED_DIRS = {"venv", "env", "build", ".git", "__pycache__"}


def scan_py_files(root):
    mtimes = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # skip common virtualenv/build/git folders
        parts = set(dirpath.split(os.sep))
        if parts & IGNORED_DIRS:
            continue
        for fname in filenames:
            if not fname.endswith('.py'):
                continue
            path = os.path.join(dirpath, fname)
            try:
                mt = os.path.getmtime(path)
            except OSError:
                continue
            mtimes[path] = mt
    return mtimes


def start_process(cmd):
    return subprocess.Popen(cmd)


def main():
    root = os.path.abspath(os.path.dirname(__file__))
    app_path = os.path.join(root, 'app.py')
    if not os.path.exists(app_path):
        print(f'app.py not found at {app_path}')
        sys.exit(1)

    cmd = [sys.executable, app_path]
    proc = start_process(cmd)
    prev = scan_py_files(root)
    try:
        while True:
            time.sleep(1)
            cur = scan_py_files(root)
            if cur != prev:
                print('Change detected. Restarting app.py...')
                # terminate child
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                # restart
                proc = start_process(cmd)
                prev = cur
    except KeyboardInterrupt:
        print('\nStopping watcher...')
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == '__main__':
    main()
