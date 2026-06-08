# Limitations

This repository is a research prototype. The current results should be interpreted with the following limitations.

- Single-building scope: conclusions are limited to LBNL Building 59 selected south zones.
- Limited test horizon: the main recommendation evaluation uses 43 non-overlapping daily test schedules.
- Overlapping forecast intervals: model-level AUPRC/F1 metrics use dense rolling forecasts, so the effective sample size is smaller than the interval count.
- Validation threshold fragility: risk-constrained thresholds are selected on a small validation set of daily schedules.
- Offline energy opportunity: safe shiftable-load opportunity uses realized future loads and is not a counterfactual estimate of deployable savings.
- No BMS intervention: no real building-management action, occupant feedback, or control experiment is included.
- No true decision-aware loss: the current model training uses standard BCE-style occupancy objectives; the decision layer is post-processing.
- Exploratory deep baselines: Transformer and DLinear are lightly tuned and should not be treated as definitive deep-learning comparisons.
- Missingness assumptions: causal forward-fill avoids leakage but can propagate stale sensor values, especially for sparse WiFi coverage.
- No production monitoring: there is no deployed inference service, drift monitoring, model registry, or fallback controller.

