# Contributing to the occupancy study

Useful contributions include testing the reproduction instructions, reporting an accounting or documentation problem, and improving the small demonstration. You do not need to train models or have building-control expertise to start.

## Try the study

- [Open the browser demonstration](https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/demo/). It needs no installation.
- [Run the notebook in Colab](https://colab.research.google.com/github/stevenchenjy/decision-aware-occupancy-forecasting/blob/main/notebooks/try_the_study.ipynb), or download `notebooks/try_the_study.ipynb` and run it locally.
- [Report a reproduction](https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/issues/new?template=reproduction.yml). Include the exact commit, environment, command, observed output, and any difference. An unsuccessful attempt is useful too.

Please distinguish reproducing saved-output calculations from retraining models. The demo and notebook replay 43 recorded horizons. Neither performs a new prospective evaluation.

## Lightweight local checks

The demonstration data builder and Python replay use only the Python standard library. Node.js 20 or later runs the cross-language checks. From the repository root:

```bash
python3 scripts/build_demo.py --check
python3 -m unittest discover -s tests -p 'test_demo_analysis.py' -v
node --test tests/demo-policy.test.cjs
python3 scripts/check_demo_notebook.py
python3 -m http.server 8765 --directory docs
```

Open `http://localhost:8765/demo/`. Change the model, threshold, minimum duration, and example date. Check that the replay label changes appropriately, the fixed reported table stays unchanged, the CSV reflects the current settings, and keyboard controls work.

For the broader scientific analysis, use [REPRODUCING.md](REPRODUCING.md) and the full dependency environment. The lightweight checks do not replace those tests.

## Propose a change

1. Check the [open issues](https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/issues) for a task or describe the problem in a new issue.
2. Work in a branch. Keep each pull request focused on one problem.
3. Explain what a reader or researcher can now do, and include the checks you ran. Screenshots help when a browser view changes.
4. Preserve source provenance and label exploratory analyses. Do not overwrite canonical results to make a new method appear better on an already inspected test period.
5. If demo generation changes, run `python3 scripts/build_demo.py` and include the updated export. Document scientific changes separately from presentation changes.

The default demo must continue to reproduce 259 recommended intervals, 14 windows, zero recorded camera-label conflicts, and approximately 490.1464 kWh of processed-load overlap for the fixed hybrid policy. Test-derived parameter exploration cannot establish a new confirmed result. Camera labels do not establish physical absence, and load overlap does not establish energy savings.

Do not upload credentials, personal data, or data you lack permission to redistribute. Contributions of original code are made under the repository's [MIT software license](LICENSE); keep third-party notices and the [licensing scope](LICENSING.md) intact.

## Evidence of outside use

Report only work you actually attempted. A star records interest; a clone or fork alone does not demonstrate successful reproduction or operational adoption. The issue template lets contributors state whether they opened the demo, reproduced saved-output metrics, or attempted an independent extension. Please avoid claims of deployment or energy savings without supporting evidence.
