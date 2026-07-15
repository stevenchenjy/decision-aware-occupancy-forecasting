#!/usr/bin/env python3
"""Run the saved-output window-aware decision study."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.window_aware_decision_search import run_window_aware_decision_search


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run validation-only window-aware selection and a frozen retrospective diagnostic."
    )
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--figures-dir", type=Path, default=Path("figures"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)
    paths = run_window_aware_decision_search(
        results_dir=args.results_dir,
        figures_dir=args.figures_dir,
        reports_dir=args.reports_dir,
    )
    print(f"Generated {len(paths)} window-aware artifacts.")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

