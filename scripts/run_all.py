#!/usr/bin/env python3
"""Run the full Python-first LBNL occupancy forecasting pipeline."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.figure_generation import generate_all_figures
from src.hybrid_analysis import generate_hybrid_artifacts
from src.lbnl_pipeline import Config, run_pipeline


DEFAULT_DATA_DIR = Path("doi_10_7941_D1N33Q__v20220202") / "Building_59" / "Bldg59_clean data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the end-to-end research pipeline.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Path to the cleaned LBNL Building 59 data folder.")
    parser.add_argument("--results-dir", type=Path, default=Path("results"), help="Directory for result CSVs.")
    parser.add_argument("--figures-dir", type=Path, default=Path("figures"), help="Directory for generated figures.")
    parser.add_argument("--skip-figures", action="store_true", help="Run modeling and tables without regenerating figures.")
    parser.add_argument("--show-notebook-output", action="store_true", help="Display report-style tables when run in IPython.")
    parser.add_argument(
        "--allow-missing-data",
        action="store_true",
        help="Attempt execution even if the expected LBNL data folder is missing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)
    data_dir = args.data_dir

    if not data_dir.exists() and not args.allow_missing_data:
        print("Expected data folder is missing:", file=sys.stderr)
        print(f"  {data_dir.resolve()}", file=sys.stderr)
        print("Read DATA.md or run scripts/download_data.py for placement instructions.", file=sys.stderr)
        print("Use --allow-missing-data only if you pass a custom --data-dir that will exist at runtime.", file=sys.stderr)
        return 1

    cfg = Config(
        data_dir=str(data_dir),
        result_dir=str(args.results_dir),
        figure_dir=str(args.figures_dir),
    )
    run_pipeline(config=cfg, make_figures=not args.skip_figures, show=args.show_notebook_output)
    if not args.skip_figures:
        generate_all_figures(results_dir=args.results_dir, figures_dir=args.figures_dir)
    generate_hybrid_artifacts(
        results_dir=args.results_dir,
        figures_dir=args.figures_dir,
        predictions_dir=Path("predictions"),
        make_figures=not args.skip_figures,
    )
    print("Pipeline execution completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
