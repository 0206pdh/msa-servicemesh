# 계약 인덱스

계약이 구현보다 먼저 변경된다. breaking change는 version을 올리고 ADR과 migration 영향을 기록한다.

## OpenAPI

- [Data Plane API](openapi/mesh-benchmark-api.yaml): Chain, Fan-out, Target, Payload, Async publish와 smoke
- [Control Plane API](openapi/experiment-control-api.yaml): Run lifecycle, 결과 참조와 Fault

데이터면은 측정 경로이므로 인증·제어 호출을 섞지 않는다. 제어면은 bearer 인증과 별도 NetworkPolicy를 전제로 한다.

## Event

- [Benchmark Task v1](events/benchmark-task.v1.schema.json): Producer → Worker 명령
- [Benchmark Task Result v1](events/benchmark-task-result.v1.schema.json): Worker 처리 결과

## Result

- [Run Manifest v1](results/run-manifest.v1.schema.json): 변경 불가능한 실행 환경과 설정
- [Experiment Summary v1](results/experiment-summary.v1.schema.json): 파생 지표, 자원 분리와 원본 참조

## 호환성 규칙

- Event와 Result는 JSON Schema Draft 2020-12를 사용한다.
- 기존 required field의 삭제·의미·단위 변경은 새 major version이다.
- 필드 추가는 consumer가 unknown field를 처리할 수 있는지 확인한 뒤 진행한다.
- timestamp는 UTC RFC 3339, duration은 명시된 단위, byte는 raw byte를 사용한다.
- 결측값은 `null`로 보존하며 0으로 대체하지 않는다.
