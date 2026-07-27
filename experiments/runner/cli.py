from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from experiments.runner.kubernetes import KubernetesAdapter

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
            adapter = KubernetesAdapter(self.root, spec) if spec["adapter"] == "kubernetes" else None
            preflight = adapter.snapshot() if adapter else None
            preflight_factors = adapter.gate(preflight) if adapter else []
            if adapter:
                self._write(raw / "kubernetes-preflight.json", preflight)
                self._write(raw / "preflight-gate.json", {"invalidatingFactors": preflight_factors})
                trace_marker = adapter.trace_marker(spec["runId"])
                log_marker = adapter.log_marker(spec["runId"])
                self._write(raw / "tempo-trace-marker.json", trace_marker)
                self._write(raw / "loki-log-marker.json", log_marker)
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
            telemetry_settle_seconds = int(spec.get("kubernetes", {}).get("telemetrySettleSeconds", 20)) if adapter else 0
            if telemetry_settle_seconds:
                time.sleep(telemetry_settle_seconds)
            postflight = adapter.snapshot() if adapter else None
            window_snapshot = adapter.window_snapshot(
                spec["loadProfile"]["warmupSeconds"] + spec["loadProfile"]["durationSeconds"]
                + telemetry_settle_seconds + 30
            ) if adapter else None
            hubble_flows = adapter.hubble_flows(spec["loadProfile"]["durationSeconds"] + 30) if adapter else []
            cleanup_factors = (adapter.cleanup_gate() + adapter.window_gate(window_snapshot)
                               + adapter.restart_delta_gate(preflight, postflight)
                               + adapter.telemetry_gate(trace_marker, log_marker, hubble_flows)) if adapter else []
            if adapter:
                self._write(raw / "kubernetes-postflight.json", postflight)
                self._write(raw / "prometheus-window.json", window_snapshot)
                self._write(raw / "hubble-flows.json", hubble_flows)
                self._write(raw / "cleanup-gate.json", {"invalidatingFactors": cleanup_factors})
            summary = self._summary(spec, run_dir, started, ended, preflight_factors + cleanup_factors,
                                    preflight, postflight, window_snapshot)
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
        container_name = "meshperf-k6-" + hashlib.sha256(
            f"{spec['runId']}:{output.parent}:{output.name}".encode()
        ).hexdigest()[:12]
        command = ["docker", "run", "--rm", "--name", container_name,
                   "-v", f"{mount}:/results", "-v", f"{str(script).replace(chr(92), '/')}:/scripts/benchmark.js:ro",
                   "-e", f"TARGET_URL={spec['targetUrl']}", "-e", f"SCENARIO={spec['scenario']}",
                   "-e", f"RUN_ID={spec['runId']}", "-e", f"SEED={spec['seed']}",
                   "-e", f"TARGET_RPS={load['targetRps']}", "-e", f"DURATION={duration}s",
                   "-e", f"EXPECTED_ITERATION_MS={load.get('expectedIterationMs', 250)}",
                   "-e", f"PRE_ALLOCATED_VUS={load.get('preAllocatedVUs', '')}",
                   "-e", f"MAX_ERROR_RATE={load.get('maximumErrorRate', 0.01)}",
                   "-e", f"WORKLOAD_CONFIG={canonical(spec['workloadConfig'])}",
                   "grafana/k6:0.49.0", "run", "--summary-export", f"/results/{output.name}", "/scripts/benchmark.js"]
        samples: list[dict] = []
        stop = threading.Event()
        sampler = None
        if spec["adapter"] == "kubernetes":
            sampler = threading.Thread(target=self._sample_docker_stats,
                                       args=(container_name, samples, stop), daemon=True)
            sampler.start()
        result = self.command_runner(command, cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True)
        stop.set()
        if sampler:
            sampler.join(timeout=5)
            self._write(output.parent / f"{output.stem}.load-generator.json", {"samples": samples})
        (output.parent / f"{output.stem}.stdout.log").write_text(result.stdout or "", encoding="utf-8")
        (output.parent / f"{output.stem}.stderr.log").write_text(result.stderr or "", encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"k6 failed with exit code {result.returncode}")

    def _sample_docker_stats(self, container_name: str, samples: list[dict], stop: threading.Event) -> None:
        while not stop.is_set():
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{json .}}", container_name],
                cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    item = json.loads(result.stdout.strip().splitlines()[-1])
                    samples.append({"at": now(), "cpuPercent": self._percent(item.get("CPUPerc")),
                                    "memoryPercent": self._percent(item.get("MemPerc")),
                                    "memoryUsage": item.get("MemUsage")})
                except json.JSONDecodeError:
                    pass
            stop.wait(1)

    @staticmethod
    def _percent(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value.rstrip("%"))
        except ValueError:
            return None

    def _ground_truth(self, spec: dict) -> dict:
        commit = self._git("rev-parse", "HEAD") or "unknown"
        dirty = bool(self._git("status", "--porcelain"))
        kubernetes = spec["adapter"] == "kubernetes"
        version = self._kubectl("version", "-o", "json") if kubernetes else None
        docker_host = None
        if kubernetes:
            result = subprocess.run(["docker", "info", "--format", "{{json .}}"], cwd=self.root,
                                    text=True, encoding="utf-8", errors="replace", capture_output=True)
            if result.returncode == 0:
                try:
                    info = json.loads(result.stdout)
                    docker_host = {"name": info.get("Name"), "operatingSystem": info.get("OperatingSystem"),
                                   "architecture": info.get("Architecture"), "cpus": info.get("NCPU"),
                                   "memoryBytes": info.get("MemTotal"), "serverVersion": info.get("ServerVersion"),
                                   "separateFromKubernetesNodes": True}
                except json.JSONDecodeError:
                    pass
        return {"capturedAt": now(), "adapter": spec["adapter"], "measurementEligible": kubernetes,
                "host": {"os": platform.platform(), "python": platform.python_version()},
                "loadGeneratorHost": docker_host,
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

    def _summary(self, spec: dict, run_dir: Path, started: str, ended: str,
                 gate_factors: list[str] | None = None, preflight: dict | None = None,
                 postflight: dict | None = None, window_snapshot: dict | None = None) -> dict:
        data = json.loads((run_dir / "raw" / "k6-summary.json").read_text(encoding="utf-8"))
        metrics = data.get("metrics", {})
        values = metrics.get("http_req_duration", {}).get("values", metrics.get("http_req_duration", {}))
        failed_metric = metrics.get("http_req_failed", {}).get("values", metrics.get("http_req_failed", {}))
        failed = failed_metric.get("rate", failed_metric.get("value"))
        requests = metrics.get("http_reqs", {}).get("values", metrics.get("http_reqs", {}))
        dropped_metric = metrics.get("dropped_iterations", {})
        dropped = dropped_metric.get("values", dropped_metric).get("count", 0)
        invalid = list(gate_factors or [])
        if dropped: invalid.append("DROPPED_ITERATIONS")
        sample_count = int(requests.get("count", 0))
        load_profile = spec.get("loadProfile", {})
        minimum_requests = int(load_profile.get("minimumRequests", 0))
        if minimum_requests and sample_count < minimum_requests:
            invalid.append("INSUFFICIENT_REQUEST_SAMPLES")
        achieved_rate = requests.get("rate")
        target_rate = float(load_profile.get("targetRps", 0))
        if target_rate and (achieved_rate is None or achieved_rate / target_rate < 0.98):
            invalid.append("TARGET_RATE_NOT_ACHIEVED")
        if spec["adapter"] != "kubernetes": invalid.append("NON_MEASUREMENT_COMPOSE_ADAPTER")
        if spec["adapter"] == "kubernetes" and self._git("status", "--porcelain"):
            invalid.append("DIRTY_SOURCE_TREE")
        load_stats_path = run_dir / "raw" / "k6-summary.load-generator.json"
        load_samples = []
        if load_stats_path.exists():
            load_samples = json.loads(load_stats_path.read_text(encoding="utf-8")).get("samples", [])
        load_cpu = [item["cpuPercent"] for item in load_samples if item.get("cpuPercent") is not None]
        load_cpu_peak = max(load_cpu) if load_cpu else None
        if spec["adapter"] == "kubernetes" and load_cpu_peak is None:
            invalid.append("LOAD_GENERATOR_HEADROOM_MISSING")
        if load_cpu_peak is not None and load_cpu_peak >= float(spec.get("loadGeneratorCpuLimitPercent", 80)):
            invalid.append("LOAD_GENERATOR_CPU_HIGH")
        if preflight and postflight:
            before = preflight["prometheus"].get("requestCount") or 0
            after = postflight["prometheus"].get("requestCount") or 0
            if after <= before:
                invalid.append("PROMETHEUS_REQUEST_DELTA_MISSING")
        invalid = list(dict.fromkeys(invalid))
        status = "INVALID" if invalid else "COMPLETED"
        empty_resource = {"cpuCoreSeconds": None, "cpuPeakCores": None, "memoryPeakBytes": None, "networkRxBytes": None, "networkTxBytes": None}
        application_resource = empty_resource
        sidecar_resource = None
        ztunnel_resource = None
        node_resource = empty_resource
        if window_snapshot:
            application_resource = {"cpuCoreSeconds": window_snapshot.get("applicationCpuCoreSeconds"),
                                    "cpuPeakCores": window_snapshot.get("applicationCpuPeakCores"),
                                    "memoryPeakBytes": window_snapshot.get("applicationMemoryPeakBytes"),
                                    "networkRxBytes": window_snapshot.get("networkRxBytes"),
                                    "networkTxBytes": window_snapshot.get("networkTxBytes")}
            if window_snapshot.get("sidecarCpuCoreSeconds") is not None:
                sidecar_resource = {"cpuCoreSeconds": window_snapshot.get("sidecarCpuCoreSeconds"),
                                    "cpuPeakCores": window_snapshot.get("sidecarCpuPeakCores"),
                                    "memoryPeakBytes": window_snapshot.get("sidecarMemoryPeakBytes"),
                                    "cpuThrottledPeriods": window_snapshot.get("sidecarCpuThrottledPeriods")}
            if window_snapshot.get("ztunnelCpuCoreSeconds") is not None:
                ztunnel_resource = {"cpuCoreSeconds": window_snapshot.get("ztunnelCpuCoreSeconds"),
                                    "cpuPeakCores": window_snapshot.get("ztunnelCpuPeakCores"),
                                    "memoryPeakBytes": window_snapshot.get("ztunnelMemoryPeakBytes"),
                                    "cpuThrottledPeriods": window_snapshot.get("ztunnelCpuThrottledPeriods"),
                                    "attribution": "cluster-wide-shared-not-per-request"}
            node_resource = {**empty_resource, "cpuPeakPercent": window_snapshot.get("nodeCpuPeakPercent"),
                             "memoryMinimumByNode": window_snapshot.get("nodeMemoryMinimum")}
        return {"runId": spec["runId"], "profile": spec["profile"], "scenario": spec["scenario"], "status": status,
                "window": {"start": started, "end": ended}, "sampleCount": sample_count,
                "metrics": {"throughputRps": requests.get("rate"), "errorRate": failed,
                            "latencyMs": {"p50": values.get("med"), "p95": values.get("p(95)"), "p99": values.get("p(99)")}},
                "resources": {"application": application_resource, "sidecar": sidecar_resource, "ztunnel": ztunnel_resource, "waypoint": None,
                              "node": node_resource, "loadGenerator": {"cpuPeakPercent": load_cpu_peak,
                              "sampleCount": len(load_samples)}},
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
