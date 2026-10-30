#!/usr/bin/env python3
"""Generate or verify the compact browser/notebook data from canonical CSVs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demo_analysis import build_payload, payload_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed demo export is stale")
    args = parser.parse_args()
    output = ROOT / "docs/demo/data.json"
    expected = payload_text(build_payload())
    if args.check:
        if not output.exists() or output.read_text() != expected:
            raise SystemExit("Demo data are stale. Run: python scripts/build_demo.py")
        print("Demo data match canonical inputs, hashes, and all three reported policy rows.")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected)
        print(f"Wrote {output.relative_to(ROOT)} ({len(expected.encode()):,} bytes)")


if __name__ == "__main__":
    main()
