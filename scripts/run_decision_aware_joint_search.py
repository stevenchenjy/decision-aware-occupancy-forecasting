#!/usr/bin/env python3
"""Run the saved-output decision-aware joint validation search."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.decision_aware_joint_search import run_decision_aware_joint_search


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit saved inputs, select joint weight-threshold candidates on validation, "
            "then evaluate the fixed candidates on held-out test."
        )
    )
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--predictions-dir", type=Path, default=Path("predictions"))
    parser.add_argument("--figures-dir", type=Path, default=Path("figures"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)
    paths = run_decision_aware_joint_search(
        results_dir=args.results_dir,
        predictions_dir=args.predictions_dir,
        figures_dir=args.figures_dir,
        reports_dir=args.reports_dir,
    )
    print(f"Generated {len(paths)} decision-aware joint-search artifacts.")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

