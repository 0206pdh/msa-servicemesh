import unittest

from experiments.resilience import pod_kill_spec, recovery_seconds


class ResilienceTests(unittest.TestCase):
    def test_pod_kill_spec_uses_high_error_tolerance_and_ambient_profile(self):
        spec = pod_kill_spec()
        self.assertEqual(spec["profile"], "AMBIENT")
        self.assertEqual(spec["loadProfile"]["maximumErrorRate"], 1.0)
        self.assertEqual(spec["loadProfile"]["durationSeconds"], 300)

    def test_recovery_seconds_finds_first_sustained_drop_after_kill(self):
        values = [
            [100.0, 0.0], [105.0, 0.01],
            [110.0, 0.9], [115.0, 0.8], [120.0, 0.3],
            [125.0, 0.01], [130.0, 0.0], [135.0, 0.0], [140.0, 0.0],
        ]
        result = recovery_seconds(values, killed_at_epoch=110.0, sustained_seconds=15)
        self.assertEqual(result, 15.0)

    def test_recovery_seconds_returns_none_when_never_recovers(self):
        values = [[100.0, 0.9], [105.0, 0.8], [110.0, 0.7]]
        result = recovery_seconds(values, killed_at_epoch=100.0)
        self.assertIsNone(result)

    def test_recovery_seconds_ignores_points_before_the_kill(self):
        values = [[90.0, 0.9], [95.0, 0.0], [100.0, 0.0], [105.0, 0.0], [110.0, 0.0]]
        result = recovery_seconds(values, killed_at_epoch=100.0, sustained_seconds=10)
        self.assertEqual(result, 0.0)


if __name__ == "__main__":
    unittest.main()
