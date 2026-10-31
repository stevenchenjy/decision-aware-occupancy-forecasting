#!/usr/bin/env python3
"""Check an extracted release kit without site packages or network access."""
import argparse
import csv
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="occupancy-kit-check-") as folder:
        with zipfile.ZipFile(args.archive) as archive:
            for name in archive.namelist():
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts or path.parts[0] != "occupancy-replay-kit":
                    raise ValueError("Unexpected archive path")
            if archive.testzip():
                raise ValueError("Archive CRC check failed")
            archive.extractall(folder)
        root = Path(folder) / "occupancy-replay-kit"
        command = """import runpy,socket,sys
def blocked(*args,**kwargs):
    raise RuntimeError('Network access is disabled for this check')
socket.socket=blocked
socket.create_connection=blocked
sys.argv=['replay.py','--receipt','receipt.json','--csv','comparison.csv']
runpy.run_path('replay.py',run_name='__main__')
"""
        completed = subprocess.run([sys.executable, "-S", "-c", command], cwd=root, capture_output=True, text=True, timeout=30)
        if completed.returncode:
            raise RuntimeError(completed.stdout + completed.stderr)
        record = json.loads((root / "receipt.json").read_text())
        manifest = json.loads((root / "kit-manifest.json").read_text())
        assert record["kit_integrity_checked"]
        assert record["source_commit"] == manifest["source_commit"]
        with (root / "comparison.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 3 and all(row["analysis_status"] == "reported_fixed_policy" for row in rows)
        assert [(int(row["recommendedWindows"]), int(row["recommendedIntervals"]), int(row["conflictIntervals"])) for row in rows] == [(14, 259, 0), (12, 66, 0), (19, 265, 11)]
        print(completed.stdout.rstrip())
        print("Extracted kit passed with site packages and network access disabled.")
        print("Source commit:", record["source_commit"])


if __name__ == "__main__":
    main()
