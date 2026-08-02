from argparse import Namespace
from pathlib import Path

import pytest

from scripts.run_all import (
    DEFAULT_FIGURES_DIR,
    DEFAULT_PREDICTIONS_DIR,
    DEFAULT_RESULTS_DIR,
    validate_isolated_output_dirs,
)


def test_legacy_replay_defaults_are_isolated():
    args = Namespace(
        results_dir=DEFAULT_RESULTS_DIR,
        figures_dir=DEFAULT_FIGURES_DIR,
        predictions_dir=DEFAULT_PREDICTIONS_DIR,
    )
    validate_isolated_output_dirs(args)


def test_legacy_replay_rejects_a_canonical_or_parent_output_directory():
    args = Namespace(
        results_dir=Path("results"),
        figures_dir=Path("figures"),
        predictions_dir=Path("predictions"),
    )
    with pytest.raises(ValueError, match="canonical"):
        validate_isolated_output_dirs(args)

    args.results_dir = Path(".")
    with pytest.raises(ValueError, match="canonical"):
        validate_isolated_output_dirs(args)
