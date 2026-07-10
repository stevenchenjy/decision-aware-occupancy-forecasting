#!/usr/bin/env python3
"""Regenerate validation-selected hybrid tables, predictions, uncertainty, and figures."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.hybrid_analysis import generate_hybrid_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate hybrid artifacts from canonical saved validation/test predictions."
    )
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--figures-dir", type=Path, default=Path("figures"))
    parser.add_argument("--predictions-dir", type=Path, default=Path("predictions"))
    parser.add_argument("--bootstrap-reps", type=int, default=2000)
    parser.add_argument("--skip-figures", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)
    paths = generate_hybrid_artifacts(
        results_dir=args.results_dir,
        figures_dir=args.figures_dir,
        predictions_dir=args.predictions_dir,
        make_figures=not args.skip_figures,
        bootstrap_reps=args.bootstrap_reps,
    )
    print(f"Regenerated {len(paths)} hybrid artifacts.")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

