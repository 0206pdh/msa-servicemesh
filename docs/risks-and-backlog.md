# 위험과 백로그

| 위험 | 영향 | 완화 |
|---|---|---|
| VMware noisy neighbor | profile 차이 왜곡 | host 부하 기록, 반복, 가능하면 고정 배치 |
| Load generator 포화 | 가짜 처리량 한계 | 별도 VM/headroom metric |
| 관측 비용 | 대상 성능 왜곡 | 동일 설정 유지 후 별도 OBS 실험 |
| JIT/warm-up 차이 | 초기 run 편향 | 고정 warm-up과 JVM 상태 기록 |
| scheduling 차이 | node별 결과 왜곡 | affinity/placement와 node metric |
| profile 기능 불일치 | 공정하지 않은 비교 | 공통 기능 비교와 추가 기능 비용 분리 |
| Cilium/Istio 중복 | 정책·telemetry 혼선 | 책임표와 단일 owner |
| 너무 많은 변수 | 결론 불가 | 단계별 한 독립 변수 |
| 통계만 유의 | 실무 가치 없음 | 절대 차이와 비용/복잡도 포함 |
| benchmark 최적화 | 현실성 저하 | 여러 통신 패턴과 장애 사용 |

## 결정 대기

- Kubernetes: kubeadm/RKE2
- Gateway controller: Cilium/Istio
- Kafka 배포와 storage
- 부하 발생기 별도 VM 여부
- CPU pinning/VM reservation 가능 여부
- 결과 분석 도구와 graph 자동화
- trace sampling 기본값
- Waypoint 전체/선택 workload 범위

## 개선 후보 Backlog

- timeout/retry budget
- circuit breaker/bulkhead
- selected Waypoint
- proxy resources/concurrency
- OTel tail sampling/batch
- HPA CPU/RPS/lag
- MVC Virtual Threads/WebFlux
- HTTP/2 connection reuse
- compression/streaming
- Kafka partition/concurrency

실제 병목 Evidence가 생기기 전에는 후보를 구현하지 않는다.
