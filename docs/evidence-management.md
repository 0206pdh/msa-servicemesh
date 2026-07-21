# Evidence 관리

## Evidence Chain

```text
Question
→ Hypothesis
→ ExperimentSpec
→ Run manifest/Ground Truth
→ Raw telemetry/load result
→ Derived summary/graph
→ Bottleneck claim
→ Improvement change
→ Before/after result
→ Conditional decision
```

중간 링크가 없는 결론은 validated로 표시하지 않는다.

## 상태

- planned: 질문과 방법만 존재
- implemented: workload/automation 존재
- validated: 기능과 수집 경로 검증
- measured: 반복 정량 결과 존재
- rejected: 가설 또는 개선이 지지되지 않음
- invalid: 환경/도구/cleanup 문제로 결과 사용 불가

## 저장 구조

```text
docs/evidence/
├── foundation/
├── infrastructure/
├── profiles/
└── improvements/
experiments/results/<run-id>/
├── manifest.json
├── ground-truth.json
├── raw/
├── summary.json
└── report.md
```

## Run 필수 항목

- UTC, commit, image digest, chart/tool version
- VM/node CPU·memory와 Kubernetes placement
- requests/limits, replica, HPA, JVM flags
- Mesh profile, mTLS, Waypoint 범위
- Workload config, seed, load profile
- fault schedule
- collector/load-generator headroom
- raw result path와 query
- invalidating factors

## 개선 Evidence

- baseline run IDs
- 병목 주장과 지지/반대 Evidence
- 한 가지 독립 변수와 diff
- 기대 지표, 회귀 지표, rollback threshold
- after run IDs
- 절대/상대 변화와 분포
- supported/rejected/inconclusive 결론

## 금지

- 평균만으로 결론
- 최선 run만 선택
- 서로 다른 이미지·부하의 직접 비교
- 누락값을 0으로 대체
- 결과가 나온 뒤 가설과 성공 기준 변경
- Secret, kubeconfig, 개인 데이터 저장
