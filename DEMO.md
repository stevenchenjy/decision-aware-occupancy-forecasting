# Try and reproduce the study

The [browser demonstration](https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/demo/) replays recorded occupancy scores and building-load exports. It uses no model service, third-party scripts, or visitor analytics in its own code. Hosting providers may keep access logs.

## What the controls do

Choose one of the three canonical models, an Empty-score threshold from 0.050 to 0.950, and a minimum duration of one, two, or four hours. The rule keeps every contiguous threshold-passing run that meets the duration requirement within one saved horizon. It does not join adjacent daily horizons.

The initial hybrid settings are the manuscript's fixed policy: threshold 0.875 and a one-hour minimum window. The other models restore their own validation-selected thresholds when selected. Changing a threshold or duration marks the replay as exploratory. Restore the reported policy to return to the documented operating point for the selected model.

The main counts always cover all 43 non-overlapping saved test horizons. Changing the example date changes only the plot and its accessible table. The initial example has the largest processed-load overlap under the fixed hybrid rule; it is an illustration, not a representative-day claim.

The CSV download includes every target interval, current settings, analysis status, scores, labels, recommendations, conflicts, and processed-load overlap. The [JSON export](docs/demo/data.json) includes all input records, source SHA-256 hashes, and a 333-setting reference grid computed by Python. The browser calculates results directly from the records; it does not merely look up those grid totals.

## Notebook

[Open in Colab](https://colab.research.google.com/github/stevenchenjy/decision-aware-occupancy-forecasting/blob/main/notebooks/try_the_study.ipynb) or open `notebooks/try_the_study.ipynb` in Jupyter. It recomputes the reported comparison without training a model. You can choose a threshold and duration in a separate, explicitly exploratory cell.

From a local checkout, `python3 scripts/check_demo_notebook.py` executes all code cells against the checked-in export and verifies the expected results. It does not require Jupyter or contact a notebook service. Actual Colab execution is a separate browser/service check.

## Rebuild and inspect

```bash
python3 scripts/build_demo.py
python3 scripts/build_demo.py --check
python3 -m unittest discover -s tests -p 'test_demo_analysis.py' -v
node --test tests/demo-policy.test.cjs
python3 scripts/check_demo_notebook.py
python3 -m http.server 8765 --directory docs
```

Open `http://localhost:8765/demo/`. No training dependencies are needed for the demo builder, replay, notebook calculations, or lightweight checks. The optional notebook plot uses Matplotlib when available.

The builder reads the three canonical source files named in the JSON, extracts the 43 midnight-labelled policy horizons, verifies target non-overlap and complete 96-step ordering, maps processed loads to targets, computes the fixed hybrid scores, and reconciles all three default policies against `results/canonical_policy_10pct.csv`. It never edits source CSVs or chooses a new model on test outcomes.

## Interpretation

The input is a cleaned, imputed release. A 00:00 anchor covers the completed 00:00-00:15 input bin; targets span 00:15 to the next 00:15. The demo does not establish prospective source availability. Scores are uncalibrated. Recorded camera-empty labels do not verify physical absence. Processed HVAC-plus-lighting overlap is not measured savings, controllable capacity, or a comfort outcome.

The paired AUPRC uncertainty comparisons in the manuscript cross zero. No claim of statistically decisive model superiority follows from the demo. Exploring the already inspected test period cannot establish a new confirmed policy. See [CLAIMS_AND_LIMITATIONS.md](CLAIMS_AND_LIMITATIONS.md) and [the empirical rerun plan](paper/audits/rerun_manifest.md).

To help, [file a reproduction report](https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/issues/new?template=reproduction.yml) describing what you actually ran and obtained.
