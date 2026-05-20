# REVIEW: 인코딩 기준 고정

## 수행 일시

2026-05-20 13:47:55

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 참조한 todo

- TODO-010.md

## 수행 내용

- 프로젝트 루트에 `.editorconfig`를 추가해 신규 텍스트 파일의 기본 인코딩을 UTF-8로 고정했습니다.
- `mulAg/common-rules.md`에 PowerShell에서 한국어 파일을 읽을 때 `Get-Content -Encoding UTF8`을 사용한다는 기준을 추가했습니다.
- 깨져 보이는 출력과 실제 파일 손상을 구분하도록 UTF-8 유효성 확인 기준을 문서화했습니다.

## 변경 파일

- `mulAg/common-rules.md`

## 생성 파일

- `.editorconfig`

## 미변경 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/services/service_email.py`

## 검증 내용

- `git diff --check` 통과.
- `.editorconfig`, `mulAg/common-rules.md`, `backend/WEB_SERVER/app.py`가 엄격 UTF-8 디코딩 기준으로 유효함을 확인.
- `Get-Content -Encoding UTF8` 기준으로 `common-rules.md`의 한국어가 정상 표시됨을 확인.

## 남은 이슈

- `backend/WEB_SERVER/app.py`는 현재 작업트리에서 Git이 CRLF 변환 경고를 표시합니다. 이번 TODO에서는 줄바꿈 정책을 추가하지 않았으므로, 별도 줄바꿈 정규화 작업이 필요하면 별도 TODO로 분리해야 합니다.

## QA 확인 요청 사항

- `.editorconfig` 추가가 프로젝트 정책과 충돌하지 않는지 확인 요청.
- 기존 코드 파일의 한국어 문자열을 일괄 변환하지 않은 점이 이번 todo 범위에 맞는지 확인 요청.
