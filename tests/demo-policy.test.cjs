const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { stableMask, evaluate } = require('../docs/demo/policy.js');
const payload = JSON.parse(fs.readFileSync(path.join(__dirname, '../docs/demo/data.json'), 'utf8'));

test('browser accounting agrees with Python on every exported threshold/model/duration setting', () => {
  assert.equal(payload.referenceGrid.length, 333);
  for (const expected of payload.referenceGrid) {
    const actual = evaluate(payload.days, expected.model, expected.threshold, expected.minSteps);
    for (const key of ['recommendedIntervals', 'recommendedWindows', 'conflictIntervals']) assert.equal(actual[key], expected[key], JSON.stringify(expected));
    assert.ok(Math.abs(actual.opportunityKwh - expected.opportunityKwh) < 1e-7);
    assert.ok(Math.abs(actual.conflictRate - expected.conflictRate) < 1e-12);
  }
});

test('runs at the threshold count, short runs do not, and an occupied recommendation is a conflict', () => {
  assert.deepEqual(stableMask([.875, .875, .875, .875, .1, .9, .9, .9], .875, 4), [true, true, true, true, false, false, false, false]);
  const day = { empty: [1, 0, 1, 1], loadKwh: [2, 100, 3, 4], scores: { hybrid: [.9, .9, .9, .9] } };
  const result = evaluate([day], 'hybrid', .875, 4);
  assert.equal(result.conflictIntervals, 1);
  assert.equal(result.opportunityKwh, 9);
});

test('daily horizons never join into a longer recommended run', () => {
  const day = { empty: [1, 1], loadKwh: [2, 2], scores: { hybrid: [.9, .9] } };
  assert.equal(evaluate([day, day], 'hybrid', .875, 4).recommendedIntervals, 0);
});

test('no recommendation and invalid settings are handled', () => {
  assert.equal(evaluate([], 'hybrid', .875, 4).conflictRate, 0);
  assert.throws(() => stableMask([.9], NaN, 4));
  assert.throws(() => stableMask([.9], .875, 0));
});
