#!/usr/bin/env python3
"""Print manual download instructions for the LBNL Building 59 dataset."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIR = REPO_ROOT / "doi_10_7941_D1N33Q__v20220202" / "Building_59" / "Bldg59_clean data"


def main() -> int:
    message = f"""
    Automated download is not implemented yet.

    Dataset:
      LBNL Building 59 Office Building Dataset

    Dryad DOI:
      10.7941/D1N33Q

    Source:
      https://doi.org/10.7941/D1N33Q

    Download the Dryad package, extract Building_59, and place the cleaned data at:

      {EXPECTED_DIR}

    Required files:
      occ.csv
      wifi.csv
      site_weather.csv
      zone_temp_interior.csv
      ele.csv
      zone_co2.csv

    Raw data is intentionally not committed to this repository.
    See DATA.md for the full expected folder structure.
    """
    print(dedent(message).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

