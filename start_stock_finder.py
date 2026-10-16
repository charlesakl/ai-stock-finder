"""Launch the local Phase 11 application with Python 3.13."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / '.venv313'
PYTHON = VENV / 'Scripts' / 'python.exe' if sys.platform == 'win32' else VENV / 'bin' / 'python'

def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)

def main():
    if not PYTHON.exists():
        print('Creating Python 3.13 environment...')
        run('py', '-3.13', '-m', 'venv', str(VENV)) if sys.platform == 'win32' else run(sys.executable, '-m', 'venv', str(VENV))
    if not (VENV / '.dependencies_installed').exists():
        print('Installing dependencies (first launch only)...')
        run(str(PYTHON), '-m', 'pip', 'install', '--upgrade', 'pip')
        run(str(PYTHON), '-m', 'pip', 'install', '-r', 'requirements.txt')
        (VENV / '.dependencies_installed').touch()
    print('Launching AI Stock Finder Phase 11 Final...')
    run(str(PYTHON), '-m', 'streamlit', 'run', 'app.py')

if __name__ == '__main__':
    main()
