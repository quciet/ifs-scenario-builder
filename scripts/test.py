"""Run tests with the same shared helpers used by the package builder."""
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPANION = Path(os.environ.get('IFS_COMPANION_PATH', ROOT.parent/'ifs-companion'))
sys.path[:0] = [str(ROOT), str(COMPANION)]
os.environ.setdefault('IFS_COMPANION_APP_DIR', str(COMPANION))
if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
