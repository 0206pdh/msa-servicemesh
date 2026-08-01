from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

from experiments.runner.cli import Runner


CAPACITY_FAILURE_FACTORS = {
    "ACHIEVED_TARGET_RATIO_BELOW_MINIMUM",
    "DROPPED_ITERATIONS",
    "ERROR_RATE_EXCEEDED",
    "P99_EXCEEDS_2X_LOW_LOAD",
    "NODE_CPU_HEADROOM_LOW",
    "LOAD_GENERATOR_CPU_SATURATED",
    "NODE_MEMORY_HEADROOM_LOW",
}


def discovery_spec(run_id: str, target_rps: int, kubeconfig: str | None = None, profile: str = "NO_MESH",
                    expected_scrape_targets: int = 7, hop_delay_ms: int = 1) -> dict:
    load = {
        "executor": "CONSTANT_ARRIVAL_RATE",
        "targetRps": target_rps,
        "expectedIterationMs": 250,
        "maximumErrorRate": 0.01,
        "warmupSeconds": 120,
        "durationSeconds": 180,
        "repetitions": 1,
    }
    config = {
        "namespace": "benchmark",
        "prometheusNamespace": "observability",
        "prometheusService": "monitoring-kube-prometheus-prometheus",
        "expectedScrapeTargets": expected_scrape_targets,
        "minimumNodeMemoryAvailableBytes": 1_073_741_824,
        "maximumNodeCpuPercent": 85,
        "telemetrySettleSeconds": 20,
    }
    if kubeconfig:
        config["kubeconfig"] = kubeconfig
    return {
        "runId": run_id,
        "adapter": "kubernetes",
        "profile": profile,
        "scenario": "SYNC_CHAIN",
        "seed": 42,
        "targetUrl": "http://192.168.200.100",
        "workloadConfig": {
            "hopCount": 3,
            "payloadBytes": 1024,
            "work": {"delayMs": hop_delay_ms, "delayDistribution": "FIXED", "errorRate": 0,
                     "cpuMillis": 0, "memoryBytes": 0, "blockingIoMs": 0, "seed": 42},
        },
        "loadProfile": load,
        "kubernetes": config,
    }


def evaluate(summary: dict, low_load_p99: float | None) -> dict:
    target = summary["loadProfileTargetRps"] if "loadProfileTargetRps" in summary else None
    p99 = summary.get("metrics", {}).get("latencyMs", {}).get("p99")
    factors = list(summary.get("invalidatingFactors", []))
    if low_load_p99 and p99 is not None and p99 > low_load_p99 * 2:
        factors.append("P99_EXCEEDS_2X_LOW_LOAD")
    non_capacity_factors = [factor for factor in factors if factor not in CAPACITY_FAILURE_FACTORS]
    if non_capacity_factors:
        outcome = "INVALID"
    elif factors:
        outcome = "CAPACITY_FAIL"
    elif summary.get("status") == "COMPLETED":
        outcome = "PASS"
    else:
        outcome = "INVALID"
    return {"passed": outcome == "PASS", "outcome": outcome,
            "targetRps": target, "p99Ms": p99, "factors": factors}


class CapacityDiscovery:
    def __init__(self, root: Path, state_path: Path, start_rps: int = 10, factor: int = 2,
                 max_rps: int = 5120, refinement_steps: int = 4, cooldown_seconds: int = 60):
        self.root = root
        self.state_path = state_path
        self.start_rps = start_rps
        self.factor = factor
        self.max_rps = max_rps
        self.refinement_steps = refinement_steps
        self.cooldown_seconds = cooldown_seconds
        self.state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"scenario": "SYNC_CHAIN", "variant": "hop-3-payload-1KiB-delay-1ms",
                "lowLoadP99Ms": None, "points": [], "status": "GEOMETRIC_SEARCH"}

    def _write(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _existing(self, rps: int) -> dict | None:
        points = [point for point in self.state["points"] if point["targetRps"] == rps]
        for point in reversed(points):
            outcome = point.get("outcome")
            if outcome is None:
                factors = point.get("factors", [])
                if point.get("passed"):
                    outcome = "PASS"
                elif all(factor in CAPACITY_FAILURE_FACTORS for factor in factors):
                    outcome = "CAPACITY_FAIL"
                else:
                    outcome = "INVALID"
            if outcome != "INVALID":
                return point
        return None

    def run_point(self, rps: int, phase: str) -> dict:
        existing = self._existing(rps)
        if existing:
            return existing
        attempt = 1 + sum(point["targetRps"] == rps for point in self.state["points"])
        run_id = f"phase4-chain-capacity-{phase.lower()}-rps-{rps:05d}"
        if attempt > 1:
            run_id += f"-retry-{attempt:02d}"
        spec = discovery_spec(run_id, rps)
        run_dir = Runner(self.root).execute(spec, 1)[0]
        summary_path = run_dir / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["loadProfileTargetRps"] = rps
        result = evaluate(summary, self.state["lowLoadP99Ms"])
        point = {"phase": phase, "runId": run_id, "targetRps": rps,
                 "status": summary.get("status"), "sampleCount": summary.get("sampleCount"),
                 "throughputRps": summary.get("metrics", {}).get("throughputRps"),
                 "errorRate": summary.get("metrics", {}).get("errorRate"),
                 "p95Ms": summary.get("metrics", {}).get("latencyMs", {}).get("p95"),
                 "p99Ms": result["p99Ms"], "passed": result["passed"],
                 "outcome": result["outcome"], "factors": result["factors"],
                 "resources": summary.get("resources", {})}
        if self.state["lowLoadP99Ms"] is None and point["passed"]:
            self.state["lowLoadP99Ms"] = point["p99Ms"]
        self.state["points"].append(point)
        self._write()
        return point

    def execute(self) -> dict:
        rps = self.start_rps
        last_pass = None
        first_fail = None
        while rps <= self.max_rps:
            point = self.run_point(rps, "GEOMETRIC")
            if point.get("outcome") == "INVALID":
                self.state.update({"status": "INVALID_POINT", "invalidPointRps": rps})
                self._write()
                return self.state
            if point["passed"]:
                last_pass = rps
                rps *= self.factor
                if self.cooldown_seconds:
                    time.sleep(self.cooldown_seconds)
            else:
                first_fail = rps
                break
        if last_pass is None:
            self.state["status"] = "FAILED_AT_START"
            self._write()
            return self.state
        if first_fail is None:
            self.state["status"] = "CAPACITY_ABOVE_SAFETY_MAX"
            self.state["lastPassedRps"] = last_pass
            self._write()
            return self.state
        self.state["status"] = "BINARY_REFINEMENT"
        low, high = last_pass, first_fail
        self._write()
        for _ in range(self.refinement_steps):
            if (high - low) / low <= 0.10:
                break
            midpoint = math.floor((low + high) / 2)
            point = self.run_point(midpoint, "REFINE")
            if point.get("outcome") == "INVALID":
                self.state.update({"status": "INVALID_POINT", "invalidPointRps": midpoint})
                self._write()
                return self.state
            if point["passed"]:
                low = midpoint
            else:
                high = midpoint
            if self.cooldown_seconds:
                time.sleep(self.cooldown_seconds)
        self.state.update({"status": "COMPLETED", "usableCapacityRps": low,
                           "firstFailingRps": high, "relativeIntervalWidth": (high - low) / low,
                           "operatingPointsRps": {"low": round(low * 0.10), "nominal": round(low * 0.30),
                                                  "high": round(low * 0.60),
                                                  "nearSaturation": round(low * 0.80)}})
        self._write()
        return self.state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--state", type=Path, default=Path("results/phase4-chain-capacity/discovery.json"))
    parser.add_argument("--max-rps", type=int, default=5120)
    parser.add_argument("--cooldown-seconds", type=int, default=60)
    args = parser.parse_args(argv)
    result = CapacityDiscovery(args.root.resolve(), args.state.resolve(), max_rps=args.max_rps,
                               cooldown_seconds=args.cooldown_seconds).execute()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
