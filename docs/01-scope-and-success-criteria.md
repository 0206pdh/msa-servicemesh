# 범위와 성공 기준

## 포함 범위

### Benchmark Workload

- 동기 chain과 hop 수 조절
- 병렬 fan-out과 부분 응답
- Kafka 기반 producer/worker와 backlog
- 설정 가능한 payload와 compression
- CPU, memory, I/O 부하 target
- delay, 5xx, connection reset, process failure 제어
- correlation/trace/experiment ID 전파

### 플랫폼

- VMware 1 control-plane + 2 worker Kubernetes
- Cilium/Hubble, MetalLB, Gateway API
- Prometheus/Grafana/Loki/Tempo/OpenTelemetry
- No Mesh, Sidecar, Ambient, Ambient + Waypoint
- k6, Chaos Mesh, Helm

### Performance Engineering

- 기준선과 포화점 탐색
- 병목 Evidence 수집
- 개선 가설과 단일 변수 실험
- 개선 전후 정량 비교
- 기능·관측성 손실과 자원 비용 평가
- 워크로드별 의사결정 Matrix

## 제외 범위

- 최종 사용자용 비즈니스 제품
- 모든 Service Mesh 제품 비교
- AWS/EKS와 관리형 서비스
- 하드웨어가 다른 결과의 직접 일반화
- 단일 echo 요청만으로 내리는 결론
- 프로덕션 SLA 인증 또는 보안 인증
- 수치를 좋게 만들기 위한 비현실적 기능 제거

## 최소 완료 기준

| 영역 | 기준 |
|---|---|
| Workload | chain, fan-out, async, payload 중 세 유형 이상이 재현 가능하다. |
| Profile | 네 profile을 같은 결과 schema로 측정한다. |
| Load | smoke, baseline, load, stress, spike, soak 중 필요한 profile을 자동 실행한다. |
| Fault | delay, error, Pod kill, network fault 중 세 종류 이상을 반복한다. |
| 공정성 | 이미지, replica, limit, node placement, 데이터와 부하 차이를 기록·통제한다. |
| 반복성 | 핵심 실험을 최소 3회 반복하고 분포와 이상치를 제공한다. |
| 병목 | 최소 세 개의 병목을 telemetry Evidence로 설명한다. |
| 개선 | 최소 세 개선안을 동일 조건으로 재측정한다. |
| Trade-off | 개선된 지표와 악화된 지표·기능 손실을 함께 기록한다. |
| 결정 | 워크로드별 profile/설정 선택과 rollback 조건을 제시한다. |
| 재현 | 새 환경에서 문서와 자동화로 핵심 결과를 재생성할 수 있다. |

## 핵심 지표

- 응답: throughput, p50/p95/p99, max latency, 오류율
- 자원: app/proxy/ztunnel/waypoint CPU, throttling, memory, network
- 확장: Pod startup, readiness, HPA convergence, node packing density
- 비동기: publish rate, consume rate, lag, backlog drain time, duplicate rate
- 회복: failure detection, downtime, recovery time, retry amplification
- 관측: trace coverage, dropped telemetry, ingest bytes, cardinality, storage
- 기능: mTLS 상태, L7 정책 적용, fault isolation, partial response rate

목표 수치는 Phase 4 No Mesh 기준선과 포화점 측정 후 확정한다.

## Definition of Done

- 모든 핵심 결과가 raw data → summary → graph → conclusion으로 연결된다.
- 환경·버전·commit/image digest·resource·부하·fault가 기록된다.
- 최소 3회 반복과 중앙값·분포·이상치가 제공된다.
- before/after는 하나의 독립 변수만 다르다.
- 개선 효과를 백분율뿐 아니라 절대값으로 표시한다.
- 실패하거나 악화된 개선도 보고서에 포함한다.
- Secret과 개인정보가 저장소와 결과에 포함되지 않는다.
