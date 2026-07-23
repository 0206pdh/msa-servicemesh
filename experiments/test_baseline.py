import tempfile
import unittest
from pathlib import Path

from experiments.baseline import BaselineMeasurement, block_order, formal_spec, measurement_duration


class BaselineMeasurementTests(unittest.TestCase):
    def test_duration_meets_twenty_thousand_request_floor(self):
        self.assertEqual(measurement_duration(8), 2500)
        self.assertEqual(measurement_duration(17), 1177)
        self.assertEqual(measurement_duration(22), 910)

    def test_formal_spec_uses_canonical_chain_and_request_floor(self):
        spec = formal_spec("nominal", 8)
        self.assertEqual(spec["scenario"], "SYNC_CHAIN")
        self.assertEqual(spec["workloadConfig"]["hopCount"], 3)
        self.assertEqual(spec["loadProfile"]["minimumRequests"], 20_000)
        self.assertEqual(spec["loadProfile"]["durationSeconds"], 2500)
        self.assertEqual(spec["loadProfile"]["warmupSeconds"], 180)

    def test_block_order_is_seeded_and_complete(self):
        first = block_order(1)
        self.assertEqual(first, block_order(1))
        self.assertEqual(set(first), {"nominal", "high", "near-saturation"})
        self.assertNotEqual(first, block_order(2))

    def test_next_repeat_preserves_partial_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            condition = root / "results" / "phase4-chain-baseline-nominal"
            (condition / "repeat-01").mkdir(parents=True)
            (condition / "repeat-03").mkdir()
            measurement = BaselineMeasurement(
                root, root / "results" / "phase4-chain-baseline" / "state.json", 0
            )
            self.assertEqual(measurement._next_repeat("nominal"), 4)


if __name__ == "__main__":
    unittest.main()
