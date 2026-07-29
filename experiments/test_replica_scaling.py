import unittest

from experiments.replica_scaling import FIXED_SYNC_CHAIN_TARGETS, NOMINAL_RPS, scaling_spec


class ReplicaScalingSpecTests(unittest.TestCase):
    def test_scaling_spec_uses_nominal_load_and_shorter_window(self):
        spec = scaling_spec("SIDECAR", 2, 1)
        self.assertEqual(spec["profile"], "SIDECAR")
        self.assertEqual(spec["loadProfile"]["targetRps"], NOMINAL_RPS)
        self.assertEqual(spec["loadProfile"]["warmupSeconds"], 60)
        self.assertEqual(spec["loadProfile"]["durationSeconds"], 180)

    def test_scaling_spec_scrape_target_count_tracks_replicas(self):
        spec = scaling_spec("AMBIENT", 4, 1)
        self.assertEqual(
            spec["kubernetes"]["expectedScrapeTargets"], FIXED_SYNC_CHAIN_TARGETS + 4
        )

    def test_scaling_spec_run_id_encodes_profile_and_replicas(self):
        spec = scaling_spec("SIDECAR", 1, 1)
        self.assertEqual(spec["runId"], "phase8-replica-scaling-sidecar-r1")


if __name__ == "__main__":
    unittest.main()
