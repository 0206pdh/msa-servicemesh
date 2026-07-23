from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

from experiments.analysis import analyze
from experiments.capacity import discovery_spec
from experiments.runner.cli import Runner


CONDITIONS = {"nominal": 8, "high": 17, "near-saturation": 22}
MINIMUM_REQUESTS = 20_000
MINIMUM_DURATION_SECONDS = 600
MAXIMUM_DURATION_SECONDS = 2_700


def measurement_duration(target_rps: int) -> int:
    required = math.ceil(MINIMUM_REQUESTS / target_rps)
    return min(MAXIMUM_DURATION_SECONDS, max(MINIMUM_DURATION_SECONDS, required))


def formal_spec(condition: str, target_rps: int) -> dict:
    spec = discovery_spec(f"phase4-chain-baseline-{condition}", target_rps)
    spec["seed"] = 42
    spec["timeSynchronized"] = True
    spec["loadProfile"].update({
        "warmupSeconds": 180,
        "durationSeconds": measurement_duration(target_rps),
        "minimumRequests": MINIMUM_REQUESTS,
        "repetitions": 1,
    })
    return spec


def block_order(block: int, seed: int = 42) -> list[str]:
    names = list(CONDITIONS)
    random.Random(seed + block).shuffle(names)
    return names


class BaselineMeasurement:
    def __init__(self, root: Path, state_path: Path, cooldown_seconds: int = 120):
        self.root = root
        self.state_path = state_path
        self.cooldown_seconds = cooldown_seconds
        self.state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {
            "scenario": "SYNC_CHAIN",
            "variant": "hop-3-payload-1KiB-delay-1ms",
            "profile": "NO_MESH",
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
        return self.root / "results" / f"phase4-chain-baseline-{condition}"

    def _next_repeat(self, condition: str) -> int:
        directory = self._condition_dir(condition)
        indices = []
        for path in directory.glob("repeat-*") if directory.exists() else []:
            try:
                indices.append(int(path.name.split("-")[-1]))
            except ValueError:
                continue
        return max(indices, default=0) + 1

    def _decision(self, condition: str) -> dict:
        directory = self._condition_dir(condition)
        return analyze(directory) if directory.exists() else {"validRuns": 0, "decision": "CONTINUE"}

    def execute_session(self, session: int, blocks: int) -> dict:
        session_state = next(
            (item for item in self.state["sessions"] if item["session"] == session), None
        )
        if session_state is None:
            session_state = {"session": session, "blocks": [], "status": "RUNNING"}
            self.state["sessions"].append(session_state)
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
            block_state = {
                "block": block, "globalBlock": global_block, "order": order,
                "runs": [], "status": "RUNNING",
            }
            session_state["blocks"].append(block_state)
            self._write()
            for condition in order:
                before = self._decision(condition)
                if before["decision"] != "CONTINUE":
                    block_state["runs"].append({
                        "condition": condition, "status": "SKIPPED",
                        "decision": before["decision"],
                    })
                    self._write()
                    continue
                repeat = self._next_repeat(condition)
                spec = formal_spec(condition, CONDITIONS[condition])
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
    args = parser.parse_args(argv)
    result = BaselineMeasurement(
        args.root.resolve(), args.state.resolve(), args.cooldown_seconds
    ).execute_session(args.session, args.blocks)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
