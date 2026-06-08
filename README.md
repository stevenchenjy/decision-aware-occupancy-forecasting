# Decision-Aware Occupancy Forecasting Research Prototype

This repository evaluates day-ahead occupancy forecasting for identifying stable empty windows in an office building. The current implementation is best described as:

`occupancy forecasting + risk-constrained recommendation post-processing`

The models forecast future occupancy probabilities. A decision layer then selects empty-window recommendations by sweeping Empty-probability thresholds on the validation split and evaluating the selected policy on the held-out test split.

## What The Project Does

- Builds 15-minute occupancy labels from the LBNL Building 59 south-zone occupancy streams.
- Aligns occupancy, WiFi, weather, interior temperature, and electrical meter streams.
- Trains several forecasting baselines: Historical Average, LightGBM, Random Forest, DLinear, and Transformer.
- Converts forecasts into stable empty-window recommendations.
- Reports occupancy-conflict risk and safe shiftable-load opportunity under validation-selected risk constraints.

## Safe Shiftable-Load Opportunity

Safe shiftable-load opportunity is an offline estimate of controllable load that coincides with recommended intervals that were actually empty.

For the default setting:

`P_controllable = hvac_S + lig_S`

For each safe recommended 15-minute interval:

`kWh = P_controllable * 0.25`

Intervals with occupancy conflicts are excluded from the safe opportunity total.

This is not verified energy savings. The repository does not include a counterfactual building simulation, BMS intervention, thermal-comfort model, or occupant-response study. The energy numbers should be interpreted as offline opportunity estimates only.

## Main Reported Result

Under the 10% validation-selected occupancy-conflict policy, LightGBM selected an Empty-probability threshold of 0.95. On the test daily schedules, it reported:

- Test occupancy conflict rate: 4.15%
- Safe shiftable-load opportunity: 493.9 kWh
- Recommended windows: 19
- Safe windows: 16
- Test period: 2019-01-09 to 2019-02-21 local Pacific time

Historical Average has the highest model-level Empty AUPRC, which shows that periodic occupancy structure is strong. LightGBM gives a stronger practical risk-opportunity tradeoff under the 10% recommendation policy in the current experiment.

## Reproduce The Results

1. Read [DATA.md](DATA.md) and download the LBNL Building 59 dataset from Dryad.
2. Place the extracted data at:

   `doi_10_7941_D1N33Q__v20220202/Building_59/Bldg59_clean data/`

3. Create an environment with Python 3.10-3.12.
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Check the environment:

   ```bash
   python scripts/check_environment.py
   ```

6. Execute the current end-to-end notebook:

   ```bash
   python scripts/run_all.py
   ```

The notebook writes outputs to `results/`, `figures/`, and `predictions/`.

## Current Limitations

- Single-building, selected-zone evaluation.
- Short held-out test period with only 43 non-overlapping daily schedules.
- Model metrics use overlapping rolling forecast intervals, so effective sample size is smaller than the interval count.
- Threshold selection is validation-only, but risk estimates are fragile because daily validation/test blocks are limited.
- Energy opportunity uses realized loads offline and is not deployable expected savings.
- Model training uses standard BCE losses. A true decision-aware loss is not implemented yet.
- Transformer and DLinear baselines are exploratory and lightly tuned.

See [LIMITATIONS.md](LIMITATIONS.md) and [ROADMAP.md](ROADMAP.md) for reviewer-facing caveats and planned improvements.

