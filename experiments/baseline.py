from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from pathlib import Path

from experiments.analysis import analyze
from experiments.capacity import discovery_spec
from experiments.runner.cli import Runner, canonical


CONDITIONS = {"nominal": 8, "high": 17, "near-saturation": 22}
MINIMUM_REQUESTS = 20_000
PLANNED_REQUESTS = 20_200
MINIMUM_DURATION_SECONDS = 600
MAXIMUM_DURATION_SECONDS = 2_700


def measurement_duration(target_rps: int) -> int:
    required = math.ceil(PLANNED_REQUESTS / target_rps)
    return min(MAXIMUM_DURATION_SECONDS, max(MINIMUM_DURATION_SECONDS, required))


def formal_spec(
    condition: str, target_rps: int, run_id_prefix: str = "phase4-chain-baseline",
    profile: str = "NO_MESH",
) -> dict:
    spec = discovery_spec(f"{run_id_prefix}-{condition}", target_rps, profile=profile)
    spec["seed"] = 42
    spec["timeSynchronized"] = True
    spec["loadProfile"].update({
        "warmupSeconds": 180,
        "durationSeconds": measurement_duration(target_rps),
        "minimumRequests": MINIMUM_REQUESTS,
        "preAllocatedVUs": 128,
        "repetitions": 1,
    })
    return spec


def block_order(block: int, seed: int = 42) -> list[str]:
    names = list(CONDITIONS)
    random.Random(seed + block).shuffle(names)
    return names


class BaselineMeasurement:
    def __init__(
        self, root: Path, state_path: Path, cooldown_seconds: int = 120,
        run_id_prefix: str = "phase4-chain-baseline", profile: str = "NO_MESH",
    ):
        self.root = root
        self.state_path = state_path
        self.cooldown_seconds = cooldown_seconds
        self.run_id_prefix = run_id_prefix
        self.profile = profile
        self.state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {
            "scenario": "SYNC_CHAIN",
            "variant": "hop-3-payload-1KiB-delay-1ms",
            "profile": self.profile,
            "seed": 42,
            "conditions": CONDITIONS,
            "sessions": [],
            "status": "READY",
        }

    def _write(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def _condition_dir(self, condition: str) -> Path:
        return self.root / "results" / f"{self.run_id_prefix}-{condition}"

    def _next_repeat(self, condition: str) -> int:
        directory = self._condition_dir(condition)
        indices = []
        for path in directory.glob("repeat-*") if directory.exists() else []:
            try:
                indices.append(int(path.name.split("-")[-1]))
            except ValueError:
                continue
        return max(indices, default=0) + 1

    def _formal_spec(self, condition: str) -> dict:
        return formal_spec(
            condition, CONDITIONS[condition],
            run_id_prefix=self.run_id_prefix, profile=self.profile,
        )

    def _decision(self, condition: str) -> dict:
        directory = self._condition_dir(condition)
        spec = self._formal_spec(condition)
        fingerprint = hashlib.sha256(canonical(spec).encode()).hexdigest()
        return (
            analyze(directory, required_fingerprint=fingerprint)
            if directory.exists() else {"validRuns": 0, "decision": "CONTINUE"}
        )

    def _latest_selected_run(self, condition: str) -> tuple[int, Path, dict] | None:
        spec = self._formal_spec(condition)
        selected = hashlib.sha256(canonical(spec).encode()).hexdigest()
        directory = self._condition_dir(condition)
        for path in sorted(directory.glob("repeat-*"), reverse=True) if directory.exists() else []:
            summary_path = path / "summary.json"
            manifest_path = path / "manifest.json"
            if not summary_path.exists() or not manifest_path.exists():
                continue
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if summary.get("status") == "COMPLETED" and manifest.get("configFingerprint") == selected:
                return int(path.name.split("-")[-1]), path, summary
        return None

    def execute_session(self, session: int, blocks: int) -> dict:
        session_state = next(
            (item for item in self.state["sessions"] if item["session"] == session), None
        )
        if session_state is None:
            baseline = {
                condition: self._decision(condition)["validRuns"] for condition in CONDITIONS
            }
            session_state = {
                "session": session, "blocks": [], "status": "RUNNING", "baseline": baseline,
            }
            self.state["sessions"].append(session_state)
        baseline = session_state.setdefault(
            "baseline", {condition: 0 for condition in CONDITIONS}
        )
        completed_blocks = {
            item["block"] for item in session_state["blocks"] if item.get("status") == "COMPLETED"
        }
        self.state["status"] = "RUNNING"
        self._write()
        runner = Runner(self.root)
        for block in range(1, blocks + 1):
            if block in completed_blocks:
                continue
            global_block = (session - 1) * 5 + block
            order = block_order(global_block, self.state["seed"])
            block_state = next(
                (item for item in reversed(session_state["blocks"])
                 if item["block"] == block and item.get("status") != "COMPLETED"),
                None,
            )
            if block_state is None:
                block_state = {
                    "block": block, "globalBlock": global_block, "order": order,
                    "runs": [], "status": "RUNNING",
                }
                session_state["blocks"].append(block_state)
            self._write()
            completed_conditions = {
                item["condition"] for item in block_state["runs"]
                if item.get("status") == "COMPLETED"
            }
            assigned = {
                condition: sum(
                    1 for prior_block in session_state["blocks"]
                    for item in prior_block["runs"]
                    if item.get("condition") == condition and item.get("status") == "COMPLETED"
                )
                for condition in CONDITIONS
            }
            for condition in order:
                decision = self._decision(condition)
                new_valid_runs = decision["validRuns"] - baseline.get(condition, 0)
                if condition in completed_conditions or new_valid_runs <= assigned[condition]:
                    continue
                recovered = self._latest_selected_run(condition)
                if recovered is None:
                    continue
                repeat, run_dir, summary = recovered
                block_state["runs"].append({
                    "condition": condition,
                    "targetRps": CONDITIONS[condition],
                    "repeat": repeat,
                    "runDir": str(run_dir.relative_to(self.root)),
                    "status": summary["status"],
                    "validRuns": decision["validRuns"],
                    "decision": decision["decision"],
                    "recovered": True,
                })
                completed_conditions.add(condition)
                self._write()
            for condition in order:
                if condition in completed_conditions:
                    continue
                before = self._decision(condition)
                if before["decision"] != "CONTINUE":
                    block_state["runs"].append({
                        "condition": condition, "status": "SKIPPED",
                        "decision": before["decision"],
                    })
                    self._write()
                    continue
                repeat = self._next_repeat(condition)
                spec = self._formal_spec(condition)
                run_dir = runner._repeat(spec, repeat)
                summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
                after = self._decision(condition)
                block_state["runs"].append({
                    "condition": condition,
                    "targetRps": CONDITIONS[condition],
                    "repeat": repeat,
                    "runDir": str(run_dir.relative_to(self.root)),
                    "status": summary["status"],
                    "validRuns": after["validRuns"],
                    "decision": after["decision"],
                })
                self._write()
                if self.cooldown_seconds:
                    time.sleep(self.cooldown_seconds)
            block_state["status"] = "COMPLETED"
            self._write()
        session_state["status"] = "COMPLETED"
        decisions = {name: self._decision(name) for name in CONDITIONS}
        self.state["decisions"] = decisions
        self.state["status"] = (
            "COMPLETED"
            if all(item["decision"] != "CONTINUE" for item in decisions.values())
            else "SESSION_COMPLETED"
        )
        self._write()
        return self.state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--state", type=Path, default=Path("results/phase4-chain-baseline/state.json")
    )
    parser.add_argument("--session", type=int, required=True)
    parser.add_argument("--blocks", type=int, default=1, choices=range(1, 6))
    parser.add_argument("--cooldown-seconds", type=int, default=120)
    parser.add_argument("--run-id-prefix", default="phase4-chain-baseline")
    parser.add_argument("--profile", default="NO_MESH")
    args = parser.parse_args(argv)
    result = BaselineMeasurement(
        args.root.resolve(), args.state.resolve(), args.cooldown_seconds,
        run_id_prefix=args.run_id_prefix, profile=args.profile,
    ).execute_session(args.session, args.blocks)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
