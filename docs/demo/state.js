/* Only published demo controls are serialized. There is no visitor tracking. */
(function (root) {
  'use strict';
  function read(search, data) {
    const params = new URLSearchParams(search);
    const model = data.models.find(item => item.id === params.get('model')) || data.models[0];
    const rawThreshold = params.get('threshold');
    const threshold = rawThreshold === null || rawThreshold.trim() === '' ? NaN : Number(rawThreshold);
    const validThreshold = Number.isFinite(threshold) && threshold >= .05 && threshold <= .95 && Math.abs(threshold * 40 - Math.round(threshold * 40)) < 1e-9;
    const hours = Number(params.get('hours'));
    const index = data.days.findIndex(day => day.anchor.slice(0, 10) === params.get('day'));
    return {
      model: model.id,
      threshold: validThreshold ? threshold : model.reportedThreshold,
      minSteps: [1, 2, 4].includes(hours) ? hours * 4 : 4,
      dayIndex: index >= 0 ? index : data.defaultExampleIndex
    };
  }
  function query(settings, day) {
    return new URLSearchParams({model: settings.model, threshold: settings.threshold.toFixed(3), hours: String(settings.minSteps / 4), day: day.anchor.slice(0, 10)}).toString();
  }
  const api = { read, query };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.OccupancyState = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
