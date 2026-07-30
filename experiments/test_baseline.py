import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.baseline import BaselineMeasurement, block_order, formal_spec, measurement_duration
from experiments.runner.cli import canonical


class _FakeRunner:
    def __init__(self, root):
        self.root = root

    def _repeat(self, spec, repeat):
        run_dir = self.root / "results" / spec["runId"] / f"repeat-{repeat:02d}"
        run_dir.mkdir(parents=True)
        fingerprint = hashlib.sha256(canonical(spec).encode()).hexdigest()
        (run_dir / "manifest.json").write_text(
            json.dumps({"configFingerprint": fingerprint}), encoding="utf-8"
        )
        (run_dir / "summary.json").write_text(
            json.dumps({"status": "COMPLETED", "sampleCount": 20_200}), encoding="utf-8"
        )
        return run_dir


class _FlakyRunner(_FakeRunner):
    """Fails the first attempt for one condition, like a k6 crash mid-run,
    then succeeds on retry - mirrors cli.py._repeat() writing failure
    evidence to disk before raising."""

    def __init__(self, root, fail_condition: str):
        super().__init__(root)
        self.fail_condition = fail_condition
        self.failed_once = False

    def _repeat(self, spec, repeat):
        if not self.failed_once and spec["runId"].endswith(self.fail_condition):
            self.failed_once = True
            run_dir = self.root / "results" / spec["runId"] / f"repeat-{repeat:02d}"
            run_dir.mkdir(parents=True)
            (run_dir / "failure.json").write_text(
                json.dumps({"code": "RUNNER_ERROR", "message": "k6 failed with exit code 99"}),
                encoding="utf-8",
            )
            raise RuntimeError("k6 failed with exit code 99")
        return super()._repeat(spec, repeat)


class BaselineMeasurementTests(unittest.TestCase):
    def test_duration_meets_twenty_thousand_request_floor(self):
        self.assertEqual(measurement_duration(8), 2525)
        self.assertEqual(measurement_duration(17), 1189)
        self.assertEqual(measurement_duration(22), 919)

    def test_formal_spec_uses_canonical_chain_and_request_floor(self):
        spec = formal_spec("nominal", 8)
        self.assertEqual(spec["scenario"], "SYNC_CHAIN")
        self.assertEqual(spec["profile"], "NO_MESH")
        self.assertEqual(spec["runId"], "phase4-chain-baseline-nominal")
        self.assertEqual(spec["workloadConfig"]["hopCount"], 3)
        self.assertEqual(spec["loadProfile"]["minimumRequests"], 20_000)
        self.assertEqual(spec["loadProfile"]["durationSeconds"], 2525)
        self.assertEqual(spec["loadProfile"]["preAllocatedVUs"], 128)
        self.assertEqual(spec["loadProfile"]["warmupSeconds"], 180)

    def test_formal_spec_no_mesh_fingerprint_is_stable(self):
        # Regression guard: Phase 4's already-collected valid runs were
        # selected against this exact fingerprint. Any change to
        # formal_spec()'s default (No-Mesh) output would silently orphan
        # that Evidence by making analyze() treat every existing run as
        # SUPERSEDED_CONFIG_FINGERPRINT.
        spec = formal_spec("nominal", 8)
        fingerprint = hashlib.sha256(canonical(spec).encode()).hexdigest()
        self.assertEqual(
            fingerprint,
            "3f24a3bdd2d885979cbccdf2f901be3a8840caf46ab6933a3361c0f121d066ba",
        )

    def test_formal_spec_accepts_a_different_profile_and_run_id_prefix(self):
        spec = formal_spec(
            "nominal", 8, run_id_prefix="phase5-sidecar-baseline", profile="SIDECAR"
        )
        self.assertEqual(spec["profile"], "SIDECAR")
        self.assertEqual(spec["runId"], "phase5-sidecar-baseline-nominal")
        # Same load-shape guarantees as the no-mesh spec.
        self.assertEqual(spec["loadProfile"]["minimumRequests"], 20_000)
        self.assertEqual(spec["loadProfile"]["preAllocatedVUs"], 128)

    def test_formal_spec_extra_fields_change_fingerprint_but_default_call_is_unaffected(self):
        base = formal_spec("nominal", 8, run_id_prefix="phase5-sidecar-baseline", profile="SIDECAR")
        variant = formal_spec(
            "nominal", 8, run_id_prefix="phase9-sidecar-mtls-disabled", profile="SIDECAR",
            extra_spec_fields={"meshVariant": "mtls-disabled"},
        )
        base_fingerprint = hashlib.sha256(canonical(base).encode()).hexdigest()
        variant_fingerprint = hashlib.sha256(canonical(variant).encode()).hexdigest()
        self.assertNotEqual(base_fingerprint, variant_fingerprint)
        self.assertEqual(variant["profile"], "SIDECAR")
        self.assertEqual(variant["meshVariant"], "mtls-disabled")
        # Regression guard: the pinned no-mesh fingerprint test above must still pass
        # unchanged since extra_spec_fields defaults to None.

    def test_formal_spec_accepts_expected_scrape_targets_override(self):
        default_spec = formal_spec("nominal", 8, run_id_prefix="phase9-ambient-replica4", profile="AMBIENT")
        self.assertEqual(default_spec["kubernetes"]["expectedScrapeTargets"], 7)
        scaled_spec = formal_spec(
            "nominal", 8, run_id_prefix="phase9-ambient-replica4", profile="AMBIENT",
            expected_scrape_targets=10,
        )
        self.assertEqual(scaled_spec["kubernetes"]["expectedScrapeTargets"], 10)

    def test_baseline_measurement_can_scope_to_a_single_condition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            measurement = BaselineMeasurement(
                root, root / "results" / "phase9-sidecar-mtls-disabled" / "state.json", 0,
                run_id_prefix="phase9-sidecar-mtls-disabled", profile="SIDECAR",
                conditions={"nominal": 8}, extra_spec_fields={"meshVariant": "mtls-disabled"},
            )
            with patch("experiments.baseline.Runner", _FakeRunner):
                state = measurement.execute_session(session=1, blocks=1)
            block = state["sessions"][0]["blocks"][0]
            conditions_seen = {run["condition"] for run in block["runs"]}
            self.assertEqual(conditions_seen, {"nominal"})
            run_dir = root / "results" / "phase9-sidecar-mtls-disabled-nominal" / "repeat-01"
            self.assertTrue(run_dir.exists())

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

    def _seed_valid_runs(self, root: Path, condition: str, target_rps: int, count: int) -> None:
        spec = formal_spec(condition, target_rps)
        fingerprint = hashlib.sha256(canonical(spec).encode()).hexdigest()
        directory = root / "results" / f"phase4-chain-baseline-{condition}"
        for repeat in range(1, count + 1):
            run_dir = directory / f"repeat-{repeat:02d}"
            run_dir.mkdir(parents=True)
            (run_dir / "manifest.json").write_text(
                json.dumps({"configFingerprint": fingerprint}), encoding="utf-8"
            )
            (run_dir / "summary.json").write_text(
                json.dumps({"status": "COMPLETED", "sampleCount": 20_200}), encoding="utf-8"
            )

    def test_new_session_executes_new_run_when_valid_runs_already_equal_block_count(self):
        # Regression test: a brand-new session must not burn its entire block
        # budget "recovering" valid runs that earlier sessions already
        # produced. Each condition here already has as many valid runs as
        # there are blocks in the session (5), which previously caused every
        # block to take the recovery branch and never execute a new run.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._seed_valid_runs(root, "nominal", 8, 5)
            self._seed_valid_runs(root, "high", 17, 5)
            self._seed_valid_runs(root, "near-saturation", 22, 5)
            measurement = BaselineMeasurement(
                root, root / "results" / "phase4-chain-baseline" / "state.json", 0
            )
            with patch("experiments.baseline.Runner", _FakeRunner):
                state = measurement.execute_session(session=3, blocks=1)
            block = state["sessions"][-1]["blocks"][0]
            fresh_runs = {
                run["condition"] for run in block["runs"]
                if run.get("status") == "COMPLETED" and not run.get("recovered")
            }
            self.assertEqual(fresh_runs, {"nominal", "high", "near-saturation"})

    def test_resumed_session_still_recovers_runs_completed_before_the_crash(self):
        # A session that crashes mid-way and is re-invoked with the same
        # session number must still reconcile already-completed blocks from
        # disk instead of re-running k6, so the baseline fix must not break
        # genuine same-session resume.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._seed_valid_runs(root, "nominal", 8, 0)
            self._seed_valid_runs(root, "high", 17, 0)
            self._seed_valid_runs(root, "near-saturation", 22, 0)
            state_path = root / "results" / "phase4-chain-baseline" / "state.json"
            measurement = BaselineMeasurement(root, state_path, 0)
            with patch("experiments.baseline.Runner", _FakeRunner):
                measurement.execute_session(session=1, blocks=1)

            # Simulate a crash that happened after "nominal" finished but
            # before "high"/"near-saturation" were recorded: drop their run
            # entries and flip the block back to RUNNING, as an interrupted
            # process would leave it, then resume the same session.
            resumed = BaselineMeasurement(root, state_path, 0)
            block_state = resumed.state["sessions"][0]["blocks"][0]
            block_state["status"] = "RUNNING"
            block_state["runs"] = [
                run for run in block_state["runs"] if run["condition"] == "nominal"
            ]
            with patch("experiments.baseline.Runner", _FakeRunner):
                state = resumed.execute_session(session=1, blocks=1)
            block = state["sessions"][0]["blocks"][0]
            recovered = [run for run in block["runs"] if run.get("recovered")]
            self.assertEqual({run["condition"] for run in recovered}, {"high", "near-saturation"})
            for condition in ("nominal", "high", "near-saturation"):
                directory_path = root / "results" / f"phase4-chain-baseline-{condition}"
                self.assertEqual(len(list(directory_path.glob("repeat-*"))), 1)

    def test_a_crashed_run_does_not_abort_the_whole_scheduler_process(self):
        # Regression test: an unhandled k6/runner failure previously
        # propagated all the way out of execute_session(), killing an
        # unattended multi-hour background process on a single flaky run.
        # The failure must instead be recorded and the block must continue.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            measurement = BaselineMeasurement(
                root, root / "results" / "phase4-chain-baseline" / "state.json", 0
            )
            with patch("experiments.baseline.Runner", lambda root: _FlakyRunner(root, "high")):
                state = measurement.execute_session(session=1, blocks=1)  # must not raise
            block = state["sessions"][0]["blocks"][0]
            statuses = {run["condition"]: run["status"] for run in block["runs"]}
            self.assertEqual(statuses["high"], "FAILED")
            self.assertEqual(statuses["nominal"], "COMPLETED")
            self.assertEqual(statuses["near-saturation"], "COMPLETED")
            # The failed attempt's evidence directory is preserved, not skipped.
            high_dir = root / "results" / "phase4-chain-baseline-high"
            self.assertEqual(len(list(high_dir.glob("repeat-*"))), 1)


if __name__ == "__main__":
    unittest.main()
