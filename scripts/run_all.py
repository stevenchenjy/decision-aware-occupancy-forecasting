#!/usr/bin/env python3
"""Run a quarantined legacy cleaned-release replay.

This entry point deliberately cannot be used as a prospective or empirical
rerun. It replays the historical implementation against a cleaned release
and writes only to an isolated output directory.
"""

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
LEGACY_OUTPUT_ROOT = Path("runs") / "legacy_cleaned_replay"
DEFAULT_RESULTS_DIR = LEGACY_OUTPUT_ROOT / "results"
DEFAULT_FIGURES_DIR = LEGACY_OUTPUT_ROOT / "figures"
DEFAULT_PREDICTIONS_DIR = LEGACY_OUTPUT_ROOT / "predictions"
CANONICAL_OUTPUT_DIRS = (Path("results"), Path("figures"), Path("predictions"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay the legacy cleaned-release pipeline in an isolated directory."
    )
    parser.add_argument(
        "--legacy-cleaned-replay",
        action="store_true",
        help=(
            "Acknowledge that this is a historical cleaned-release replay, "
            "not an empirical/prospective rerun."
        ),
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Path to the cleaned LBNL Building 59 data folder.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR, help="Isolated directory for replay result CSVs.")
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES_DIR, help="Isolated directory for replay figures.")
    parser.add_argument("--predictions-dir", type=Path, default=DEFAULT_PREDICTIONS_DIR, help="Isolated directory for replay prediction exports.")
    parser.add_argument("--skip-figures", action="store_true", help="Run modeling and tables without regenerating figures.")
    parser.add_argument("--show-notebook-output", action="store_true", help="Display report-style tables when run in IPython.")
    parser.add_argument(
        "--allow-missing-data",
        action="store_true",
        help="Attempt execution even if the expected LBNL data folder is missing.",
    )
    return parser.parse_args()


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_isolated_output_dirs(args: argparse.Namespace) -> None:
    """Reject output locations that can overwrite canonical saved artifacts."""
    selected = {
        "results": _absolute(args.results_dir).resolve(),
        "figures": _absolute(args.figures_dir).resolve(),
        "predictions": _absolute(args.predictions_dir).resolve(),
    }
    canonical = tuple((_absolute(path).resolve() for path in CANONICAL_OUTPUT_DIRS))
    for name, directory in selected.items():
        for protected in canonical:
            if directory == protected or _contains(directory, protected):
                raise ValueError(
                    f"{name} output directory {directory} can overwrite canonical "
                    f"saved artifacts at {protected}; choose an isolated directory."
                )


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)
    if not args.legacy_cleaned_replay:
        print(
            "Refusing to run. This command is a legacy cleaned-release replay, "
            "not an empirical/prospective rerun. Re-run with --legacy-cleaned-replay "
            "only to reproduce historical artifacts in an isolated directory.",
            file=sys.stderr,
        )
        return 2
    try:
        validate_isolated_output_dirs(args)
    except ValueError as exc:
        print(f"Refusing to run: {exc}", file=sys.stderr)
        return 2
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
        prediction_dir=str(args.predictions_dir),
    )
    run_pipeline(config=cfg, make_figures=not args.skip_figures, show=args.show_notebook_output)
    if not args.skip_figures:
        generate_all_figures(results_dir=args.results_dir, figures_dir=args.figures_dir)
    generate_hybrid_artifacts(
        results_dir=args.results_dir,
        figures_dir=args.figures_dir,
        predictions_dir=args.predictions_dir,
        make_figures=not args.skip_figures,
    )
    print("Legacy cleaned-release replay completed. It is not empirical or prospective validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
