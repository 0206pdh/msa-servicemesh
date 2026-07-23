# Canonical No Mesh baseline - session 1, block 2

- Completed: 2026-07-24 (Asia/Seoul)
- Profile: `NO_MESH`
- Scenario: `SYNC_CHAIN`, 3 hop, payload 1 KiB, fixed hop delay 1 ms
- Load-generator setting: 128 pre-allocated/max VUs for every condition
- Seed: 42
- Randomized order: near-saturation -> nominal -> high
- Block result: two valid runs and one invalid run

| Condition | Target | Repeat | Status | Samples | Achieved RPS | p95 ms | p99 ms | Node CPU peak | Load-generator CPU peak |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| near-saturation | 22 | 06 | `COMPLETED` | 20,218 | 22.001 | 38.349 | 57.902 | 37.40% | 6.36% |
| nominal | 8 | 02 | `COMPLETED` | 20,201 | 8.001 | 39.297 | 55.201 | 37.26% | 6.47% |
| high | 17 | 04 | `INVALID` | 20,213 | 17.001 | 40.132 | 54.243 | 39.53% | 5.08% |

## Invalid-run analysis

`high/repeat-04` met the load requirements: zero errors, zero interrupted
iterations, 20,213 samples, and 17.001 achieved RPS. It was excluded because
the preflight snapshot reported `WORKLOAD_NOT_READY`.

The snapshot showed that all seven pods on the synchronous request path were
Running and Ready. Only `kafka-0`, which is not used by `SYNC_CHAIN`, was
unready. The preflight and postflight snapshots both showed the same Kafka
state, and no measurement-path pod restart increased. Therefore this is a
false-positive environment gate, not a performance failure.

The runner was paused before block 3. The readiness and restart gates were
scoped to the seven `SYNC_CHAIN` request-path pod prefixes while retaining the
original all-pod behavior for other scenarios. The original repeat-04 artifact
was not modified or reclassified. It remains an invalid run and will be
replaced by a later valid repetition.

Regression verification:

- `python -m unittest discover -s experiments -p 'test_*.py'`: 19 tests passed
- repeat-04 preflight evaluated by the corrected gate: no factors
- repeat-04 restart delta evaluated by the corrected gate: no factors

## Evidence integrity

- `results/phase4-chain-baseline-near-saturation/repeat-06/summary.json`
  - SHA-256 `AB6815E5C19B6FC8DDADC8FA76A300F8C7E2998BAFB162BA589A3C9D43931F01`
- `results/phase4-chain-baseline-nominal/repeat-02/summary.json`
  - SHA-256 `2EE90DA1F6C2AE2BDBFCF2E4C10BC8DA73E61642F5B5D7738404EB49AE5F1FF6`
- `results/phase4-chain-baseline-high/repeat-04/summary.json`
  - SHA-256 `BF6153816B9B6937E21926F03808D0A773C0DAD6202801A0D1690BF30563CBB3`

After block 2, selected valid-run counts are 2/2/1 for 22/8/17 RPS.
All conditions remain `CONTINUE`; the minimum is 10 valid runs per condition.

