# Experiment Runner

Phase 2의 비대화형 실행기다. `compose` adapter는 개발/E2E 검증 전용이고, 최종 성능 측정은 VMware Kubernetes에서 `kubernetes` adapter로 실행한다.

```powershell
python -m experiments.runner run experiments/specs/smoke-chain.json --repetitions 3
```

각 반복은 `results/<run-id>/repeat-XX/` 아래에 상태 이력, manifest, Ground Truth, k6 원본, summary와 보고서를 남긴다. 이미 존재하는 run 디렉터리는 덮어쓰지 않는다.
