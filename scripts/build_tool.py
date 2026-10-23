"""Build Scenario Builder using Companion's shared Python packaging."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--version', required=True)
    parser.add_argument('--release-notes', type=Path, default=ROOT/'RELEASE_NOTES.md')
    parser.add_argument('--release-date')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    companion = Path(os.environ.get('IFS_COMPANION_PATH', ROOT.parent/'ifs-companion'))
    command = [args.python, str(companion/'packaging/build_shared_tool.py'),
               '--tool', 'ifs-scenario-builder', '--source', str(ROOT), '--version', args.version,
               '--release-notes', str(args.release_notes)]
    if args.release_date: command += ['--release-date', args.release_date]
    if args.output_dir: command += ['--output-dir', str(args.output_dir)]
    subprocess.run(command, check=True)


if __name__ == '__main__': main()
