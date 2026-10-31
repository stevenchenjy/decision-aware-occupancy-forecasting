/* Offline, client-side accounting. No third-party scripts or data uploads. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const policy = window.OccupancyPolicy;
  let data;
  const number = n => n.toLocaleString('en-US');
  const oneDecimal = n => n.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  function settings() { return { model: $('model').value, threshold: Number($('threshold').value), minSteps: Number($('duration').value) }; }
  function isReported(s) { return s.minSteps === 4 && Math.abs(s.threshold - data.models.find(m => m.id === s.model).reportedThreshold) < 1e-9; }
  function render() {
    const s = settings();
    const result = policy.evaluate(data.days, s.model, s.threshold, s.minSteps);
    const model = data.models.find(m => m.id === s.model);
    $('threshold-value').value = s.threshold.toFixed(3);
    $('threshold').setAttribute('aria-valuetext', s.threshold.toFixed(3) + ', uncalibrated Empty score');
    $('windows').textContent = number(result.recommendedWindows);
    $('intervals').textContent = number(result.recommendedIntervals) + ' recommended 15-minute intervals';
    $('conflicts').textContent = number(result.conflictIntervals);
    $('conflict-rate').textContent = result.recommendedIntervals ? (result.conflictRate * 100).toFixed(2) + '% of recommended intervals later labeled occupied' : 'No recommendations at these settings';
    $('opportunity').textContent = oneDecimal(result.opportunityKwh);
    $('policy-status').classList.toggle('exploratory', !isReported(s));
    $('policy-status').textContent = isReported(s)
      ? 'Reported policy: ' + model.label + ', validation-selected threshold ' + s.threshold.toFixed(3) + ', minimum window 1 hour. Evaluated on saved test outputs.'
      : 'Exploratory replay of an already inspected test period. These settings are not a newly validated policy or confirmed improvement.';
    renderDay(s);
    const address = new URL(location.href);
    address.search = window.OccupancyState.query(s, data.days[Number($('day').value)]);
    history.replaceState(null, '', address);
    $('share-link').value = address.href;
    $('share-status').textContent = 'The link preserves the model, threshold, duration, and example date.';
  }
  function renderDay(s) {
    const day = data.days[Number($('day').value)];
    const scores = day.scores[s.model];
    const mask = policy.stableMask(scores, s.threshold, s.minSteps);
    const x = i => 104 + i * 6.5;
    const y = score => 166 - score * 130;
    const grid = [0, 0.5, 1].map(value => '<line x1="104" y1="' + y(value) + '" x2="728" y2="' + y(value) + '" stroke="#e3eae7"/><text x="91" y="' + (y(value) + 4) + '" text-anchor="end">' + value.toFixed(1) + '</text>').join('');
    const points = scores.map((v, i) => x(i + .5) + ',' + y(v)).join(' ');
    let rows = '';
    const bands = day.empty.map((label, i) => {
      const occupied = !label;
      const rec = mask[i];
      const time = day.targetTimes[i];
      const state = rec ? (occupied ? 'Conflict: recommended while camera-labeled occupied' : 'Recommended') : 'Not recommended';
      rows += '<tr><td>' + time.slice(5, 16) + '</td><td>' + scores[i].toFixed(3) + '</td><td>' + (label ? 'Empty' : 'Occupied') + '</td><td>' + state + '</td><td>' + day.loadKwh[i].toFixed(3) + '</td></tr>';
      return (label ? '<rect x="' + x(i) + '" y="190" width="6.6" height="17" fill="#dce6e3"/>' : '') + (rec ? '<rect x="' + x(i) + '" y="218" width="6.6" height="17" fill="' + (occupied ? '#b45d31' : '#13685e') + '"/>' : '');
    }).join('');
    const title = 'Example horizon anchored ' + day.anchor.slice(0, 10) + '. Empty scores, threshold, camera-empty labels, and current recommendations. Read the adjacent table for individual values.';
    $('timeline').innerHTML = '<svg viewBox="0 0 764 281" role="img" aria-labelledby="plot-title plot-desc"><title id="plot-title">' + title + '</title><desc id="plot-desc">Scores range from zero to one. Each band interval is 15 minutes. Recorded camera-empty labels are gray-green; recommendations are teal and conflicts are rust.</desc><g font-family="Arial,sans-serif" font-size="11" fill="#53676b"><text x="15" y="47">Empty score</text>' + grid + '<line x1="104" y1="' + y(s.threshold) + '" x2="728" y2="' + y(s.threshold) + '" stroke="#667b8b" stroke-dasharray="5 4"/><polyline points="' + points + '" fill="none" stroke="#13685e" stroke-width="1.8"/><text x="13" y="203">Camera empty</text><text x="13" y="231">Recommended</text>' + bands + '<text x="104" y="260">00:15</text><text x="252" y="260">06:15</text><text x="408" y="260">12:15</text><text x="564" y="260">18:15</text><text x="728" y="260" text-anchor="end">Next 00:15</text></g></svg>';
    $('day-table').innerHTML = rows;
  }
  function download() {
    const s = settings();
    const rows = [['model', 'threshold', 'minimum_window_hours', 'analysis_status', 'anchor_time', 'target_time', 'empty_score', 'camera_empty_label', 'recommended', 'camera_label_conflict', 'processed_load_proxy_kwh', 'recommended_camera_empty_load_proxy_kwh']];
    for (const day of data.days) {
      const mask = policy.stableMask(day.scores[s.model], s.threshold, s.minSteps);
      mask.forEach((on, i) => rows.push([s.model, s.threshold, s.minSteps / 4, isReported(s) ? 'reported_fixed_policy' : 'exploratory_replay', day.anchor, day.targetTimes[i], day.scores[s.model][i], day.empty[i], Number(on), Number(on && !day.empty[i]), day.loadKwh[i], on && day.empty[i] ? day.loadKwh[i] : 0]));
    }
    const csv = rows.map(row => row.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',')).join('\r\n') + '\r\n';
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'occupancy-' + s.model + '-' + s.threshold.toFixed(3) + '-' + s.minSteps / 4 + 'h.csv'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function load() {
    $('load-error').hidden = true;
    $('policy-status').textContent = 'Loading the saved records…';
    try {
      const response = await fetch('./data.json');
      if (!response.ok) throw new Error('Data unavailable');
      data = await response.json();
      if (data.schemaVersion !== 1 || data.days.length !== 43 || data.models.length !== 3) throw new Error('Unexpected data format');
      $('day').replaceChildren(...data.days.map((day, i) => { const option = document.createElement('option'); option.value = i; option.textContent = day.anchor.slice(0, 10); return option; }));
      const initial = window.OccupancyState.read(location.search, data);
      $('model').value = initial.model;
      $('threshold').value = String(initial.threshold);
      $('duration').value = String(initial.minSteps);
      $('day').value = String(initial.dayIndex);
      $('provenance').replaceChildren(...data.sources.map(source => { const item = document.createElement('li'); item.textContent = source.path + ' · SHA-256: ' + source.sha256; return item; }));
      ['controls', 'reset', 'day', 'download', 'copy-link'].forEach(id => { $(id).disabled = false; });
      render();
    } catch (error) {
      $('load-error').hidden = false;
      $('policy-status').textContent = 'Interactive data unavailable. The fixed reported-policy table below remains readable.';
      $('timeline').textContent = 'Open the notebook or reload the data to explore an example.';
    }
  }
  $('model').addEventListener('change', () => { $('threshold').value = data.models.find(m => m.id === $('model').value).reportedThreshold; $('duration').value = '4'; render(); });
  $('threshold').addEventListener('input', render);
  $('duration').addEventListener('change', render);
  $('day').addEventListener('change', render);
  $('reset').addEventListener('click', () => { $('threshold').value = data.models.find(m => m.id === $('model').value).reportedThreshold; $('duration').value = '4'; render(); });
  $('download').addEventListener('click', download);
  $('copy-link').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($('share-link').value);
      $('share-status').textContent = 'Link copied. Anyone opening it can inspect the same replay settings.';
    } catch (error) {
      $('share-link').focus();
      $('share-link').select();
      $('share-status').textContent = 'Select and copy the replay address above.';
    }
  });
  $('retry').addEventListener('click', load);
  load();
})();
