# 전체 아키텍처

## 구성

```text
External Load Generator
        │ k6 + run metadata
        ▼
benchmark-gateway
  ├── chain-service(role=a) → chain-service(role=b) → chain-service(role=c)
  ├── fanout-service → workload-target replicas
  ├── producer-service → Kafka → worker-service → result store
  └── payload-service → object/storage sink

Experiment Runner
  ├── applies Helm profile and fault
  ├── records Ground Truth and versions
  ├── queries Prometheus/Loki/Tempo/Hubble
  └── stores raw/summary/report
```

## 코드 모듈과 배포 단위

| 단위 | 책임 | 주요 설정 |
|---|---|---|
| benchmark-gateway | 외부 진입, scenario 선택, ID 전파 | route, deadline |
| orchestrator-service | chain/fan-out orchestration | fanout, parallelism, budget |
| workload-service | delay/error/CPU/memory/payload target | role, fault, response size |
| producer-service | 비동기 작업 발행 | batch, message size, rate |
| worker-service | 소비·처리·멱등성 | concurrency, processing cost |
| experiment-runner | 환경/부하/fault/결과 수집 | profile, run ID, variables |
| web-console (선택) | 실행 상태와 저장된 결과 조회 | 측정 경로 밖의 read-only 보조 도구 |

같은 `workload-service` 이미지를 역할과 설정을 바꿔 여러 hop/target으로 배포한다. 서비스 수를 늘리기 위한 복제 코드는 만들지 않는다.

## 실험 제어면과 데이터면

- 데이터면: 실제 측정 대상 요청과 이벤트
- 제어면: scenario/fault 설정, run lifecycle, 결과 metadata
- 제어 요청은 측정 트래픽과 별도 port/path 및 NetworkPolicy를 사용한다.
- 실험은 web-console 없이 CLI와 자동화만으로 실행·재현할 수 있어야 한다.
- 부하는 브라우저가 아니라 experiment-runner와 k6가 생성한다.
- 실험 중 설정 변경은 금지하고 run 시작 전에 snapshot을 저장한다.

## Profile

```text
no-mesh        Cilium only
sidecar        Istio sidecar injection
ambient        ztunnel enrollment
waypoint       ambient + selected waypoint
```

Gateway API controller와 workload Gateway는 profile 간 동일하게 유지하는 것을 원칙으로 한다. controller 자체 비교가 목적이면 별도 실험 ID를 사용한다.

## 결과 경로

```text
experiments/results/<run-id>/
├── manifest.json
├── ground-truth.json
├── k6-summary.json
├── prometheus/
├── traces/
├── logs/
├── hubble/
├── summary.json
└── report.md
```

## 실패 처리

- Workload fault와 플랫폼 오류를 다른 code로 기록한다.
- timeout/retry는 앱과 Mesh 중 소유자를 명시한다.
- 부하 발생기나 관측 스택이 포화되면 run을 invalid로 표시한다.
- 결과 누락을 0으로 대체하지 않는다.
- cleanup 실패 시 다음 run을 시작하지 않는다.
