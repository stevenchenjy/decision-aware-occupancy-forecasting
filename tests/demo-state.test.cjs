const { test } = require('node:test');
const assert = require('node:assert/strict');
const { read, query } = require('../docs/demo/state.js');
const { evaluate } = require('../docs/demo/policy.js');
const payload = require('../docs/demo/data.json');

test('shared exploratory settings and example date survive a URL round trip', () => {
  const shared = { model: 'lightgbm', threshold: .925, minSteps: 16 };
  const day = payload.days[0];
  const restored = read('?' + query(shared, day), payload);
  assert.deepEqual(restored, { ...shared, dayIndex: 0 });
  assert.deepEqual(evaluate(payload.days, restored.model, restored.threshold, restored.minSteps), evaluate(payload.days, shared.model, shared.threshold, shared.minSteps));
});

test('empty, invalid and out-of-grid settings use the model reported policy', () => {
  for (const threshold of ['', 'NaN', 'Infinity', '.999', '.876', '-1']) {
    const state = read('?model=historical&threshold=' + threshold + '&hours=3&day=invalid', payload);
    assert.deepEqual(state, { model: 'historical', threshold: .95, minSteps: 4, dayIndex: payload.defaultExampleIndex });
  }
  assert.equal(read('?model=unknown', payload).model, 'hybrid');
  assert.equal(read('', payload).threshold, .875);
});

test('serialization includes only the published controls, without unrelated query parameters', () => {
  const state = read('?model=hybrid&threshold=.875&hours=1&tracking=remove', payload);
  const params = new URLSearchParams(query(state, payload.days[state.dayIndex]));
  assert.deepEqual([...params.keys()], ['model', 'threshold', 'hours', 'day']);
  assert.equal(params.get('tracking'), null);
});
