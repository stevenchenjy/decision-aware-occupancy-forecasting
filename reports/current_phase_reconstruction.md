# Current Phase Reconstruction

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Verification Status: VERIFIED for repository state, tests, and saved-output tabular reproduction; ANALYZED for scientific-stage classification
- Reconstruction Date: 2026-07-17
- Evidence Cutoff: commit `0c813fdaa31ecc8af9b8c9e67c5de04226b362ee`

## 1. Current repository state

At the start of this reconstruction, `main` was clean and one commit ahead of `origin/main`. The current commit is `0c813fd` (`Hybrid Addition`, 2026-07-15). It adds 24 files and modifies no pre-existing file. Consequently, the canonical headline documents, tables, and figures are byte-identical to their versions in the parent commit.

The latest commit contains both the decision-aware joint search and a later window-aware search. It is not limited to the last milestone described in the recovery request.

All files named in the recovery request exist and are tracked:

| Artifact | Git state | Role | SHA-256 |
|---|---|---|---|
| `reports/decision_aware_joint_search_audit.md` | tracked | saved-input and split audit | `e01cc1a6006d776bb046ee4973cadffa8fc244863bad30e3b2776690e9f8f038` |
| `reports/decision_aware_joint_search_report.md` | tracked | scientific interpretation | `ad29e3d16520526a44e6e7aa2cba3c99fe705f6655bce3235b657f6964be632b` |
| `results/decision_aware_joint_weight_threshold_grid.csv` | tracked | 8,547 validation pairs | `086e22869f4b1408b7ff2fee835f51d5cd03a51afd230c92136485e5c3736ef5` |
| `results/decision_aware_joint_selected_candidates.csv` | tracked | frozen candidates and fixed test evaluation | `14829546094b06e2a22be365280617d1d847fd93bf1d351e6fee3ff69094a77e` |
| `results/decision_aware_joint_auprc_floor_sensitivity.csv` | tracked | validation-only floor sensitivity | `ca358b12ea6d4d64d290b02bd88caa3fe01f7be55ff4c9a7457fcc8decb7ddbb` |
| `figures/decision_aware_joint_validation_frontier.png` | tracked | validation frontier | `6b2d3828a3123a69e8ee906b727115b34d49a09ccf06dd89b49d0ace97434f99` |
| `figures/decision_aware_joint_test_comparison.png` | tracked | fixed-candidate test comparison | `7337fda8071820e5c458deabea49ccf407b2045ba534db987e6e820b1465a110` |
| `figures/forecast_optimal_vs_decision_optimal.png` | tracked | validation-selected strategy comparison | `39654feb89946f29b97778ed18fc8b5b51f3fb249830a1cb9aac4d8b14148e78` |
| `src/decision_aware_joint_search.py` | tracked | implementation | n/a |
| `scripts/run_decision_aware_joint_search.py` | tracked | command-line runner | n/a |
| `tests/test_decision_aware_joint_search.py` | tracked | leakage, constraint, and determinism tests | n/a |

The requested joint-search numbers match the tracked tables: 231 legal weight vectors multiplied by 37 thresholds equals 8,547 validation pairs. The reported canonical, decision-optimal, and 99%-floor weights, thresholds, test Empty AUPRC values, interval conflict rates, and safe-opportunity values all reproduce exactly before rounding.

The best-fit recovery classification at inspection time is **State B: joint search complete, presentation integration incomplete**. The scientific work is actually beyond the joint-search milestone, but presentation integration was incomplete because `reports/professor_presentation_guide.md` had been deleted in commit `31bcacd` while `README.md`, `reports/current_result_consistency_audit.md`, and `reports/no_raw_data_upgrade_report.md` still referred to it. The root headline documents also contain no decision-aware or window-aware comparison. This reconstruction restores the guide without changing headline claims.

## 2. Last fully completed phase

The last fully completed scientific phase is the **window-aware validation search and candidate freeze**, not merely the initial decision-aware joint search.

Evidence added in `0c813fd` includes:

- `src/window_aware_decision_search.py` and its runner;
- `tests/test_window_aware_decision_search.py`;
- `results/window_aware_joint_selection_grid.csv`, containing 8,547 pairs crossed with 20 constraint combinations, or 170,940 data rows;
- `results/window_aware_selected_candidates.csv`;
- `results/window_conflict_severity_metrics.csv`;
- `results/window_aware_current_test_diagnostic.csv`, explicitly labeled retrospective and not fresh;
- three window-focused figures;
- `reports/window_aware_decision_search_audit.md` and `reports/window_aware_decision_search_report.md`;
- `reports/future_untouched_evaluation_protocol.md`.

The window-aware phase selected on validation only. Its frozen primary future challenger is Seasonal/LightGBM/Transformer `0.40/0.40/0.20` at threshold `0.850`, under the `W_min=85%`, `Q=99%` rule. Its current-test values are explicitly retrospective diagnostics and cannot support promotion.

Therefore, a prompt after the original joint-search implementation was executed. The repository implemented the requested window-aware objective, froze candidates, generated presentation figures, analyzed conflict-window severity, and wrote a future untouched-evaluation protocol. There is no later commit after this combined commit.

## 3. Work that appears partially completed

- **Professor-facing integration:** dedicated decision-aware and window-aware reports/figures exist, but the previously canonical professor guide was deleted and not replaced. The active `README.md` link was broken. This reconstruction repairs that documentation gap.
- **Remote publication:** the complete latest commit is local only; `main` is one commit ahead of `origin/main`.
- **Rendering reproducibility:** two fresh runs under Python 3.13.2, Matplotlib 3.10.9, and Pillow 12.2.0 produced identical PNG hashes to one another, but not to the three committed decision-aware PNG hashes. Dimensions were equal for two figures and differed by one pixel in height for the third. The CSVs and Markdown reports were byte-identical. This is an environment-sensitive presentation-rendering gap, not metric drift.
- **Future evaluation:** the protocol and candidate freeze are complete, but no genuinely new evaluation block has been acquired or evaluated.

## 4. Work that was proposed but never implemented

- One-shot evaluation on a genuinely untouched chronological period.
- Nested temporal validation of the complete hybrid. The existing validation and test dates are already inspected and cannot be relabeled untouched.
- Hybrid rolling-origin validation. `results/rolling_origin_cv.csv` contains aggregate metrics for Historical Average, LightGBM, and Random Forest, but no aligned fold-level probabilities for the full Seasonal/LightGBM/Transformer hybrid.
- Hybrid-specific per-seed analysis. The seed files contain aggregate model metrics, not aligned per-seed component probabilities.
- Full base-model retraining and raw feature-pipeline revalidation.
- External-building or external-season validation.
- Causal, counterfactual, comfort, or measured-energy-savings evaluation.

## 5. Canonical current model

The canonical model remains the validation-selected primary hybrid:

- Weights, Seasonal/LightGBM/Transformer: `0.15/0.60/0.25`.
- Empty-probability threshold: `0.875`.
- Selection: maximum validation Empty AUPRC on the 0.05 convex simplex, followed by the validation-only 10% conflict policy.
- Current test Empty AUPRC: `0.8514`.
- Current test interval conflict: `0/259 = 0.00%` observed.
- Current test safe opportunity: `490.1 kWh` of recorded load-proxy opportunity.
- Current test windows: `14/14` fully safe in this observed period.

The latest commit did not change `README.md`, the main result summaries, `results/canonical_model_comparison.csv`, `results/canonical_policy_10pct.csv`, `results/canonical_uncertainty_summary.csv`, or the canonical comparison figures. Zero observed conflict is not zero future risk, and safe opportunity is not measured savings.

## 6. Exploratory current models

The repository now freezes three principal challengers, all exploratory:

| Candidate | Weights S/L/T | Threshold | Selection evidence | Current-test role |
|---|---|---:|---|---|
| Decision-optimal 10% | `0.65/0.05/0.30` | 0.775 | validation safe opportunity under interval conflict `<=10%` | fixed-candidate descriptive evaluation: AUPRC 0.8604, conflict 2.98%, opportunity 623.5 kWh |
| Decision-optimal 99%-AUPRC floor | `0.35/0.35/0.30` | 0.800 | same objective plus validation AUPRC `>=99%` of best | fixed-candidate descriptive evaluation: AUPRC 0.8569, conflict 3.09%, opportunity 650.4 kWh |
| Window-aware primary future challenger | `0.40/0.40/0.20` | 0.850 | validation interval conflict `<=10%`, fully safe windows `>=85%`, AUPRC `>=99%` of best | retrospective diagnostic only: AUPRC 0.8610, conflict 2.49%, 15/16 fully safe windows, opportunity 511.6 kWh |

None is canonical. No current-test result may be used to alter these candidates or choose among them.

## 7. Tests and reproduction status

- `python3 -m pytest -q tests/test_decision_aware_joint_search.py`: **7 passed**.
- `python3 -m pytest -q`: **35 passed**. The historical 27-test count is consistent with the 20 earlier tests plus the 7 joint-search tests; the 8 later window-aware tests bring the current total to 35.
- The saved-output joint-search runner completed in a temporary detached worktree without accessing Dryad data or retraining.
- The two reports and three CSV outputs were byte-identical to the committed artifacts. Candidate values and all 8,547 grid rows therefore reproduce exactly.
- Two same-environment figure reruns were byte-identical to each other. Their hashes differed from the committed PNGs, consistent with renderer-version sensitivity; no committed file was overwritten.
- Selection leakage controls pass in code and tests: validation selection functions accept no test frame, reject columns containing test metrics in the window-aware path, mark `test_used_for_selection=False`, and load/evaluate the current test only after candidates are fixed.
- The main working tree remained unchanged by verification. No Dryad path was read and no base model was trained.

## 8. Exact remaining scientific and technical gaps

1. **No fresh evaluation unit:** all current validation and test dates have already informed analysis or diagnostics.
2. **No additional saved temporal block:** the committed prediction exports cover only the inspected validation and test periods.
3. **No fold-level full-hybrid probabilities:** aggregate rolling-origin metrics cannot support nested selection/evaluation of the complete hybrid.
4. **No aligned per-seed hybrid probabilities:** seed-level hybrid dispersion cannot be reconstructed from aggregate metrics.
5. **No serialized fitted base models:** the repository contains no model checkpoint capable of producing probabilities for a new period without reconstructing/retraining the training pipeline.
6. **Raw-data dependency:** full retraining and new prediction generation are blocked by absent raw data, unless a collaborator supplies a new, locked saved-output bundle containing aligned component probabilities, labels, and loads.
7. **Limited effective safety sample:** observed windows are clustered within days; zero current conflict is finite-sample evidence only.
8. **No causal savings evidence:** safe opportunity is coincidence with recorded controllable-load proxy, not measured or counterfactual savings.
9. **Renderer not pinned:** scientific tables reproduce exactly, but committed PNG bytes do not reproduce under the current plotting stack.
10. **Local-only latest commit:** the scientific additions in `0c813fd` are not on `origin/main`.
