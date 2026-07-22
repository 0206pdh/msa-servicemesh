from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

STATES = ("PLANNED", "WARMING_UP", "RUNNING", "COLLECTING", "COMPLETED")
SCENARIOS = {"SYNC_CHAIN", "FAN_OUT", "ASYNC_PIPELINE", "PAYLOAD", "MIXED_RESOURCE"}
PROFILES = {"NO_MESH", "SIDECAR", "AMBIENT", "WAYPOINT"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_spec(spec: dict) -> None:
    required = {"runId", "adapter", "profile", "scenario", "seed", "targetUrl", "workloadConfig", "loadProfile"}
    missing = sorted(required - spec.keys())
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    if spec["adapter"] not in {"compose", "kubernetes"}:
        raise ValueError("adapter must be compose or kubernetes")
    if spec["profile"] not in PROFILES or spec["scenario"] not in SCENARIOS:
        raise ValueError("unknown profile or scenario")
    load = spec["loadProfile"]
    if load.get("targetRps", 0) <= 0 or load.get("durationSeconds", 0) < 1 or load.get("warmupSeconds", -1) < 0:
        raise ValueError("loadProfile bounds are invalid")


class Runner:
    def __init__(self, root: Path, command_runner=subprocess.run):
        self.root = root
        self.command_runner = command_runner

    def execute(self, spec: dict, repetitions: int | None = None) -> list[Path]:
        validate_spec(spec)
        count = repetitions or int(spec["loadProfile"].get("repetitions", 1))
        return [self._repeat(spec, index) for index in range(1, count + 1)]

    def _repeat(self, spec: dict, repetition: int) -> Path:
        run_dir = self.root / "results" / spec["runId"] / f"repeat-{repetition:02d}"
        if run_dir.exists():
            raise FileExistsError(f"refusing to overwrite evidence: {run_dir}")
        raw = run_dir / "raw"
        raw.mkdir(parents=True)
        history: list[dict] = []
        transition = lambda state: (history.append({"state": state, "at": now()}), self._write(run_dir / "state.json", {"history": history}))
        transition("PLANNED")
        try:
            ground = self._ground_truth(spec)
            self._write(run_dir / "ground-truth.json", ground)
            manifest = self._manifest(spec, repetition, ground)
            self._write(run_dir / "manifest.json", manifest)
            transition("WARMING_UP")
            if spec["loadProfile"]["warmupSeconds"]:
                self._run_k6(spec, raw / "warmup-summary.json", warmup=True)
            transition("RUNNING")
            started = now()
            self._run_k6(spec, raw / "k6-summary.json", warmup=False)
            ended = now()
            transition("COLLECTING")
            self._snapshot_metrics(spec, raw)
            summary = self._summary(spec, run_dir, started, ended)
            self._write(run_dir / "summary.json", summary)
            (run_dir / "report.md").write_text(self._report(summary), encoding="utf-8")
            transition("COMPLETED")
            return run_dir
        except Exception as exc:
            history.append({"state": "FAILED", "at": now(), "reason": str(exc)})
            self._write(run_dir / "state.json", {"history": history})
            self._write(run_dir / "failure.json", {"code": "RUNNER_ERROR", "message": str(exc)})
            raise

    def _run_k6(self, spec: dict, output: Path, warmup: bool) -> None:
        load = spec["loadProfile"]
        duration = load["warmupSeconds"] if warmup else load["durationSeconds"]
        script = (self.root / "experiments" / "k6" / "benchmark.js").resolve()
        mount = str(output.parent.resolve()).replace("\\", "/")
        command = ["docker", "run", "--rm", "-v", f"{mount}:/results", "-v", f"{str(script).replace(chr(92), '/')}:/scripts/benchmark.js:ro",
                   "-e", f"TARGET_URL={spec['targetUrl']}", "-e", f"SCENARIO={spec['scenario']}",
                   "-e", f"RUN_ID={spec['runId']}", "-e", f"SEED={spec['seed']}",
                   "-e", f"TARGET_RPS={load['targetRps']}", "-e", f"DURATION={duration}s",
                   "-e", f"WORKLOAD_CONFIG={canonical(spec['workloadConfig'])}",
                   "grafana/k6:0.49.0", "run", "--summary-export", f"/results/{output.name}", "/scripts/benchmark.js"]
        result = self.command_runner(command, cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True)
        (output.parent / f"{output.stem}.stdout.log").write_text(result.stdout or "", encoding="utf-8")
        (output.parent / f"{output.stem}.stderr.log").write_text(result.stderr or "", encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"k6 failed with exit code {result.returncode}")

    def _ground_truth(self, spec: dict) -> dict:
        commit = self._git("rev-parse", "HEAD") or "unknown"
        dirty = bool(self._git("status", "--porcelain"))
        kubernetes = spec["adapter"] == "kubernetes"
        version = self._kubectl("version", "-o", "json") if kubernetes else None
        return {"capturedAt": now(), "adapter": spec["adapter"], "measurementEligible": kubernetes,
                "host": {"os": platform.platform(), "python": platform.python_version()},
                "source": {"commit": commit, "dirty": dirty}, "kubernetesVersion": version or "not-applicable-compose-validation",
                "timeSynchronized": bool(spec.get("timeSynchronized", False)) if kubernetes else False,
                "loadGeneratorCpuPeakPercent": None, "configFingerprint": hashlib.sha256(canonical(spec).encode()).hexdigest()}

    def _manifest(self, spec: dict, repetition: int, ground: dict) -> dict:
        digest = hashlib.sha256(ground["source"]["commit"].encode()).hexdigest()
        return {"runId": spec["runId"], "createdAt": now(), "profile": spec["profile"], "scenario": spec["scenario"],
                "seed": spec["seed"], "configFingerprint": ground["configFingerprint"],
                "source": {**ground["source"], "repository": self._git("remote", "get-url", "origin") or None},
                "platform": {"kubernetesVersion": ground["kubernetesVersion"], "nodeInventory": [{"adapter": spec["adapter"]}],
                             "timeSynchronized": ground["timeSynchronized"], "componentVersions": {"k6": "0.49.0"}},
                "workload": {"config": spec["workloadConfig"], "images": {"suite": f"local@sha256:{digest}"}, "placement": {}, "resources": {}, "jvm": {"version": "25"}},
                "load": {"tool": "k6", "toolVersion": "0.49.0", "executor": spec["loadProfile"].get("executor", "CONSTANT_ARRIVAL_RATE"),
                         "targetRps": spec["loadProfile"]["targetRps"], "warmupSeconds": spec["loadProfile"]["warmupSeconds"],
                         "durationSeconds": spec["loadProfile"]["durationSeconds"], "repetition": repetition, "faultSchedule": spec.get("faultSchedule", [])},
                "telemetry": {"sampling": {}, "cardinalityPolicy": "docs/evidence-management.md", "queries": {}}}

    def _summary(self, spec: dict, run_dir: Path, started: str, ended: str) -> dict:
        data = json.loads((run_dir / "raw" / "k6-summary.json").read_text(encoding="utf-8"))
        metrics = data.get("metrics", {})
        values = metrics.get("http_req_duration", {})
        failed_metric = metrics.get("http_req_failed", {})
        failed = failed_metric.get("rate", failed_metric.get("value"))
        requests = metrics.get("http_reqs", {})
        dropped = metrics.get("dropped_iterations", {}).get("count", 0)
        invalid = []
        if dropped: invalid.append("DROPPED_ITERATIONS")
        if spec["adapter"] != "kubernetes": invalid.append("NON_MEASUREMENT_COMPOSE_ADAPTER")
        status = "INVALID" if invalid else "COMPLETED"
        empty_resource = {"cpuCoreSeconds": None, "cpuPeakCores": None, "memoryPeakBytes": None, "networkRxBytes": None, "networkTxBytes": None}
        return {"runId": spec["runId"], "profile": spec["profile"], "scenario": spec["scenario"], "status": status,
                "window": {"start": started, "end": ended}, "sampleCount": int(requests.get("count", 0)),
                "metrics": {"throughputRps": requests.get("rate"), "errorRate": failed,
                            "latencyMs": {"p50": values.get("med"), "p95": values.get("p(95)"), "p99": values.get("p(99)")}},
                "resources": {"application": empty_resource, "sidecar": None, "ztunnel": None, "waypoint": None, "node": empty_resource},
                "artifacts": {"manifest": "manifest.json", "raw": "raw/", "queries": {}}, "invalidatingFactors": invalid}

    def _snapshot_metrics(self, spec: dict, raw: Path) -> None:
        urls = spec.get("metricUrls", {})
        for name, url in urls.items():
            try:
                with urlopen(url, timeout=5) as response:
                    (raw / f"{name}.prom").write_bytes(response.read())
            except Exception as exc:
                (raw / f"{name}.error.txt").write_text(str(exc), encoding="utf-8")

    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True)
        return result.stdout.strip() if result.returncode == 0 else ""

    def _kubectl(self, *args: str) -> str:
        if not shutil.which("kubectl"): return ""
        result = subprocess.run(["kubectl", *args], cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True)
        return result.stdout.strip() if result.returncode == 0 else ""

    @staticmethod
    def _write(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _report(summary: dict) -> str:
        latency = summary["metrics"]["latencyMs"]
        return f"# Run {summary['runId']}\n\n- status: `{summary['status']}`\n- samples: {summary['sampleCount']}\n- throughput: {summary['metrics']['throughputRps']} req/s\n- p95 / p99: {latency['p95']} / {latency['p99']} ms\n- invalidating factors: {', '.join(summary['invalidatingFactors']) or 'none'}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("spec", type=Path)
    run.add_argument("--repetitions", type=int)
    run.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    paths = Runner(args.root.resolve()).execute(spec, args.repetitions)
    print(json.dumps([str(path) for path in paths], ensure_ascii=False))
    return 0
