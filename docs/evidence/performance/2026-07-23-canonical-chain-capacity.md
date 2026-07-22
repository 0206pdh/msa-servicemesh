# Canonical SYNC_CHAIN capacity discovery

- Date: 2026-07-23 (Asia/Seoul)
- Profile: `NO_MESH`
- Scenario: `SYNC_CHAIN`, 3 hop, payload 1 KiB, fixed hop delay 1 ms
- Policy: [ADR-0014](../../decisions/0014-measurement-repetition-and-load-policy.md)
- Result: usable capacity `C* = 28 RPS`
- Boundary: 28 RPS pass, 30 RPS capacity fail, relative interval width 7.14%
- Operating points: low 3, nominal 8, high 17, near-saturation 22 RPS

## Measurement results

| Target RPS | Phase | Outcome | Achieved RPS | Error | p95 ms | p99 ms | Decision |
|---:|---|---|---:|---:|---:|---:|---|
| 10 | geometric | PASS | 10.004 | 0% | 34.073 | 41.945 | low-load baseline |
| 20 | geometric | PASS | 20.004 | 0% | 30.311 | 46.767 | usable |
| 40 | geometric | CAPACITY_FAIL | 39.885 | 0% | 101.238 | 193.956 | dropped iterations, p99 ratio |
| 30 | refine | CAPACITY_FAIL | 30.002 | 0% | 68.965 | 118.975 | p99 ratio |
| 25 | refine | PASS | 25.003 | 0% | 54.793 | 80.406 | usable |
| 27 | refine retry-03 | PASS | 27.001 | 0% | 47.225 | 72.835 | usable |
| 28 | refine | PASS | 28.001 | 0% | 47.381 | 69.087 | usable, final C* |

The p99 ceiling was `2 × 41.945 = 83.890 ms`. The 30 RPS point exceeded it, while 28 RPS stayed below it. At 28 RPS, peak node CPU was 36.38%, load-generator CPU was 5.10%, and the minimum available memory across nodes was 2,079,956,992 bytes. Throughput, error, latency, node headroom, load-generator headroom, telemetry, and cleanup criteria all passed.

## Invalid runs and correction

Two earlier 27 RPS runs remain preserved but are excluded from the capacity boundary:

- `phase4-chain-capacity-refine-rps-00027`: `TEMPO_TRACE_MISSING`
- `phase4-chain-capacity-refine-rps-00027-retry-02`: `TEMPO_TRACE_MISSING`, `DIRTY_SOURCE_TREE`

The discovery implementation incorrectly treated any invalid point as a capacity failure. Commit `92ff0ea` introduced explicit `PASS`, `CAPACITY_FAIL`, and `INVALID` outcomes, retries invalid points without overwriting evidence, and prevents invalid points from becoming a capacity boundary.

Tempo was repeatedly `OOMKilled`: the chart supplied a 1024 MiB memory ballast while the container limit was 768 MiB. The final configuration uses a 128 MiB ballast and a 1536 MiB limit. The Tempo Pod returned to Ready with zero restarts, the OTel Collector was restarted to clear its saturated exporter queue, and a new trace completed an application-to-Tempo round trip. Commit `0f196ab` records the final resource setting.

## Evidence integrity

Full runner artifacts remain in the ignored local `results/` tree and are not rewritten or deleted.

- `results/phase4-chain-capacity/discovery.json` — SHA-256 `F40DF111EC758F4AB3EC953F9D1BDD0F99EDB1BA11FDB1617D94EC9550DAFC96`
- `results/phase4-chain-capacity-refine-rps-00027-retry-03/repeat-01/summary.json` — SHA-256 `020840871809A68C2983F4CB1E873A1A47381FE94DEED806E88B75A9F85EBE66`
- `results/phase4-chain-capacity-refine-rps-00028/repeat-01/summary.json` — SHA-256 `811365ED5947D20D370B72506FCCF9616E2A9E3482C65CBBC14CC69A17FCCFA0`

## Verification

- Python capacity, analysis, and runner tests: 10 passed
- Final discovery state: `COMPLETED`
- Final Tempo state during 28 RPS run: Ready, restart count 0
- 27 and 28 RPS final runs: `COMPLETED`, no invalidating factors
