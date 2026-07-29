import json
import tempfile
import unittest
from pathlib import Path

from experiments.compare_profiles import bootstrap_difference_ci, compare_conditions


def _write_condition(root: Path, name: str, p99_values: list[float]) -> Path:
    condition_dir = root / name
    for index, p99 in enumerate(p99_values, start=1):
        repeat = condition_dir / f"repeat-{index:02d}"
        repeat.mkdir(parents=True)
        summary = {
            "status": "COMPLETED",
            "sampleCount": 1000,
            "metrics": {
                "throughputRps": 10,
                "errorRate": 0,
                "latencyMs": {"p50": p99 / 2, "p95": p99 * 0.8, "p99": p99},
            },
            "resources": {"application": {"cpuCoreSeconds": 5, "memoryPeakBytes": 100,
                                           "networkRxBytes": 10, "networkTxBytes": 10}},
        }
        (repeat / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return condition_dir


class CompareProfilesTests(unittest.TestCase):
    def test_clearly_separated_groups_are_flagged_significant(self):
        low = [10.0 + index * 0.1 for index in range(12)]
        high = [40.0 + index * 0.1 for index in range(12)]
        result = bootstrap_difference_ci(low, high, seed=1)
        self.assertGreater(result["confidenceInterval95"]["low"], 0)
        self.assertTrue(result["significant"])

    def test_overlapping_groups_are_not_flagged_significant(self):
        rng_values_a = [20.0, 21.0, 19.5, 20.5, 20.2, 19.8, 20.1, 19.9, 20.3, 19.7]
        rng_values_b = [20.1, 20.9, 19.6, 20.4, 20.3, 19.9, 20.0, 20.2, 19.8, 20.05]
        result = bootstrap_difference_ci(rng_values_a, rng_values_b, seed=2)
        self.assertFalse(result["significant"])

    def test_compare_conditions_reads_two_directories_and_skips_thin_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dir_a = _write_condition(root, "profile-a", [50.0] * 12)
            dir_b = _write_condition(root, "profile-b", [55.0] * 12)
            result = compare_conditions("A", dir_a, "B", dir_b, metrics=("p99Ms",))
            self.assertIn("p99Ms", result["comparisons"])
            comparison = result["comparisons"]["p99Ms"]
            self.assertEqual(comparison["nA"], 12)
            self.assertEqual(comparison["nB"], 12)
            self.assertAlmostEqual(comparison["medianA"], 50.0)
            self.assertAlmostEqual(comparison["medianB"], 55.0)

    def test_insufficient_samples_are_skipped_not_crashed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dir_a = _write_condition(root, "profile-a", [50.0])
            dir_b = _write_condition(root, "profile-b", [55.0] * 12)
            result = compare_conditions("A", dir_a, "B", dir_b, metrics=("p99Ms",))
            self.assertEqual(result["comparisons"]["p99Ms"]["skipped"], "insufficientSamples")


if __name__ == "__main__":
    unittest.main()
