# Benchmark Workload 설계

이 디렉터리의 “애플리케이션”은 사용자 제품이 아니라 실제 MSA 통신·동시성·장애 패턴을 재현하는 Java Benchmark Workload다. 측정 결과를 왜곡하지 않도록 기능은 작고 설정은 명시적이어야 한다.

## 문서

- [요구사항](requirements.md)
- [실험 도메인 모델](domain-model.md)
- [서비스 경계](service-boundaries.md)
- [제어·데이터 API](api-and-data.md)
- [Workload 개발 Phase](../phases/application-development.md)

## Scenario

- `SYNC_CHAIN`: 지정 hop 수만큼 순차 호출
- `FAN_OUT`: 여러 target을 순차 또는 병렬 호출
- `ASYNC_PIPELINE`: Kafka 발행과 worker 처리
- `PAYLOAD`: 크기와 compression에 따른 전송
- `MIXED_RESOURCE`: CPU/memory/I/O 제어 부하

## 원칙

- 모든 run은 immutable ExperimentSpec을 참조한다.
- Workload는 profile을 감지해 동작을 바꾸지 않는다.
- fault는 시간·강도·대상과 cleanup을 기록한다.
- 결과 payload와 business logic을 최소화하되 멱등성·부분 결과·deadline 같은 분산 시스템 의미는 구현한다.
- 제어 endpoint는 측정 경로에서 분리한다.
