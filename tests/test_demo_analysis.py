import json
import math
import unittest
from pathlib import Path

from src.demo_analysis import build_payload, evaluate, payload_text, stable_mask

ROOT = Path(__file__).resolve().parents[1]


class DemoAnalysisTests(unittest.TestCase):
    def test_demo_is_current_and_reconciles_with_canonical_inputs(self):
        payload = build_payload()
        self.assertEqual((ROOT / "docs/demo/data.json").read_text(), payload_text(payload))
        metrics = evaluate(payload["days"])
        self.assertEqual((metrics["recommendedIntervals"], metrics["recommendedWindows"], metrics["conflictIntervals"]), (259, 14, 0))
        self.assertTrue(math.isclose(metrics["opportunityKwh"], 490.1463795265, abs_tol=1e-7))
        self.assertEqual(len({t for d in payload["days"] for t in d["targetTimes"]}), 4128)

    def test_runs_do_not_join_across_horizon_boundaries(self):
        days = [{"empty": [1, 1], "loadKwh": [2, 2], "scores": {"hybrid": [0.9, 0.9]}}] * 2
        self.assertEqual(evaluate(days, min_steps=4)["recommendedIntervals"], 0)

    def test_equality_and_boundary_runs_and_conflict_accounting(self):
        self.assertEqual(stable_mask([0.875] * 4 + [0.1] + [0.9] * 3, 0.875, 4), [True] * 4 + [False] * 4)
        day = {"empty": [1, 0, 1, 1], "loadKwh": [2, 100, 3, 4], "scores": {"hybrid": [0.9] * 4}}
        result = evaluate([day])
        self.assertEqual(result["conflictIntervals"], 1)
        self.assertEqual(result["opportunityKwh"], 9)
        self.assertEqual(result["conflictRate"], 0.25)

    def test_empty_recommendation_set_has_no_division_error(self):
        self.assertEqual(evaluate([])["conflictRate"], 0)
        self.assertEqual(stable_mask([], 0.875, 4), [])

    def test_invalid_settings_are_rejected(self):
        for threshold in [float("nan"), -0.1, 1.1]:
            with self.assertRaises(ValueError):
                stable_mask([0.9], threshold, 4)
        with self.assertRaises(ValueError):
            stable_mask([0.9], 0.875, 0)


if __name__ == "__main__":
    unittest.main()
