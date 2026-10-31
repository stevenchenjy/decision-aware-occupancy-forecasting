import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from replay import ROOT, compare, load_records, receipt, verify_kit


class OfflineReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.digest = load_records(ROOT / "docs/demo/data.json")

    def test_reported_rows_match_and_exploration_stays_distinct(self):
        rows = compare(self.data)
        self.assertEqual([(r["recommendedWindows"], r["recommendedIntervals"], r["conflictIntervals"]) for r in rows], [(14, 259, 0), (12, 66, 0), (19, 265, 11)])
        self.assertTrue(all(r["reconciled_with_reported_metrics"] for r in rows))
        row = compare(self.data, "hybrid", .85, 2)[0]
        self.assertEqual(row["analysis_status"], "exploratory_replay")
        self.assertFalse(row["reconciled_with_reported_metrics"])

    def test_invalid_settings_and_corrupt_reported_reference_are_rejected(self):
        for settings in [("all", .9, 1), ("unknown", None, 1), ("hybrid", float("nan"), 1), ("hybrid", None, 3)]:
            with self.assertRaises(ValueError): compare(self.data, *settings)
        broken = copy.deepcopy(self.data)
        broken["models"][0]["reportedMetrics"]["recommendedWindows"] = 15
        with self.assertRaisesRegex(ValueError, "does not reconcile"): compare(broken)

    def test_receipt_contains_observations_without_identity_or_success_claim(self):
        record = receipt(self.data, self.digest, compare(self.data), {"software_version": "working-tree"})
        self.assertEqual(set(record["environment"]), {"python", "implementation", "os"})
        self.assertEqual(record["scope"]["unique_target_intervals"], 4128)
        self.assertEqual(record["data_sha256"], self.digest)
        self.assertNotIn("independent_reproduction", record)
        self.assertNotIn("user", record)

    def test_kit_integrity_detects_changed_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "input.txt").write_bytes(b"original")
            manifest = {"release_tag": "test", "source_commit": "fixture", "files": {"input.txt": hashlib.sha256(b"original").hexdigest()}}
            (root / "kit-manifest.json").write_text(json.dumps(manifest))
            self.assertTrue(verify_kit(root)["kit_integrity_checked"])
            (root / "input.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash does not match"): verify_kit(root)

    def test_overlapping_target_records_are_rejected(self):
        broken = copy.deepcopy(self.data)
        broken["days"][1]["targetTimes"] = broken["days"][0]["targetTimes"]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            path.write_text(json.dumps(broken))
            with self.assertRaisesRegex(ValueError, "must not overlap"): load_records(path)


if __name__ == "__main__":
    unittest.main()
