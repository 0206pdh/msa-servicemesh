from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import threading
import time
from pathlib import Path

from experiments.capacity import discovery_spec
from experiments.runner.cli import Runner, canonical, now
from experiments.runner.kubernetes import KubernetesAdapter

# Phase 10 resilience experiments (ADR-0030). Directional scope, not this
# project's full 20,000-request formal floor -- the goal is characterizing
# fault response (error-rate spike, recovery time), not a tight latency CI.
POD_KILL_RUN_ID = "phase10-pod-kill-orchestrator"
POD_KILL_TARGET_RPS = 8
POD_KILL_WARMUP_SECONDS = 60
POD_KILL_DURATION_SECONDS = 300
POD_KILL_AFTER_SECONDS = 120
POD_KILL_TARGET_LABEL = "app.kubernetes.io/name=orchestrator-service"
POD_KILL_NAMESPACE = "benchmark"


def pod_kill_spec() -> dict:
    spec = discovery_spec(POD_KILL_RUN_ID, POD_KILL_TARGET_RPS, profile="AMBIENT")
    spec["loadProfile"].update({
        "warmupSeconds": POD_KILL_WARMUP_SECONDS,
        "durationSeconds": POD_KILL_DURATION_SECONDS,
        # A fault-induced error spike is the expected signal here, not a
        # test failure -- don't let k6's own threshold mark the run FAILED.
        "maximumErrorRate": 1.0,
    })
    return spec


def _k6_command(runner: Runner, spec: dict, output: Path, container_name: str) -> list[str]:
    load = spec["loadProfile"]
    script = (runner.root / "experiments" / "k6" / "benchmark.js").resolve()
    mount = str(output.parent.resolve()).replace("\\", "/")
    return ["docker", "run", "--rm", "--name", container_name,
            "-v", f"{mount}:/results", "-v", f"{str(script).replace(chr(92), '/')}:/scripts/benchmark.js:ro",
            "-e", f"TARGET_URL={spec['targetUrl']}", "-e", f"SCENARIO={spec['scenario']}",
            "-e", f"RUN_ID={spec['runId']}", "-e", f"SEED={spec['seed']}",
            "-e", f"TARGET_RPS={load['targetRps']}", "-e", f"DURATION={load['durationSeconds']}s",
            "-e", f"EXPECTED_ITERATION_MS={load.get('expectedIterationMs', 250)}",
            "-e", f"PRE_ALLOCATED_VUS={load.get('preAllocatedVUs', '')}",
            "-e", f"MAX_ERROR_RATE={load.get('maximumErrorRate', 0.01)}",
            "-e", f"WORKLOAD_CONFIG={canonical(spec['workloadConfig'])}",
            "grafana/k6:0.49.0", "run", "--summary-export", f"/results/{output.name}", "/scripts/benchmark.js"]


def kill_target_pod(namespace: str, label_selector: str, kubeconfig: str | None) -> dict:
    """Deletes the (single) pod matching label_selector and returns identifying
    info for the audit trail. Kubernetes recreates it immediately via the
    owning Deployment -- no manual recovery step is required."""
    kubectl = ["kubectl"] + (["--kubeconfig", kubeconfig] if kubeconfig else [])
    get_result = subprocess.run(
        kubectl + ["-n", namespace, "get", "pods", "-l", label_selector, "-o", "json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    pods = json.loads(get_result.stdout or "{}").get("items", [])
    if not pods:
        raise RuntimeError(f"no pod matched selector {label_selector!r} to kill")
    pod_name = pods[0]["metadata"]["name"]
    killed_at = now()
    subprocess.run(kubectl + ["-n", namespace, "delete", "pod", pod_name, "--wait=false"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    return {"podName": pod_name, "killedAt": killed_at}


def error_rate_timeseries(adapter: KubernetesAdapter, start_iso: str, end_iso: str,
                           step_seconds: int = 5) -> list[dict]:
    from datetime import datetime
    start = datetime.fromisoformat(start_iso.replace("Z", "+00:00")).timestamp()
    end = datetime.fromisoformat(end_iso.replace("Z", "+00:00")).timestamp()
    response = adapter.prometheus_query_range(
        'sum(rate(http_server_requests_seconds_count{namespace="benchmark",'
        'uri="/api/v1/workloads/chain",outcome!="SUCCESS"}[10s])) / '
        'clamp_min(sum(rate(http_server_requests_seconds_count{namespace="benchmark",'
        'uri="/api/v1/workloads/chain"}[10s])), 0.001)',
        start, end, step_seconds,
    )
    series = adapter._matrix(response)
    return series[0]["values"] if series else []


def recovery_seconds(values: list[list[float]], killed_at_epoch: float,
                      recovered_threshold: float = 0.02, sustained_seconds: int = 15) -> float | None:
    """Seconds from the kill until the error-rate series first drops back
    under recovered_threshold and stays there for sustained_seconds. None if
    it never recovers within the observed window."""
    points = [(ts, val) for ts, val in values if ts >= killed_at_epoch]
    if not points:
        return None
    for index, (ts, val) in enumerate(points):
        if val > recovered_threshold:
            continue
        window_end = ts + sustained_seconds
        if all(v <= recovered_threshold for later_ts, v in points[index:] if later_ts <= window_end):
            return ts - killed_at_epoch
    return None


def run_pod_kill_repeat(root: Path, repeat: int, kubeconfig: str | None = None) -> dict:
    spec = pod_kill_spec()
    run_dir = root / "results" / spec["runId"] / f"repeat-{repeat:02d}"
    if run_dir.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {run_dir}")
    raw = run_dir / "raw"
    raw.mkdir(parents=True)
    runner = Runner(root)
    adapter = KubernetesAdapter(root, spec)

    runner._run_k6(spec, raw / "warmup-summary.json", warmup=True)

    output = raw / "k6-summary.json"
    container_name = "meshperf-k6-" + hashlib.sha256(f"{spec['runId']}:{repeat}".encode()).hexdigest()[:12]
    command = _k6_command(runner, spec, output, container_name)
    started = now()
    process = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)

    time.sleep(POD_KILL_AFTER_SECONDS)
    kill_info = kill_target_pod(POD_KILL_NAMESPACE, POD_KILL_TARGET_LABEL, kubeconfig)

    stdout, stderr = process.communicate(timeout=spec["loadProfile"]["durationSeconds"] + 120)
    ended = now()
    (raw / "k6-summary.stdout.log").write_text(stdout or "", encoding="utf-8")
    (raw / "k6-summary.stderr.log").write_text(stderr or "", encoding="utf-8")

    k6_summary = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
    error_series = error_rate_timeseries(adapter, started, ended)
    from datetime import datetime
    killed_epoch = datetime.fromisoformat(kill_info["killedAt"].replace("Z", "+00:00")).timestamp()
    recovery = recovery_seconds(error_series, killed_epoch)
    peak_error_rate = max((val for _, val in error_series if _ >= killed_epoch), default=None)

    result = {
        "runId": spec["runId"], "repeat": repeat, "window": {"start": started, "end": ended},
        "killInfo": kill_info, "k6ExitCode": process.returncode,
        "overallErrorRate": k6_summary.get("metrics", {}).get("http_req_failed", {}).get("values", {}).get("rate"),
        "peakErrorRateDuringFault": peak_error_rate,
        "recoverySeconds": recovery,
        "errorRateTimeseries": error_series,
    }
    (run_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--reps", type=int, default=10)
    parser.add_argument("--kubeconfig", default=None)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    existing = sorted((root / "results" / POD_KILL_RUN_ID).glob("repeat-*")) if (root / "results" / POD_KILL_RUN_ID).exists() else []
    start_at = len(existing) + 1
    for repeat in range(start_at, start_at + args.reps):
        result = run_pod_kill_repeat(root, repeat, args.kubeconfig)
        print(json.dumps({"repeat": repeat, "recoverySeconds": result["recoverySeconds"],
                          "peakErrorRateDuringFault": result["peakErrorRateDuringFault"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
