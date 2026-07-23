# Phase 4 P3 checkpoint addendum - session 1 block 2

- Date: 2026-07-24
- Parent checkpoint: `phase-04-p3-canonical-formal-baseline.md`
- Status: in progress
- Randomized order: 22 -> 8 -> 17 RPS
- Selected valid-run counts after the block: 22/8/17 RPS = 2/2/1
- Decision for every condition: `CONTINUE`

The 22 RPS repeat-06 and 8 RPS repeat-02 runs completed without invalidating
factors. The 17 RPS repeat-04 run was excluded by `WORKLOAD_NOT_READY`.

The cause was a false-positive gate: unrelated `kafka-0` was not Ready while
all seven `SYNC_CHAIN` request-path pods were Running and Ready. The runner was
paused before block 3. The readiness and restart gates were scoped to the
synchronous request path, with all-pod behavior preserved for other scenarios.
Nineteen unit tests pass, including regressions proving that an unready Kafka
pod is ignored and an unready chain pod is still rejected.

The original invalid artifact is unchanged and remains excluded. Blocks 3-5
must provide a replacement 17 RPS run, followed by session 2 and any additional
session required to reach 10-15 valid runs and the bootstrap precision target.

Evidence:
[session 1 block 2](../evidence/performance/2026-07-24-canonical-baseline-session-01-block-02.md)
