#!/usr/bin/env python3
"""Author the small self-contained notebook without a Jupyter dependency."""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demo_analysis import evaluate, stable_mask


def cell(kind, source):
    item = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        item.update(execution_count=None, outputs=[])
    return item


def main():
    cells = [
        cell("markdown", """# Try the occupancy study

**Junyu Chen · Chong Li**

Recompute the paper's fixed recommendation comparison from a compact export of 43 saved test horizons. This notebook does not train models or run a building controller. Its core calculations use only Python's standard library; Matplotlib is optional for the figure.

[Research overview](https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/) · [Interactive browser demo](https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/demo/) · [Full reproduction guide](https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/blob/main/REPRODUCING.md)

Use **Run all**. The first cell reads the local checked-in export when available; otherwise it downloads the public JSON from GitHub. No private data or credentials are needed. The export records source SHA-256 hashes so you can identify which records you used.
"""),
        cell("code", '''import json
import math
from pathlib import Path
from urllib.request import urlopen

DEMO_DATA_URL = "https://raw.githubusercontent.com/stevenchenjy/decision-aware-occupancy-forecasting/main/docs/demo/data.json"
local = next((p for p in [Path("docs/demo/data.json"), Path("../docs/demo/data.json")] if p.exists()), None)
if local:
    payload = json.loads(local.read_text())
    print("Data source:", local)
else:
    with urlopen(DEMO_DATA_URL, timeout=30) as response:
        payload = json.load(response)
    print("Data source:", DEMO_DATA_URL)
assert payload["schemaVersion"] == 1
assert len(payload["days"]) == 43
print(payload["scope"])
print(payload["timeConvention"])
for source in payload["sources"]:
    print(source["path"], "SHA-256:", source["sha256"])
'''),
        cell("markdown", """## Account for recommendations

An interval is recommended when its uncalibrated Empty score meets the threshold and belongs to a continuous run long enough to meet the duration requirement. Runs stop at each horizon boundary. A conflict means a recommended interval was subsequently camera-labeled occupied. The load proxy sums processed HVAC-plus-lighting load in recommended intervals subsequently camera-labeled empty.

The functions below are copied from `src/demo_analysis.py` so you can inspect and run them without importing the research training environment.
"""),
        cell("code", 'MODELS = {model["id"]: model["label"] for model in payload["models"]}\n\n' + inspect.getsource(stable_mask) + '\n' + inspect.getsource(evaluate)),
        cell("markdown", """## Reproduce the reported fixed policies

Each model uses its own validation-selected threshold and a one-hour minimum window. All counts below use the same 4,128 unique policy intervals. The manuscript's 388,032 overlapping forecast rows are a different evaluation scope.
"""),
        cell("code", '''reported = []
print(f'{"Model":<22} {"Threshold":>9} {"Windows":>8} {"Intervals":>10} {"Conflicts":>10} {"Load proxy (kWh)":>17}')
for model in payload["models"]:
    result = evaluate(payload["days"], model["id"], model["reportedThreshold"], 4)
    for key, expected in model["reportedMetrics"].items():
        assert math.isclose(result[key], expected, rel_tol=1e-10, abs_tol=1e-7), (model["id"], key)
    reported.append({"model": model["id"], "label": model["label"], **result})
    print(f'{model["label"]:<22} {model["reportedThreshold"]:>9.3f} {result["recommendedWindows"]:>8} {result["recommendedIntervals"]:>10} {result["conflictIntervals"]:>10} {result["opportunityKwh"]:>17.1f}')
hybrid = reported[0]
assert (hybrid["recommendedWindows"], hybrid["recommendedIntervals"], hybrid["conflictIntervals"]) == (14, 259, 0)
assert math.isclose(hybrid["opportunityKwh"], 490.1463795265, abs_tol=1e-7)
print("\\nAll three fixed policy rows match the documented comparison.")
'''),
        cell("code", '''try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Optional plot skipped: Matplotlib is not installed. The verified numerical results are above.")
else:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    labels = [row["label"] for row in reported]
    colors = ["#13685e", "#80968f", "#bf7947"]
    for ax, key, title in zip(axes, ["opportunityKwh", "conflictIntervals"], ["Processed-load overlap (kWh)", "Camera-label conflict intervals"]):
        ax.barh(labels, [row[key] for row in reported], color=colors)
        ax.invert_yaxis()
        ax.set_title(title, fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Fixed policies on 43 recorded test horizons", fontsize=13)
    fig.tight_layout()
    plt.show()
print("Load overlap is not measured energy savings. Zero recorded conflicts does not guarantee future performance.")
'''),
        cell("markdown", """## Explore a different setting

Edit the values below and run the cell. This reuses an already inspected test period. It cannot establish a new validated policy or a confirmed improvement. The fixed reported table above remains unchanged.
"""),
        cell("code", '''model_id = "hybrid"     # "hybrid", "historical", or "lightgbm"
threshold = 0.80         # an uncalibrated score cutoff, not an occupancy probability
minimum_hours = 2       # 1, 2, or 4
assert minimum_hours in (1, 2, 4)
exploratory = evaluate(payload["days"], model_id, threshold, minimum_hours * 4)
print("EXPLORATORY REPLAY: no new validation or model selection")
print(json.dumps(exploratory, indent=2))
'''),
        cell("markdown", """## Share what you actually reproduced

[Open a reproduction report](https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/issues/new?template=reproduction.yml) with the commit or source hashes, environment, commands, and observed outputs. Failed attempts are useful. A successful run here reproduces saved-output accounting; it does not establish independent predictive generalization, operational adoption, energy savings, or verified physical absence.

The input is a cleaned, imputed dataset. Original source timestamp and imputation provenance remain unresolved. Prospective work requires a corrected, protocol-locked empirical rerun and fresh evaluation data. See [the claim limits](https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/blob/main/CLAIMS_AND_LIMITATIONS.md).
"""),
    ]
    for i, item in enumerate(cells):
        item["id"] = f"occupancy-{i:02}"
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}, "colab": {"name": "try_the_study.ipynb", "provenance": []}}, "nbformat": 4, "nbformat_minor": 5}
    path = ROOT / "notebooks/try_the_study.ipynb"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
    print("Wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
