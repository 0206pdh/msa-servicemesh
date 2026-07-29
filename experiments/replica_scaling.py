from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.capacity import discovery_spec
from experiments.runner.cli import Runner

# Directional replica-scaling study (ADR-0027). Not a formal 10-15-rep
# baseline: 3 reps per point, nominal load only, shorter warm-up/duration.
# Purpose is comparing HOW sidecar vs ztunnel resource totals move as
# orchestrator-service replica count grows, not tight CI bounds.
NOMINAL_RPS = 8
REPLICA_COUNTS = (1, 2, 4)
REPS_PER_POINT = 3
FIXED_SYNC_CHAIN_TARGETS = 6  # gateway, workload-a/b/c, producer, worker (orchestrator scales)


def scaling_spec(profile: str, replicas: int, repeat: int) -> dict:
    run_id = f"phase8-replica-scaling-{profile.lower()}-r{replicas}"
    spec = discovery_spec(run_id, NOMINAL_RPS, profile=profile)
    spec["loadProfile"]["warmupSeconds"] = 60
    spec["loadProfile"]["durationSeconds"] = 180
    spec["kubernetes"]["expectedScrapeTargets"] = FIXED_SYNC_CHAIN_TARGETS + replicas
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--profile", required=True, choices=["SIDECAR", "AMBIENT"])
    parser.add_argument("--replicas", type=int, required=True, choices=REPLICA_COUNTS)
    parser.add_argument("--reps", type=int, default=REPS_PER_POINT)
    args = parser.parse_args(argv)

    runner = Runner(args.root.resolve())
    spec = scaling_spec(args.profile, args.replicas, args.reps)
    results = []
    for repeat in range(1, args.reps + 1):
        run_dir = runner._repeat(spec, repeat)
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        results.append({"repeat": repeat, "status": summary["status"],
                         "invalidatingFactors": summary.get("invalidatingFactors", [])})
        print(json.dumps(results[-1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
