# ADR-0020: Service Mesh Performance Engineering 프로젝트

- 상태: accepted
- 날짜: 2026-07-22
- supersedes: 비즈니스 제품 및 SRE 제품 중심 방향

## Context

외부 API 제약이 있는 도메인이나 MSA를 정당화하기 위한 제품을 만들면 핵심 목표인 Mesh 비교와 개선이 흐려진다.

## Decision

프로젝트 목적을 Service Mesh의 성능·자원·회복탄력성 비교와 Evidence 기반 개선으로 명시한다. Java MSA는 통신 패턴을 재현하는 Benchmark Workload이며 최종 산출물은 반복 가능한 suite, before/after 데이터와 선택 Matrix다.

## Consequences

- 제품 기능 평가는 범위에서 제외한다.
- 실험 공정성, 자동화, 통계와 환경 기록의 요구 수준이 높아진다.
- 결과를 다른 환경에 보편적으로 일반화하지 않는다.

## Validation

네 profile 비교, 세 병목 설명, 세 개선안 재측정과 새 환경 재현을 완료 조건으로 한다.
