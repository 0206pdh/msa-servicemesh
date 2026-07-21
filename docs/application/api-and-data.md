# 제어·데이터 API

## 데이터면

| Method | Path | 목적 |
|---|---|---|
| POST | `/api/v1/workloads/chain` | hop chain 실행 |
| POST | `/api/v1/workloads/fanout` | fan-out 실행 |
| POST | `/api/v1/workloads/payload` | payload 전송 실행 |
| POST | `/api/v1/workloads/target` | bounded target 작업 실행 |
| POST | `/api/v1/workloads/async/tasks` | Kafka task batch 발행 |
| GET | `/api/v1/system/ping` | 최소 연결 smoke |

요청은 `X-Experiment-Run-Id`, `X-Correlation-Id`와 선택적 deadline을 포함한다.

## 제어면

| Method | Path | 목적 |
|---|---|---|
| POST | `/control/v1/runs` | immutable run 생성 |
| POST | `/control/v1/runs/{id}/start` | warm-up/측정 시작 |
| POST | `/control/v1/runs/{id}/finish` | 수집과 종료 |
| POST | `/control/v1/runs/{id}/invalidate` | Evidence를 보존한 무효화 |
| GET | `/control/v1/runs/{id}` | config와 상태 조회 |
| GET | `/control/v1/runs/{id}/result` | summary와 raw artifact 위치 조회 |
| PUT | `/control/v1/runs/{id}/faults/{target}` | run에 속한 fault 설정 |
| DELETE | `/control/v1/runs/{id}/faults/{target}` | fault 해제 |

구현 전 제어면 인증과 NetworkPolicy를 확정한다.

정식 계약은 [Data Plane OpenAPI](../../contracts/openapi/mesh-benchmark-api.yaml), [Control Plane OpenAPI](../../contracts/openapi/experiment-control-api.yaml)와 [계약 인덱스](../../contracts/README.md)를 따른다.

## 오류 계약

```json
{
  "code": "TARGET_TIMEOUT",
  "message": "target did not respond within the remaining budget",
  "correlationId": "...",
  "experimentRunId": "...",
  "retryable": true,
  "target": "workload-b"
}
```

## 결과 데이터

- 시계열 원본은 Prometheus/Loki/Tempo/Hubble에 제한 기간 저장한다.
- 각 run 종료 시 필요한 범위를 파일로 export한다.
- summary는 원본 query와 시간 범위를 포함한다.
- 소수점 반올림 전 원본값을 보존한다.
- baseline과 after의 schema와 단위를 동일하게 유지한다.
