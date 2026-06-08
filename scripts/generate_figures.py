#!/usr/bin/env python3
"""Regenerate figures from saved experiment result CSVs."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.figure_generation import generate_all_figures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate all figures from saved result tables.")
    parser.add_argument("--results-dir", type=Path, default=Path("results"), help="Directory containing result CSVs.")
    parser.add_argument("--figures-dir", type=Path, default=Path("figures"), help="Directory to write figures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)
    paths = generate_all_figures(results_dir=args.results_dir, figures_dir=args.figures_dir)
    print(f"Regenerated {len(paths)} figure files in {args.figures_dir.resolve()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
