"""sys.path setup and argument parsing for scripts run as: Blender -b -P script.py -- args"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
OUT = os.path.join(ROOT, 'out')


def args():
    argv = sys.argv
    return argv[argv.index('--') + 1:] if '--' in argv else []


def log(*a):
    print('[am]', *a, flush=True)
