# Phase 6 — Istio Ambient

## 목적

Ambient의 노드 공유 ztunnel 비용 구조와 Sidecar 대비 확장 특성을 측정한다.

## 작업

1. namespace enrollment, HBONE 경로, mTLS와 ztunnel 배치를 검증한다.
2. ztunnel 자원을 노드와 해당 노드의 실험 트래픽에 귀속하는 규칙을 적용한다.
3. Pod/worker replica와 노드 수 증가에 따른 공유 비용을 측정한다.
4. L7 기능이 없는 기본 Ambient 범위를 Sidecar와 명시적으로 구분한다.

## 검증과 Gate

- 우회 경로가 없고 ztunnel metric/trace가 run과 연결됨
- 같은 image, load, placement에서 유효 run 최소 3회
- 진입: No Mesh와 Sidecar 측정 완료
- 종료: Ambient 비용 증가 형태와 기능 범위 Evidence `measured`
