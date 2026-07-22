import unittest

from experiments.capacity import discovery_spec, evaluate


class CapacityTests(unittest.TestCase):
    def test_discovery_uses_canonical_chain(self):
        spec = discovery_spec("run", 40)
        self.assertEqual(spec["scenario"], "SYNC_CHAIN")
        self.assertEqual(spec["workloadConfig"]["hopCount"], 3)
        self.assertEqual(spec["loadProfile"]["targetRps"], 40)

    def test_p99_over_twice_low_load_fails(self):
        summary = {"status": "COMPLETED", "loadProfileTargetRps": 40,
                   "invalidatingFactors": [], "metrics": {"latencyMs": {"p99": 21}}}
        result = evaluate(summary, 10)
        self.assertFalse(result["passed"])
        self.assertIn("P99_EXCEEDS_2X_LOW_LOAD", result["factors"])


if __name__ == "__main__":
    unittest.main()
