#!/usr/bin/env python3
"""Check third-party and local imports needed by the research prototype."""

from __future__ import annotations

import importlib
import sys
from importlib import metadata
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("sklearn", "scikit-learn"),
    ("lightgbm", "lightgbm"),
    ("torch", "torch"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
]

LOCAL_MODULES = [
    "src.data_preprocessing",
    "src.energy_opportunity",
    "src.evaluation",
    "src.feature_engineering",
    "src.figure_generation",
    "src.lbnl_pipeline",
    "src.models",
    "src.plotting",
    "src.recommendation_policy",
]


def version_for(distribution_name: str) -> str:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return "unknown"


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"Executable: {sys.executable}")
    print(f"Repository: {REPO_ROOT}")

    failures: list[str] = []
    if not ((3, 10) <= sys.version_info[:2] <= (3, 12)):
        failures.append("Python version: use Python 3.10, 3.11, or 3.12")
        print("  FAIL Python version: use Python 3.10, 3.11, or 3.12")

    print("\nThird-party packages:")
    for module_name, distribution_name in PACKAGES:
        try:
            importlib.import_module(module_name)
            print(f"  OK {module_name}=={version_for(distribution_name)}")
        except Exception as exc:  # pragma: no cover - exercised by missing envs
            failures.append(f"{module_name}: {exc}")
            print(f"  FAIL {module_name}: {exc}")

    print("\nLocal modules:")
    for module_name in LOCAL_MODULES:
        try:
            importlib.import_module(module_name)
            print(f"  OK {module_name}")
        except Exception as exc:  # pragma: no cover - exercised by missing envs
            failures.append(f"{module_name}: {exc}")
            print(f"  FAIL {module_name}: {exc}")

    if failures:
        print("\nEnvironment check failed. Install dependencies with:")
        print("  python -m pip install -r requirements.txt")
        print("\nRecommended interpreter:")
        print("  Python 3.11 in a virtualenv or the Conda environment from environment.yml")
        if any("libomp" in failure.lower() or "lightgbm" in failure.lower() for failure in failures):
            print("\nmacOS LightGBM note:")
            print("  If LightGBM fails to load libomp.dylib, install OpenMP first:")
            print("  brew install libomp")
        print("\nFailures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nEnvironment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
