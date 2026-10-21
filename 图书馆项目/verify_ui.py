"""Run UI smoke checks through the production QApplication initialization."""
import subprocess, sys
from pathlib import Path
if __name__=='__main__':
    raise SystemExit(subprocess.call([sys.executable,str(Path(__file__).with_name('main.py')),'--smoke-test']))
