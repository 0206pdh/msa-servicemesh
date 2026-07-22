import unittest

from experiments.capacity import CapacityDiscovery, discovery_spec, evaluate


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
        self.assertEqual(result["outcome"], "CAPACITY_FAIL")
        self.assertIn("P99_EXCEEDS_2X_LOW_LOAD", result["factors"])

    def test_telemetry_failure_is_invalid_not_capacity_failure(self):
        summary = {"status": "INVALID", "loadProfileTargetRps": 27,
                   "invalidatingFactors": ["TEMPO_TRACE_MISSING"],
                   "metrics": {"latencyMs": {"p99": 12}}}
        result = evaluate(summary, 10)
        self.assertFalse(result["passed"])
        self.assertEqual(result["outcome"], "INVALID")

    def test_invalid_existing_point_is_retried(self):
        discovery = CapacityDiscovery.__new__(CapacityDiscovery)
        discovery.state = {"points": [
            {"targetRps": 27, "passed": False, "factors": ["TEMPO_TRACE_MISSING"]},
            {"targetRps": 30, "passed": False, "outcome": "CAPACITY_FAIL"},
        ]}
        self.assertIsNone(discovery._existing(27))
        self.assertEqual(discovery._existing(30)["outcome"], "CAPACITY_FAIL")

    def test_invalid_point_does_not_become_capacity_boundary(self):
        discovery = CapacityDiscovery.__new__(CapacityDiscovery)
        discovery.start_rps = 10
        discovery.factor = 2
        discovery.max_rps = 40
        discovery.refinement_steps = 4
        discovery.cooldown_seconds = 0
        discovery.state = {"points": [], "status": "GEOMETRIC_SEARCH"}
        discovery._write = lambda: None
        points = {
            10: {"passed": True, "outcome": "PASS"},
            20: {"passed": True, "outcome": "PASS"},
            40: {"passed": False, "outcome": "CAPACITY_FAIL"},
            30: {"passed": False, "outcome": "INVALID"},
        }
        discovery.run_point = lambda rps, phase: points[rps]
        result = discovery.execute()
        self.assertEqual(result["status"], "INVALID_POINT")
        self.assertEqual(result["invalidPointRps"], 30)
        self.assertNotIn("usableCapacityRps", result)


if __name__ == "__main__":
    unittest.main()
