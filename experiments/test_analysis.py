import json
import tempfile
import unittest
from pathlib import Path

from experiments.analysis import analyze


class AnalysisTests(unittest.TestCase):
    def test_requires_at_least_ten_valid_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(1, 10):
                repeat = root / f"repeat-{index:02d}"
                repeat.mkdir()
                summary = {"status": "COMPLETED", "sampleCount": 1000,
                           "metrics": {"throughputRps": 100, "errorRate": 0,
                                       "latencyMs": {"p50": 10, "p95": 20, "p99": 30}},
                           "resources": {"application": {"cpuCoreSeconds": 10,
                                                          "memoryPeakBytes": 100,
                                                          "networkRxBytes": 100,
                                                          "networkTxBytes": 100}}}
                (repeat / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            self.assertEqual(analyze(root)["decision"], "CONTINUE")

    def test_stops_when_ten_stable_runs_reach_precision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(1, 11):
                repeat = root / f"repeat-{index:02d}"
                repeat.mkdir()
                summary = {"status": "COMPLETED", "sampleCount": 1000,
                           "metrics": {"throughputRps": 100, "errorRate": 0,
                                       "latencyMs": {"p50": 10, "p95": 20, "p99": 30}},
                           "resources": {"application": {"cpuCoreSeconds": 10,
                                                          "memoryPeakBytes": 100,
                                                          "networkRxBytes": 100,
                                                          "networkTxBytes": 100}}}
                (repeat / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            self.assertEqual(analyze(root)["decision"], "STOP_PRECISION_REACHED")


if __name__ == "__main__":
    unittest.main()
