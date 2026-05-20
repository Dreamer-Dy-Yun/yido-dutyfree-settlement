# TODO: email_user_templates 300라인 초과 해소

## 참조 plan

- PLAN-20260520-backend-cleanup.md

## 목적

- `email_user_templates.py`가 빈 줄 포함 기준 300라인을 초과한 문제를 해소한다.

## 작업 범위

- 사용자 인증/환영 템플릿과 사용자 임시비밀번호/삭제 템플릿을 파일 단위로 분리한다.
- `service_email.py` import 경로만 새 파일 구조에 맞게 조정한다.

## 선행 조건

- TODO-014 review 보류 상태

## 수정 가능 파일

- `backend/WEB_SERVER/services/service_email.py`
- `backend/WEB_SERVER/services/email_user_templates.py`

## 생성 가능 파일

- `backend/WEB_SERVER/services/email_user_account_templates.py`
- `mulAg/review/REVIEW-017.md`

## 읽기 전용 파일

- `backend/WEB_SERVER/services/email_message_builder.py`
- `backend/WEB_SERVER/services/test_service_email.py`
- `mulAg/review/REVIEW-014.md`

## 수정 금지 파일

- `backend/WEB_SERVER/routers`
- `backend/WEB_SERVER/app.py`
- `backend/DATABASE`

## 입력

- `email_user_templates.py`의 verification/welcome/temp-password/deletion builder
- QA 보류 사유: `email_user_templates.py` 300라인 초과

## 출력

- 300라인 이하의 `email_user_templates.py`
- 300라인 이하의 `email_user_account_templates.py`
- import 경로가 보정된 `service_email.py`
- `REVIEW-017.md`

## 작업 단계

- [ ] 1. temp-password/deletion builder를 `email_user_account_templates.py`로 이동한다.
- [ ] 2. `email_user_templates.py`에는 verification/welcome builder만 남긴다.
- [ ] 3. `service_email.py` import를 새 파일 구조에 맞게 조정한다.
- [ ] 4. `ReadAllLines` 기준으로 관련 파일이 각각 300라인 이하인지 확인한다.

## 완료 기준

- `email_user_templates.py`와 `email_user_account_templates.py`가 각각 300라인 이하.
- 기존 `EmailService` 공개 API/체이닝/send 위치가 유지됨.
- TODO-014 QA 보류 사유가 해소됨.

## 주의사항

- 메일 본문 의미를 임의로 줄이거나 삭제하지 않는다.
- 기존 mojibake 문자열 수정은 별도 인코딩/문구 정리 TODO로 분리한다.
