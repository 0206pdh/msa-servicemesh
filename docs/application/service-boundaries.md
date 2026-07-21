# 서비스 경계

| 단위 | 책임 | 분리 이유 |
|---|---|---|
| benchmark-gateway | 외부 traffic 진입과 scenario routing | 인바운드 비용과 downstream 분리 |
| orchestrator-service | chain/fan-out, deadline, 부분 결과 | 동시성 모델과 resilience 정책 비교 |
| workload-service | 제어 가능한 target 작업 | 역할별 동일 이미지로 편향 감소 |
| producer-service | 메시지 생성과 발행 | 생산과 소비 scale 분리 |
| worker-service | 비동기 처리와 멱등성 | Pod 수 증가 비용과 backlog 실험 |
| experiment-runner | run lifecycle, 환경·부하·fault·결과 | 측정 대상과 제어 주체 분리 |
| web-console (선택) | 실행 상태/결과 조회 | 측정 경로 밖의 read-only 보조 UI |

## 데이터면

- `/workloads/chain`
- `/workloads/fanout`
- `/workloads/payload`
- Kafka benchmark topic

## 제어면

- run 생성·시작·종료
- immutable config 조회
- fault arm/disarm
- readiness와 cleanup 확인

제어면 호출은 latency 표본에서 제외하며 별도 network path와 metric prefix를 사용한다.
web-console은 실험 실행의 필수 의존성이 아니다. 모든 기능은 CLI/API로 먼저 제공하며 부하 생성은 k6가 담당한다.

## 재사용 정책

`workload-service`는 role/config로 여러 배포를 만든다. 동일 행위를 이름만 다른 서비스에 복사하지 않는다. 별도 서비스는 자원 모델, 프로토콜 또는 확장 축이 실제로 다를 때만 추가한다.
