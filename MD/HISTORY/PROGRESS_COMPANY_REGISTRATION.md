# 회사 등록 및 메일 발송 기능 구현 진척 상황

## 📋 개요
신규 회사 등록 시 메일 발송 기능 및 관련 UI/UX 개선 작업 완료 내역

---

## ✅ 완료된 작업

### 1. 이메일 발송 서비스 확장 (`WEB_SERVER/services/service_email.py`)

#### 1.1 신규 회사 등록 안내 메일 템플릿
- **메서드**: `EmailService.set_company_registration_email()`
- **위치**: `service_email.py:264-458`
- **용도**: 회사 등록 신청 접수 시 회사 대표 이메일로 발송
- **내용**:
  - 회사명, 사업자번호(선택), 대표 연락처(선택) 표시
  - "내부 검토 후 승인 여부 안내 예정" 안내
  - HTML/텍스트 이중 형식 지원

#### 1.2 회사 등록 승인 메일 템플릿
- **메서드**: `EmailService.set_company_approval_email()`
- **위치**: `service_email.py:459-719`
- **용도**: 테넌트 승인 시 회사 대표 이메일로 발송
- **내용**:
  - 승인 완료 안내
  - 초기 관리자 계정 ID (대표 이메일)
  - 로그인 페이지 URL
  - "초기 비밀번호는 별도 안전 채널로 안내, 첫 로그인 후 변경 필요" 안내
  - HTML/텍스트 이중 형식 지원

#### 1.3 SMTP 계정 관리
- **함수**: `get_db_smtp_email_service(db: DBManager)`
- **위치**: `service_email.py:274-311`
- **동작**:
  1. `public.service_account` 테이블에서 `role='smtp_sender' AND is_active=True` 인 계정 조회
  2. 있으면 → 해당 계정의 `e_mail`/`password`로 `EmailService` 인스턴스 생성
  3. 없으면 → `None` 반환 (환경변수 기반 `email_service` fallback)

---

### 2. 회사 등록 API 개선 (`WEB_SERVER/routers/router_company.py`)

#### 2.1 요청 스키마 변경
- **변경 전**: `admin_email`, `admin_name` 필수 필드 포함
- **변경 후**: 관리자 정보 필드 제거, `email` 필드만 사용 (회사 대표 이메일)
- **추가**: `use_existing_if_pending: bool` 필드 (기존 미승인 테넌트 재사용 여부)

#### 2.2 스키마명 생성 로직 변경
- **변경 전**: 회사명 기반 (`company_name_lower_underscore`) + 중복 시 카운터 추가
- **변경 후**: UUID 기반 (`company_{UUID}`)
  - 예: `company_550e8400e29b41d4a716446655440000`
  - 충돌 확률 거의 없음 (UUID v4)
  - 문자로 시작해서 PostgreSQL 식별자 규칙 준수
  - 업데이트 단계 불필요 (한 번에 완성)

#### 2.3 사업자번호 중복 처리
- **이미 DB 생성된 테넌트**: 무조건 거부 (`400: 이미 등록된 사업자번호입니다`)
- **DB 미생성 테넌트 (승인 전)**:
  - 첫 시도: `400: 이미 등록된 사업자번호입니다. 계속 진행할까요?` (프론트에서 팝업 띄움)
  - `use_existing_if_pending=True` 재시도: 기존 테넌트 정보 업데이트 후 정상 처리

#### 2.4 메일 발송 통합
- **위치**: `router_company.py:185-196`
- **조건**: `company_data.email`이 있을 때만 발송
- **템플릿**: `set_company_registration_email()` 사용
- **SMTP 계정**: `get_db_smtp_email_service(db)` 우선, 없으면 환경변수 기반

---

### 3. 테넌트 승인 API 개선

#### 3.1 시스템 어드민 승인 API (`WEB_SERVER/routers/router_system_admin.py`)
- **엔드포인트**: `POST /api/system-admin/tenants/{tenant_id}/approve`
- **위치**: `router_system_admin.py:194-272`
- **동작**:
  1. 테넌트 스키마/DB 생성
  2. 임시 관리자 계정 생성 (이메일 = `tenant.email`, 랜덤 비밀번호 12자리)
  3. **승인 메일 발송** (`set_company_approval_email()`)
  4. 테넌트 활성화 (`is_active=True`)

#### 3.2 일반 관리자 승인 API (`WEB_SERVER/routers/router_admin.py`)
- **엔드포인트**: `POST /api/admin/tenants/{tenant_id}/approve`
- **위치**: `router_admin.py:78-157`
- **동작**: 시스템 어드민 API와 동일

#### 3.3 승인 메일 발송
- **수신자**: `tenant.email` (회사 대표 이메일)
- **내용**: 승인 완료 + 초기 관리자 계정 ID + 로그인 URL
- **비밀번호**: API 응답에만 포함 (시스템 어드민이 별도 채널로 전달)

---

### 4. 프론트엔드 UI 개선 (`FRONT_END/src/pages/CompanyRegisterPage.jsx`)

#### 4.1 폼 필드 제거
- **제거된 필드**: `admin_name`, `admin_email`
- **제거된 섹션**: "관리자 정보" 전체 섹션

#### 4.2 안내 문구 추가
- **위치**: 대표 이메일 레이블 하단
- **내용**: "이 메일로 승인 결과 및 초기 로그인 계정이 발송됩니다."
- **스타일**: 붉은색 강조 (`#dc2626`)

#### 4.3 중복 사업자번호 처리
- **모달 팝업**: `showDuplicateConfirm` state로 제어
- **메시지**: "이미 등록된 사업자 번호입니다. 계속 진행할까요?"
- **버튼**: "예, 계속 진행" / "아니오"
- **동작**:
  - "예" → `use_existing_if_pending: true`로 재시도
  - "아니오" 또는 바깥 클릭 → 모달만 닫히고 폼 상태 유지

#### 4.4 CSS 개선 (`CompanyRegisterPage.css`)
- **추가**: `.email-alert` 스타일 (붉은색 안내 문구)
- **제거**: `.form-section` 하단 보더 (버튼 위 선 중복 제거)

---

## 🔧 기술적 세부사항

### 스키마명 생성 전략
```
1. UUID v4 생성 (하이픈 제거) → 32자 hex 문자열
2. "company_" 접두어 추가 → "company_{UUID}"
3. PostgreSQL 스키마명으로 사용
   - 문자로 시작 → 식별자 규칙 준수
   - 충돌 확률 거의 없음 → while 루프 불필요
   - 한 번에 완성 → 업데이트 단계 제거
```

### 메일 발송 흐름
```
회사 등록 시:
  company_data.email → set_company_registration_email() → send()
  (smtp_sender 계정 사용)

테넌트 승인 시:
  tenant.email → set_company_approval_email() → send()
  (smtp_sender 계정 사용)
```

### SMTP 계정 우선순위
```
1. DB에서 smtp_sender 계정 조회 (get_db_smtp_email_service)
2. 없으면 환경변수 기반 email_service 사용
```

---

## ⚠️ 알려진 이슈

### SMTP 인증 실패
- **현상**: `SMTPAuthenticationError: (535, 'Username and Password not accepted')`
- **원인**: Gmail 계정의 일반 비밀번호 사용 (앱 비밀번호 필요)
- **해결 방법**:
  1. Gmail 2단계 인증 활성화
  2. 앱 비밀번호 생성
  3. `ServiceAccount.password` 또는 `SMTP_PASSWORD`에 앱 비밀번호 설정

---

## 📝 TODO / 향후 작업

### 완료된 항목
- ✅ 신규 회사 등록 안내 메일 템플릿
- ✅ 회사 등록 승인 메일 템플릿
- ✅ 프론트엔드 관리자 필드 제거
- ✅ 스키마명 UUID 기반 생성
- ✅ 사업자번호 중복 처리 (팝업 확인)

### 미완료 / 개선 필요
- ⚠️ SMTP 계정 설정 (Gmail 앱 비밀번호 필요)
- ⚠️ 첫 로그인 시 비밀번호/관리자 정보 변경 강제 플로우 (미구현)
- ⚠️ 거부 메일 템플릿 (TODO 주석만 있음)

---

## 📁 수정된 파일 목록

### 백엔드
- `WEB_SERVER/services/service_email.py` - 메일 템플릿 2개 추가
- `WEB_SERVER/routers/router_company.py` - 회사 등록 로직 개선
- `WEB_SERVER/routers/router_admin.py` - 승인 메일 발송 추가
- `WEB_SERVER/routers/router_system_admin.py` - 승인 메일 발송 추가

### 프론트엔드
- `FRONT_END/src/pages/CompanyRegisterPage.jsx` - 폼 필드 제거, 중복 확인 팝업 추가
- `FRONT_END/src/pages/CompanyRegisterPage.css` - 안내 문구 스타일 추가

---

## 🎯 핵심 변경사항 요약

1. **관리자 정보 입력 제거**: 회사 등록 시 관리자 이름/이메일 입력 불필요
2. **스키마명 UUID 기반**: `company_{UUID}` 형태로 충돌 걱정 없이 생성
3. **메일 발송 자동화**: 등록/승인 시 자동으로 회사 대표 이메일로 안내 메일 발송
4. **SMTP 계정 DB 관리**: `ServiceAccount` 테이블의 `smtp_sender` 계정으로 발송
5. **중복 사업자번호 처리**: 팝업으로 사용자 확인 후 기존 미승인 테넌트 재사용 가능

---

*작성일: 2026-02-25*
*마지막 업데이트: 회사 등록 및 승인 메일 발송 기능 완료*
