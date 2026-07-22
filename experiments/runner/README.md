# Experiment Runner

Phase 2의 비대화형 실행기다. `compose` adapter는 개발/E2E 검증 전용이고, 최종 성능 측정은 VMware Kubernetes에서 `kubernetes` adapter로 실행한다.

```powershell
python -m experiments.runner run experiments/specs/smoke-chain.json --repetitions 3
```

각 반복은 `results/<run-id>/repeat-XX/` 아래에 상태 이력, manifest, Ground Truth, k6 원본, summary와 보고서를 남긴다. 이미 존재하는 run 디렉터리는 덮어쓰지 않는다.

정식 steady-state 조건은 최소 10회 실행한 뒤 집계한다.

```powershell
python -m experiments.analysis results/<condition-run-id>
```

집계기는 run-level median의 10,000회 percentile-bootstrap 95% CI를 계산한다. p95와 CPU/request relative half-width 5%, p99 10%를 모두 만족하면 `STOP_PRECISION_REACHED`, 15회에도 만족하지 못하면 `INCONCLUSIVE_MAX_RUNS`를 반환한다. 부하와 반복 정책은 `experiments/design/phase4-measurement-policy.json`이 기준이다.
