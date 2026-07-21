# Phase 3 — 플랫폼 기반

## 목적

네 Mesh profile을 공정하게 배치하고 관측할 온프레미스 Kubernetes 기반을 만든다.

## 작업

1. VMware VM의 vCPU/memory/disk/NIC, NUMA, 전원 정책과 시간 동기화를 기록한다.
2. Kubernetes, Cilium/Hubble, MetalLB와 Gateway API를 설치하고 버전을 고정한다.
3. Prometheus, Grafana, Loki, Tempo와 OpenTelemetry Collector를 배포한다.
4. Helm chart와 profile별 values를 분리하고 공통 Workload image digest를 고정한다.
5. 측정 대상, 부하 발생기, 관측 스택의 노드/자원 경계를 정의한다.

## 검증과 Gate

- NetworkPolicy, DNS, Gateway, storage와 재부팅 후 복구 검증
- metric/log/trace/Hubble flow의 run ID 연결과 수집 손실률 확인
- node, collector, load generator headroom 기록
- 진입: Phase 2 자동화 계약 완료
- 종료: No Mesh dry-run이 telemetry completeness 기준 통과
