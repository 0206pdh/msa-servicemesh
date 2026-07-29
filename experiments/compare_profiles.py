from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from experiments.analysis import collect_valid_runs, extract, percentile


def load_metric_values(condition_dir: Path, metric_name: str,
                        required_fingerprint: str | None = None) -> list[float]:
    collected = collect_valid_runs(condition_dir, required_fingerprint)
    extracted = [extract(summary) for summary in collected["summaries"]]
    return [float(item[metric_name]) for item in extracted if item.get(metric_name) is not None]


def bootstrap_difference_ci(values_a: list[float], values_b: list[float], seed: int,
                             resamples: int = 10_000, confidence: float = 0.95) -> dict:
    """Two-sample bootstrap CI for median(b) - median(a).

    The two groups are resampled independently (not index-paired) because runs
    across profiles were never executed in matched blocks -- each profile's
    canonical baseline is its own independent repeated-measurement session
    (see ADR-0023/0027 on this project's own confidence-interval methodology).
    """
    rng = random.Random(seed)
    differences = []
    for _ in range(resamples):
        resample_a = rng.choices(values_a, k=len(values_a))
        resample_b = rng.choices(values_b, k=len(values_b))
        differences.append(_median(resample_b) - _median(resample_a))
    alpha = (1 - confidence) / 2
    low = percentile(differences, alpha)
    high = percentile(differences, 1 - alpha)
    return {
        "medianA": _median(values_a),
        "medianB": _median(values_b),
        "medianDifference": _median(values_b) - _median(values_a),
        "confidenceInterval95": {"low": low, "high": high},
        "significant": low > 0 or high < 0,
    }


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


COMPARISON_METRICS = ("throughputRps", "p95Ms", "p99Ms", "cpuCoreSecondsPerRequest",
                      "memoryPeakBytes", "networkBytesPerRequest")


def compare_conditions(label_a: str, dir_a: Path, label_b: str, dir_b: Path,
                        seed: int = 42, metrics: tuple[str, ...] = COMPARISON_METRICS,
                        required_fingerprint_a: str | None = None,
                        required_fingerprint_b: str | None = None) -> dict:
    results = {}
    for index, metric_name in enumerate(metrics):
        values_a = load_metric_values(dir_a, metric_name, required_fingerprint_a)
        values_b = load_metric_values(dir_b, metric_name, required_fingerprint_b)
        if len(values_a) < 2 or len(values_b) < 2:
            results[metric_name] = {"skipped": "insufficientSamples", "nA": len(values_a), "nB": len(values_b)}
            continue
        comparison = bootstrap_difference_ci(values_a, values_b, seed + index)
        comparison["nA"] = len(values_a)
        comparison["nB"] = len(values_b)
        results[metric_name] = comparison
    return {"labelA": label_a, "labelB": label_b, "comparisons": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("label_a")
    parser.add_argument("dir_a", type=Path)
    parser.add_argument("label_b")
    parser.add_argument("dir_b", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    result = compare_conditions(args.label_a, args.dir_a, args.label_b, args.dir_b, seed=args.seed)
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
