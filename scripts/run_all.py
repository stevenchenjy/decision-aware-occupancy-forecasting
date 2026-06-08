#!/usr/bin/env python3
"""Execute the current end-to-end experiment notebook with nbclient."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOK = REPO_ROOT / "LBNL_occupancy_forecasting_main.ipynb"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "executed_notebook.ipynb"
DEFAULT_DATA_DIR = REPO_ROOT / "doi_10_7941_D1N33Q__v20220202" / "Building_59" / "Bldg59_clean data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the current notebook-based experiment.")
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK, help="Notebook to execute.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Executed notebook output path.")
    parser.add_argument("--timeout", type=int, default=1200, help="Per-cell timeout in seconds.")
    parser.add_argument("--kernel", default="python3", help="Jupyter kernel name.")
    parser.add_argument(
        "--allow-missing-data",
        action="store_true",
        help="Attempt execution even if the expected LBNL data folder is missing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notebook_path = args.notebook.resolve()
    output_path = args.output.resolve()

    if not notebook_path.exists():
        print(f"Notebook not found: {notebook_path}", file=sys.stderr)
        return 1

    if not DEFAULT_DATA_DIR.exists() and not args.allow_missing_data:
        print("Expected data folder is missing:", file=sys.stderr)
        print(f"  {DEFAULT_DATA_DIR}", file=sys.stderr)
        print("Read DATA.md or run scripts/download_data.py for placement instructions.", file=sys.stderr)
        print("Use --allow-missing-data only if the notebook has been modified to use another path.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Executing notebook: {notebook_path}")
    print(f"Working directory: {REPO_ROOT}")
    print(f"Output notebook: {output_path}")

    with notebook_path.open("r", encoding="utf-8") as handle:
        notebook = nbformat.read(handle, as_version=4)

    client = NotebookClient(
        notebook,
        timeout=args.timeout,
        kernel_name=args.kernel,
        resources={"metadata": {"path": str(REPO_ROOT)}},
    )
    client.execute()

    with output_path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)

    print("Notebook execution completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

