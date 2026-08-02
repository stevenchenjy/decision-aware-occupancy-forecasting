# Research-Question Candidates

> **Superseded workspace note.** The manuscript has selected its current
> post-bin offline case-study framing. These historical candidates must not
> override the final claim matrix or imply prospective availability, calibrated
> probabilities, verified controllability, or a frozen exploratory candidate
> after empirical retraining.

The original request specifies an IEEE paper but not yet a single research
question or venue. The workspace therefore keeps these candidates distinct from
the manuscript until the authors select one.

## Recommended candidate — evaluation-focused

**RQ:** *For one office-building dataset, how do validation-selected occupancy
forecast models trade off Empty-class forecast quality, empirical
camera-label-conflict rate, and offline camera-label-empty processed load-proxy
overlap when recommendations require stable
empty windows?*

Why this is safest:

- it matches the frozen evidence already in the repository;
- it does not require claiming that the hybrid is decisively superior;
- it naturally motivates a strong schedule baseline and uncertainty analysis;
- it supports an honest “case study/evaluation framework” contribution.

Proposed sub-questions:

1. How does the validation-selected hybrid compare with schedule, tabular, and
   sequence baselines on held-out Empty-class forecasting metrics?
2. How do validation-selected operating thresholds change offline load-proxy overlap,
   coverage, conflict, and stable-window outcomes?
3. How robust are the key pairwise differences to daily-block uncertainty, and
   which limitations prevent operational deployment claims?

## Candidate B — narrower hybrid question

**RQ:** *Can a validation-selected convex blend of schedule, LightGBM, and
Transformer probabilities improve the held-out risk--opportunity operating point
over its individual components in Building 59?*

This is feasible, but it is risky as a headline because confidence intervals for
some pairwise advantages include zero. Use it only if the abstract explicitly
states that the result is an uncertain point-estimate comparison.

## Candidate C — future work, not the current headline

**RQ:** *Can a validation-only joint weight--threshold search improve offline
safe opportunity while preserving prespecified forecast- and window-safety
constraints on a genuinely untouched chronological period?*

The repository contains a frozen challenger and protocol, but no new untouched
period. This is an excellent next experiment, not a completed paper result.

## Author decisions needed before drafting

1. Is the target a conference-length paper, a journal article, or a course/
   internal IEEE-style manuscript?
2. Do you want the paper to foreground the evaluation protocol (recommended) or
   the probability hybrid itself?
3. Can the project obtain a new chronological period or another building before
   submission? This changes the appropriate venue and strength of the claims.
