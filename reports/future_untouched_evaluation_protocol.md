# Future untouched evaluation protocol

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: plan/validate
- Verification Status: ANALYZED
- Version Label: future_untouched_protocol_v1

## Purpose and data firewall

Apply the frozen candidates once to a chronological period whose labels, loads, outcomes, and qualitative examples have not been inspected during model training, canonical selection, decision-aware selection, or this window-aware study. Do not change a weight, threshold, metric, floor, tie-break, or promotion criterion after opening that period.

## Frozen candidates

- Canonical forecast-optimal primary: `0.15/0.60/0.25`, threshold `0.875`.
- Exploratory decision-optimal: `0.65/0.05/0.30`, threshold `0.775`.
- Exploratory 99%-AUPRC-floor: `0.35/0.35/0.30`, threshold `0.800`.
- **Primary window-aware challenger:** `0.40/0.40/0.20`, threshold `0.850`, selected under validation `W_min=85%` and `Q=99%`.
- Secondary, multiplicity-labeled window-floor sensitivity candidates:
  - W>=80%, Q=99%: `0.05/0.75/0.20`, threshold `0.875`.
  - W>=90%, Q=99%: `0.30/0.60/0.10`, threshold `0.900`.
  - W>=95%, Q=99%: `0.10/0.65/0.25`, threshold `0.950`.
  - W>=100%, Q=99%: `0.10/0.65/0.25`, threshold `0.950`.

Only the primary window-aware challenger is eligible for the primary promotion comparison. The other window-floor variants are secondary sensitivity analyses and cannot be substituted after seeing future outcomes.

## Evaluation unit and fixed calculations

- Use complete non-overlapping midnight-anchored 96-step horizons, matching the validation policy scope.
- Keep the stable-window requirement at four consecutive 15-minute intervals.
- Use the saved definition of controllable-load opportunity: HVAC south plus lighting south interval kWh.
- Report both aggregate totals and paired daily values. Preserve day identifiers for day-block uncertainty and influence analysis.

## Primary future metric

- **Safe opportunity kWh**, paired by day against the canonical primary. Also report kWh per evaluation day so periods of different duration remain comparable.

## Safety metrics

- Interval conflict rate.
- Fully safe window rate/window precision.
- Number of conflict windows.
- Longest continuous occupied duration within a recommended window.
- Total occupied minutes inside recommended windows.
- Controllable-load kWh associated with conflict intervals.

## Forecasting metrics

- Empty AUPRC, precision, recall, and F1 on all saved rolling forecasts for the untouched period.

## Pre-specified promotion criteria

The primary window-aware challenger may replace the canonical primary only if **all** criteria hold:

1. Safe opportunity is at least 10% higher than canonical and, for a period comparable to the current 43-day evaluation, at least 50 kWh higher. For another duration, scale the absolute criterion as `1.16 kWh × evaluation days` (50/43), while retaining the 10% criterion.
2. Interval conflict rate is `<=10%`.
3. Fully safe window rate is `>=85%`.
4. Empty AUPRC is at least 99% of canonical on the same untouched period.
5. Recommendation coverage is at least 80% of canonical coverage and at least 2% absolute; at least 10 windows must be recommended.
6. Leave-one-day-out influence analysis shows the safe-opportunity gain remains positive after removing each of the two highest-load gain days; the gain cannot be driven by only one or two unusually high-load days.
7. A paired daily-block 95% interval for the safe-opportunity difference is reported. Promotion requires its lower bound to be above zero; this is an added evidential gate, not a claim of guaranteed future performance.

The 10% relative and 50 kWh comparable-period thresholds are deliberately round, operationally interpretable effect thresholds. They were fixed without optimizing against the already-inspected current test diagnostic.

## Execution and reporting order

1. Record the untouched period boundaries and hash all inputs before computing outcomes.
2. Generate all frozen candidate probabilities and recommendations in one run.
3. Compute forecasting, interval, window, severity, coverage, and daily influence metrics.
4. Run the paired daily-block analysis.
5. Apply the promotion criteria mechanically; do not choose among sensitivity candidates.
6. Publish failures as well as passes and retain the canonical primary unless every gate passes.

## Work that cannot be completed now

- Acquire and lock a genuinely new chronological occupancy/load period.
- Produce frozen base-model probabilities for that period without adapting the trained models.
- Apply the candidates once, compute the paired daily evidence, and make the promotion decision.

The present validation study and current-test retrospective diagnostic cannot substitute for this untouched evaluation.
