import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from experiments.runner.cli import Runner, validate_spec
from experiments.runner.kubernetes import KubernetesAdapter


class RunnerTests(unittest.TestCase):
    def test_validation_rejects_unbounded_load(self):
        with self.assertRaises(ValueError):
            validate_spec({})

    def test_three_repetitions_have_same_artifact_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "experiments" / "k6").mkdir(parents=True)
            (root / "experiments" / "k6" / "benchmark.js").write_text("", encoding="utf-8")
            def fake(command, **kwargs):
                output_name = command[command.index("--summary-export") + 1].split("/")[-1]
                current_raw = next((root / "results").glob("**/raw")) if len(list((root / "results").glob("**/raw"))) == 1 else list((root / "results").glob("**/raw"))[-1]
                (current_raw / output_name).write_text(json.dumps({"metrics": {"http_reqs": {"values": {"count": 1, "rate": 1}}, "http_req_failed": {"values": {"rate": 0}}, "http_req_duration": {"values": {"med": 1, "p(95)": 2, "p(99)": 3}}}}), encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="ok", stderr="")
            spec = {"runId": "test", "adapter": "compose", "profile": "NO_MESH", "scenario": "SYNC_CHAIN", "seed": 1,
                    "targetUrl": "http://example", "workloadConfig": {}, "loadProfile": {"targetRps": 1, "warmupSeconds": 0, "durationSeconds": 1, "repetitions": 3}}
            paths = Runner(root, fake).execute(spec)
            shapes = [{str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()} for path in paths]
            self.assertEqual(shapes[0], shapes[1])
            self.assertEqual(shapes[1], shapes[2])

    def test_k6_values_shape_is_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "results" / "run" / "repeat-01" / "raw"
            raw.mkdir(parents=True)
            (raw / "k6-summary.json").write_text(json.dumps({"metrics": {
                "http_reqs": {"values": {"count": 5, "rate": 2.5}},
                "http_req_failed": {"values": {"rate": 0}},
                "http_req_duration": {"values": {"med": 1, "p(95)": 2, "p(99)": 3}},
                "dropped_iterations": {"values": {"count": 0}},
            }}), encoding="utf-8")
            spec = {"runId": "run", "adapter": "compose", "profile": "NO_MESH", "scenario": "SYNC_CHAIN"}
            summary = Runner(root)._summary(spec, raw.parent, "start", "end")
            self.assertEqual(summary["sampleCount"], 5)
            self.assertEqual(summary["metrics"]["latencyMs"]["p95"], 2)

    def test_restart_gate_uses_measurement_delta(self):
        before = {"pods": [{"name": "workload-a", "restarts": 2}]}
        unchanged = {"pods": [{"name": "workload-a", "restarts": 2}]}
        increased = {"pods": [{"name": "workload-a", "restarts": 3}]}
        self.assertEqual(KubernetesAdapter.restart_delta_gate(before, unchanged), [])
        self.assertEqual(
            KubernetesAdapter.restart_delta_gate(before, increased),
            ["WORKLOAD_RESTARTS_INCREASED"],
        )


if __name__ == "__main__": unittest.main()
