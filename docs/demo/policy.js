/* The browser replay has no third-party dependencies, training, or telemetry. */
(function (root) {
  'use strict';
  function stableMask(scores, threshold, minSteps) {
    if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1 || !Number.isInteger(minSteps) || minSteps < 1) throw new Error('Invalid policy settings');
    const mask = scores.map(() => false);
    let start = null;
    for (let i = 0; i <= scores.length; i++) {
      const high = i < scores.length && scores[i] >= threshold;
      if (high && start === null) start = i;
      if (!high && start !== null) {
        if (i - start >= minSteps) mask.fill(true, start, i);
        start = null;
      }
    }
    return mask;
  }
  function evaluate(days, model, threshold, minSteps) {
    const result = { recommendedIntervals: 0, conflictIntervals: 0, recommendedWindows: 0, opportunityKwh: 0, conflictRate: 0 };
    for (const day of days) {
      const mask = stableMask(day.scores[model], threshold, minSteps);
      mask.forEach((on, i) => {
        if (!on) return;
        result.recommendedIntervals++;
        if (i === 0 || !mask[i - 1]) result.recommendedWindows++;
        if (day.empty[i]) result.opportunityKwh += day.loadKwh[i];
        else result.conflictIntervals++;
      });
    }
    result.conflictRate = result.recommendedIntervals ? result.conflictIntervals / result.recommendedIntervals : 0;
    return result;
  }
  const api = { stableMask, evaluate };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.OccupancyPolicy = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
