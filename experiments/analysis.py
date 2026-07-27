from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path


POLICY = {
    "minimumValidRuns": 10,
    "maximumValidRuns": 15,
    "bootstrapResamples": 10_000,
    "confidenceLevel": 0.95,
    # A metric passes if EITHER the relative half-width or the absolute
    # half-width threshold is met (see ADR-0023). Relative-only thresholds
    # overstate noise on this cluster's small (~25-40ms) baseline latencies;
    # the absolute floor keeps the gate meaningful once relative width can't
    # converge within the 15-run cap.
    "precision": {
        "p95Ms": {"relative": 0.05, "absolute": 5.0},
        "p99Ms": {"relative": 0.10, "absolute": 8.0},
        "cpuCoreSecondsPerRequest": {"relative": 0.05, "absolute": 0.01},
    },
}


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_median_ci(values: list[float], seed: int, resamples: int = 10_000,
                        confidence: float = 0.95) -> tuple[float, float]:
    rng = random.Random(seed)
    medians = [statistics.median(rng.choices(values, k=len(values))) for _ in range(resamples)]
    alpha = (1 - confidence) / 2
    return percentile(medians, alpha), percentile(medians, 1 - alpha)


def metric_summary(values: list[float], seed: int) -> dict:
    median = statistics.median(values)
    low, high = bootstrap_median_ci(values, seed, POLICY["bootstrapResamples"], POLICY["confidenceLevel"])
    deviations = [abs(value - median) for value in values]
    half_width = (high - low) / 2
    return {
        "count": len(values),
        "median": median,
        "min": min(values),
        "max": max(values),
        "q1": percentile(values, 0.25),
        "q3": percentile(values, 0.75),
        "mad": statistics.median(deviations),
        "confidenceInterval95": {"low": low, "high": high},
        "halfWidth": half_width,
        "relativeHalfWidth": None if median == 0 else half_width / abs(median),
    }


def extract(summary: dict) -> dict[str, float | None]:
    samples = summary.get("sampleCount", 0)
    resources = summary.get("resources", {}).get("application", {})
    cpu = resources.get("cpuCoreSeconds")
    extracted = {
        "throughputRps": summary.get("metrics", {}).get("throughputRps"),
        "p50Ms": summary.get("metrics", {}).get("latencyMs", {}).get("p50"),
        "p95Ms": summary.get("metrics", {}).get("latencyMs", {}).get("p95"),
        "p99Ms": summary.get("metrics", {}).get("latencyMs", {}).get("p99"),
        "errorRate": summary.get("metrics", {}).get("errorRate"),
        "cpuCoreSecondsPerRequest": None if not samples or cpu is None else cpu / samples,
        "memoryPeakBytes": resources.get("memoryPeakBytes"),
        "networkBytesPerRequest": None if not samples else (
            (resources.get("networkRxBytes") or 0) + (resources.get("networkTxBytes") or 0)
        ) / samples,
    }
    sidecar = summary.get("resources", {}).get("sidecar")
    if sidecar is not None:
        sidecar_cpu = sidecar.get("cpuCoreSeconds")
        extracted["sidecarCpuCoreSecondsPerRequest"] = (
            None if not samples or sidecar_cpu is None else sidecar_cpu / samples
        )
        extracted["sidecarMemoryPeakBytes"] = sidecar.get("memoryPeakBytes")
        extracted["sidecarCpuThrottledPeriods"] = sidecar.get("cpuThrottledPeriods")
    ztunnel = summary.get("resources", {}).get("ztunnel")
    if ztunnel is not None:
        # Not normalized per-request: ztunnel is a per-node shared DaemonSet, not a
        # per-pod proxy, so "cost per request" would misattribute a value that other
        # workloads on the same node also contribute to (see ADR-0025).
        extracted["ztunnelCpuCoreSecondsAbsolute"] = ztunnel.get("cpuCoreSeconds")
        extracted["ztunnelMemoryPeakBytes"] = ztunnel.get("memoryPeakBytes")
        extracted["ztunnelCpuThrottledPeriods"] = ztunnel.get("cpuThrottledPeriods")
    return extracted


def analyze(condition_dir: Path, seed: int = 42, required_fingerprint: str | None = None) -> dict:
    summaries = []
    invalid = []
    fingerprints = set()
    for path in sorted(condition_dir.glob("repeat-*/summary.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        manifest_path = path.parent / "manifest.json"
        fingerprint = (
            json.loads(manifest_path.read_text(encoding="utf-8")).get("configFingerprint")
            if manifest_path.exists() else None
        )
        if summary.get("status") == "COMPLETED" and (
            required_fingerprint is None or fingerprint == required_fingerprint
        ):
            summaries.append(summary)
            fingerprints.add(fingerprint)
        else:
            factors = list(summary.get("invalidatingFactors", []))
            if summary.get("status") == "COMPLETED" and required_fingerprint != fingerprint:
                factors.append("SUPERSEDED_CONFIG_FINGERPRINT")
            invalid.append({"path": str(path), "factors": factors})
    if len(fingerprints - {None}) > 1:
        raise ValueError("condition contains multiple config fingerprints")
    extracted = [extract(summary) for summary in summaries]
    metrics = {}
    for index, name in enumerate(extracted[0].keys() if extracted else []):
        values = [float(item[name]) for item in extracted if item[name] is not None]
        if values:
            metrics[name] = metric_summary(values, seed + index)
    precision = {}
    for name, threshold in POLICY["precision"].items():
        observed_relative = metrics.get(name, {}).get("relativeHalfWidth")
        observed_absolute = metrics.get(name, {}).get("halfWidth")
        passed_relative = observed_relative is not None and observed_relative <= threshold["relative"]
        passed_absolute = observed_absolute is not None and observed_absolute <= threshold["absolute"]
        precision[name] = {
            "threshold": threshold,
            "observedRelative": observed_relative,
            "observedAbsolute": observed_absolute,
            "passed": passed_relative or passed_absolute,
        }
    valid_count = len(summaries)
    if valid_count < POLICY["minimumValidRuns"]:
        decision = "CONTINUE"
    elif all(item["passed"] for item in precision.values()):
        decision = "STOP_PRECISION_REACHED"
    elif valid_count >= POLICY["maximumValidRuns"]:
        decision = "INCONCLUSIVE_MAX_RUNS"
    else:
        decision = "CONTINUE"
    return {"condition": str(condition_dir), "policy": POLICY, "validRuns": valid_count,
            "invalidRuns": invalid, "configFingerprints": sorted(value for value in fingerprints if value),
            "metrics": metrics, "precision": precision, "decision": decision}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("condition_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = analyze(args.condition_dir)
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
