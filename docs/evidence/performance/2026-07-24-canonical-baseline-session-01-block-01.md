# Canonical No Mesh baseline — session 1, block 1

- Completed: 2026-07-24 (Asia/Seoul)
- Profile: `NO_MESH`
- Scenario: `SYNC_CHAIN`, 3 hop, payload 1 KiB, fixed hop delay 1 ms
- Final load-generator setting: 128 pre-allocated/max VUs for all conditions
- Seed: 42
- Randomized order: near-saturation → high → nominal
- Block result: all three runs `COMPLETED`, no invalidating factors

| Condition | Target | Selected repeat | Samples | Achieved RPS | p95 ms | p99 ms | Node CPU peak | Load-generator CPU peak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| near-saturation | 22 | 05 | 20,219 | 22.002 | 41.626 | 62.881 | 37.21% | 9.09% |
| high | 17 | 03 | 20,214 | 17.001 | 44.207 | 60.221 | 37.56% | 16.07% |
| nominal | 8 | 01 | 20,200 | 8.000 | 34.336 | 50.659 | 31.83% | 7.51% |

These are the first valid runs, not a final performance conclusion. Each condition requires at least 10 valid runs and bootstrap 95% CI precision checks. Earlier Docker-off, restart-gate, insufficient-VU, and superseded-fingerprint artifacts remain local but are excluded from the selected 128-VU statistics.

## Evidence integrity

- `results/phase4-chain-baseline-near-saturation/repeat-05/summary.json` — SHA-256 `37EEB513E306E02B95FC4CFCAAB78C602D6979632397C5CF3FB5A41C4B4407CE`
- `results/phase4-chain-baseline-high/repeat-03/summary.json` — SHA-256 `28366A822A386B30838E3C6539AF90DB0A26316FE9A07A3315F8DD66E6FA47F0`
- `results/phase4-chain-baseline-nominal/repeat-01/summary.json` — SHA-256 `30C2499A2D5ED9A49241AE8042183F55C7CD94919E6F46CEB1452FF66D3B942C`

Full runner artifacts remain in the ignored local `results/` tree.
