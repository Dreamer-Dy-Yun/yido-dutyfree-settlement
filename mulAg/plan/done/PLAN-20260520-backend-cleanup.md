# PLAN: Backend Responsibility Refactoring (2026-05-20)

## 배경

- `backend/WEB_SERVER/routers/router_tenant.py`(2,535행), `backend/WEB_SERVER/routers/router_system_admin.py`(1,010행), `backend/WEB_SERVER/services/service_email.py`(1,336행) 등 핵심 모듈이 과도하게 응집되어 있습니다.
- 라우트 도메인과 서비스 책임이 혼재되어 변경·시험·리뷰 비용이 높아졌습니다.
- `MD/MODULE_BOUNDARIES.md`와 라우터/서비스 README에 분해 후보가 이미 기록되어 있으나 실제 실행 단위가 없습니다.
- 멀티 작업 규칙상 중복 파일 수정 충돌을 막기 위해 todo 단위를 더 작게 쪼갭니다.

## 목표

- 라우트/서비스 책임 경계를 분리한다.
- 사용자/도메인별로 라우트 파일을 분해한다.
- `service_email.py`를 계층별(계정 해석/템플릿/전송)로 분해한다.
- DB/모듈 경계 문서를 최신 상태로 유지한다.
- `hardening` 대상 모듈(이미 지정) 수정 시 명확한 리뷰 기준을 남긴다.

## 작업 범위

- 대상 루트: `D:\DEV\YIDO\backend`
- 우선 대상:
  - `backend/WEB_SERVER/routers`
  - `backend/WEB_SERVER/services`
  - `backend/WEB_SERVER/app.py`
  - `MD/MODULE_BOUNDARIES.md`
  - `backend/WEB_SERVER/routers/README.md`
  - `backend/WEB_SERVER/services/README.md`
- 비대상(이번 루틴):
  - `frontend`
  - `infra`
  - `legacy SQL scripts` (문헌화 없는 직접 변경 금지)

## 선행 조건

- 본 작업은 현재 브랜치에서 변경 전/후 문서 상태를 `mulAg`에 보존한다.
- todo는 `mulAg/todo`에 분리 후, 각 todo가 완료되면 `review` 문서를 통해 QA로 이동한다.
- 동일 파일 동시 수정은 금지한다.

## 완료 기준(전체)

- `plan/active/PLAN-20260520-backend-cleanup.md`에 대응하는 todo들이 모두 `done` 처리.
- 각 todo 완료 시 해당 범위의 review가 품질 기준 통과.
- plan 문서가 완료 후 `plan/done/`로 이동.

## 작업 분해

### 1차 정리군: 등록 라우터 정합성
- `backend/WEB_SERVER/router_registration.py`의 앱 등록 누락 해소
- 담당 todo: `TODO-001.md`

### 2차 정리군: `router_tenant.py` 도메인 분리
- 사용자/정보, EDI, 이미지-OCR/리뷰, 매칭, 검증/삭제/Usage로 분리
- 담당 todo: `TODO-002.md`, `TODO-003.md`, `TODO-004.md`, `TODO-005.md`, `TODO-006.md`

### 3차 정리군: `router_system_admin.py` 도메인 분리
- 대시보드, tenant lifecycle, service account, LLM key, prompt 관리로 분리
- 담당 todo: `TODO-007.md`, `TODO-008.md`

### 4차 정리군: `service_email.py` 구조 정리
- SMTP 계정 해석, 템플릿 빌드, 전송 래퍼 분리
- 담당 todo: `TODO-009.md`

### 5차 정리군: 문서/경계 정합성 정리
- `MD/MODULE_BOUNDARIES.md`, `backend/WEB_SERVER/routers/README.md`, `backend/WEB_SERVER/services/README.md` 갱신
- 담당 todo: `TODO-010.md`

## 리스크/유의점

- 라우트 분리 시 `app.py` 라우트 등록 순서 변화가 문서화되지 않으면 client측 의존성에 영향이 생길 수 있습니다.
- 내부 라우트 헬퍼(예: tenant schema 조회, 검증 행 병합)가 공통으로 쓰일 경우, 이동 순서와 import 경계를 명확히 합의해야 합니다.
- 인코딩이 깨진 주석/설명 문자열은 기능 변경 없이 정리 범위로 분리 처리합니다.
