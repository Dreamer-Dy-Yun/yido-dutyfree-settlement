# TODO: 경계 문서/README 동기화

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- 백엔드 라우터/서비스 분해 진행 결과를 문서에 반영해 향후 작업자와 LLM이 경계를 즉시 이해할 수 있게 한다.

## 작업 범위

- `MD/MODULE_BOUNDARIES.md` split candidates 및 하드닝 목록 업데이트.
- `backend/WEB_SERVER/routers/README.md`와 `backend/WEB_SERVER/services/README.md`의 Active Routers/Files 영역 반영.
- `mulAg/role-reference` 계열 문서의 plan 연결 상태 필요 시 추가 갱신.

## 선행 조건

- TODO-001~008 중 완료된 항목만 반영
- plan 상태가 `plan/done`이 아닌 경우에도 진행 중 상태에서 갱신 가능

## 수정 가능 파일

- `MD/MODULE_BOUNDARIES.md`
- `backend/WEB_SERVER/routers/README.md`
- `backend/WEB_SERVER/services/README.md`
- `mulAg/role-reference-map.md`
- `mulAg/orchestrator.md`
- `mulAg/sub-agent.md`
- `mulAg/qa.md`

## 생성 가능 파일

- 없음

## 읽기 전용 파일

- `mulAg/plan/active/PLAN-20260520-backend-cleanup.md`
- 현재 완료된 TODO 문서.

## 수정 금지 파일

- `frontend`
- `infra`
- `DATABASE` 핵심 스키마/마이그레이션 파일

## 입력

- 완료된 TODO 리스트와 review 상태
- 기존 경계 문서의 split candidates
- 라우터/서비스 새 파일 위치

## 출력

- 반영된 경계 문서 3~4개
- `mulAg` 규칙 문서간 참조 관계 변경사항 기록

## 작업 단계

- [ ] 1. 완료된 todo의 신규 라우터/서비스 파일명 반영.
- [ ] 2. split 완료/미완료 상태를 명시.
- [ ] 3. 하드닝 위반 위험 구간이 생기면 보완 안내 추가.
- [ ] 4. 변경 이력(요약) 추가.

## 완료 기준

- 문서에 현재 구조와 실제 파일 구조가 일치.
- 새 라우터/서비스 경로가 코드 변경 없이도 추적 가능.
- `todo`의 다음 단계에서 문서 수정 필요성이 없음이 확인.

## 주의사항

- 경계 문서는 기능 동작 상세 변경이 아닌 책임 경계 중심으로 기술.
- 문서가 오래되지 않도록 각 완료 단계마다 상태 갱신.

