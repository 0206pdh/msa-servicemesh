# Phase 상세화와 API 계약 완성

- Status: validated
- Date: 2026-07-22
- Scope: documentation and contracts only
- Related ADR: ADR-0020, ADR-0021, ADR-0022

## 변경 근거

구현 전에 실험의 진입/종료 조건과 서비스 간 계약을 고정해야 profile별 구현 차이와 결과 선택 편향을 줄일 수 있다. 데이터면과 제어면을 분리해 제어 호출이 측정 표본에 섞이지 않도록 한다.

## 산출물

- Phase 0~11 독립 실행 문서
- Chain, Fan-out, Target, Payload, Async publish Data Plane OpenAPI
- Run lifecycle, result reference, invalidation, Fault Control Plane OpenAPI
- Task/Task Result event schema
- Run Manifest와 Experiment Summary schema
- 계약 인덱스와 호환성 규칙

## 검증

- Redocly recommended lint: OpenAPI 2개 오류/경고 없이 통과
- AJV Draft 2020-12 compile: JSON Schema 4개 통과
- Markdown 상대 링크 검사 통과
- 상세 Phase 파일 수: 12

## 한계

- 계약은 구현되지 않았으며 실제 요청/응답 호환성 테스트 전이다.
- Control Plane bearer 인증의 issuer, audience와 권한 모델은 플랫폼 구현 전에 별도 ADR이 필요하다.
- `workloadConfig`와 일부 플랫폼 inventory는 Scenario 확장성을 위해 열린 object이며 구현 시 typed 하위 schema로 점진적으로 좁힌다.
