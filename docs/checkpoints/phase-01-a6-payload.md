# Checkpoint — `phase-01-a6-payload`

- Status: validated
- Updated at: 2026-07-22

## 목표

0~10MiB 결정론 payload의 크기·생성 방식·압축 비용을 독립적으로 비교한다.

## 완료 조건

- [x] 0~10MiB 경계와 seed 기반 byte 생성
- [x] buffered/chunked generation
- [x] identity/gzip
- [x] SHA-256와 optional body
- [x] 단위 테스트와 Gateway E2E

## 검증 결과와 해석 제한

- 1KiB gzip 요청: 논리 크기 1024와 SHA-256 응답 확인
- buffered와 chunked generation은 같은 seed에서 같은 byte/checksum을 생성
- v1 응답은 JSON/Base64 계약이므로 `STREAMING`은 생성 방식 비교다. 진짜 binary network streaming이라고 해석하지 않는다.
