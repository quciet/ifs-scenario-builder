"""Exercise a relocated build through the real Companion tool manager."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tool_manager import ToolManager

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_build_install_launch_and_preserve_saved_work(self):
        with tempfile.TemporaryDirectory(prefix='scenario-package-') as temporary:
            root = Path(temporary)
            subprocess.run([sys.executable, str(ROOT/'scripts/build_tool.py'),
                            '--version', '0.0.0', '--output-dir', str(root/'release')],
                           cwd=root, check=True, capture_output=True, text=True)
            package = root/'release/ifs-scenario-builder-0.0.0-win-x64.ifstool'
            digest = hashlib.sha256(package.read_bytes()).hexdigest()
            self.assertEqual(package.with_suffix('.sha256').read_text().split()[0], digest)
            with zipfile.ZipFile(package) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('ai_settings.py', archive.namelist())
                self.assertIn('installation_validation.py', archive.namelist())
                self.assertEqual(json.loads(archive.read('tool.json'))['entrypoint'], 'service.py')
            # Real host environment and authentication; no network or user data required.
            with patch.dict(os.environ, {'IFS_COMPANION_PYTHON':sys.executable}):
                manager = ToolManager(root/'data/companion')
                try:
                    manager.install(package)
                    saved = manager.data/'ifs-scenario-builder/scenarios/saved.sce'
                    saved.parent.mkdir(parents=True)
                    saved.write_text('CUSTOM,example,1')
                    manager.start('ifs-scenario-builder')
                    for asset in ('', 'scenario.js', 'scenario.css', 'bridge.js'):
                        with manager.request('ifs-scenario-builder', asset) as response:
                            self.assertGreater(len(response.read()), 0)
                    with manager.request('ifs-scenario-builder', 'bridge/status') as response:
                        self.assertFalse(json.load(response)['running'])
                    manager.stop('ifs-scenario-builder')
                    manager.uninstall('ifs-scenario-builder')
                    self.assertEqual(saved.read_text(), 'CUSTOM,example,1')
                finally:
                    manager.close()
