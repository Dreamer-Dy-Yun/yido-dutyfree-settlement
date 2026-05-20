# TODO: 인코딩 기준 고정

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- 백엔드 정리 중 PowerShell/도구 출력에서 한국어가 깨져 보이는 문제를 줄이기 위해 UTF-8 인코딩 기준을 명시한다.

## 작업 범위

- 프로젝트 루트의 텍스트 파일 기본 UTF-8 인코딩 기준을 `.editorconfig`로 고정한다.
- `mulAg/common-rules.md`에 Windows PowerShell 읽기 기준을 추가한다.

## 선행 조건

- 없음

## 수정 가능 파일

- `mulAg/common-rules.md`

## 생성 가능 파일

- `.editorconfig`

## 읽기 전용 파일

- `backend/WEB_SERVER/app.py`
- `backend/WEB_SERVER/routers/router_tenant.py`
- `backend/WEB_SERVER/routers/router_system_admin.py`
- `backend/WEB_SERVER/services/service_email.py`

## 수정 금지 파일

- `frontend`
- `infra`
- `backend/DATABASE`
- `backend/PROCESSOR_DATA`
- `backend/PROCESSOR_MATCHING`

## 입력

- UTF-8 유효성 확인 대상 파일
- Windows PowerShell `Get-Content` 기본 인코딩 차이

## 출력

- `.editorconfig`
- `mulAg/common-rules.md`

## 작업 단계

- [ ] 1. `.editorconfig`에 UTF-8 기준 추가.
- [ ] 2. `common-rules.md`에 PowerShell 읽기 기준 추가.
- [ ] 3. 변경 결과를 review로 기록.

## 완료 기준

- 새 텍스트 파일의 기본 charset이 UTF-8로 명시됨.
- PowerShell에서 한국어 파일을 읽을 때 `-Encoding UTF8` 사용 기준이 문서화됨.
- 기능 코드 변경 없이 인코딩 기준만 추가됨.

## 주의사항

- 기존 Python 소스의 문자열/주석을 일괄 변환하지 않는다.
- 깨져 보이는 출력과 실제 파일 손상을 구분해 기록한다.
