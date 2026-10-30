#!/usr/bin/env python3
"""Execute notebook code cells locally and reconcile the reported comparison."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.chdir(ROOT)
    os.environ.setdefault("MPLBACKEND", "Agg")
    notebook = json.loads((ROOT / "notebooks/try_the_study.ipynb").read_text())
    namespace = {"__name__": "__main__"}
    for i, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            exec(compile("".join(cell["source"]), f"notebook-cell-{i}", "exec"), namespace)
    assert len(namespace["reported"]) == 3
    print("Notebook code cells passed using the local checked-in export.")


if __name__ == "__main__":
    main()
