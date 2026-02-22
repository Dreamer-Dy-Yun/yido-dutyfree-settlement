# 인증 및 회원가입 프로세스 설계 문서

## 1. 개요

본 문서는 YIDO.DUTYFREE 프로젝트의 로그인 및 회원가입 프로세스에 대한 상세 설계를 다룹니다.

---

## 2. 로그인 프로세스

### 2.1 로그인 화면

사용자는 로그인 화면에서 다음 정보를 입력합니다:
- **이메일 주소**: 사용자 계정 이메일
- **비밀번호**: 사용자 비밀번호

로그인 성공 시 JWT 토큰이 발급되며, 이후 API 요청 시 인증에 사용됩니다.

---

## 3. 신규가입 프로세스

### 3.1 전체 프로세스 흐름

```
로그인 화면
    │
    └─► 신규가입 선택
            │
            ├─► 신규 회사(여행사) 선택
            │       │
            │       ├─► 미등록 회사
            │       │   └─► 신규 회사 등록
            │       │       └─► 서비스 제공사 검토 대기
            │       │
            │       └─► 기등록 회사
            │           └─► 회사 선택
            │
            ├─► 신규가입 양식 작성
            │
            ├─► 이메일 인증
            │
            └─► 이메일 인증 완료
```

### 3.2 신규 회사(여행사) 선택

#### 3.2.1 미등록 회사: 신규 회사 등록

**프로세스:**
1. 사용자가 "신규 회사 등록" 선택
2. 회사 등록 양식 작성 및 제출
3. 서비스 제공사 검토 대기 상태로 등록
4. 서비스 제공사 관리자가 검토 후 승인/거부 처리
5. 승인 완료 시 해당 회사가 기등록 회사 목록에 추가됨

**등록 양식:**
- **회사명** ※ 필수
- **회사 별칭** (선택)
- **사업자 번호** ※ 필수
- **대표 번호** ※ 필수
- **대표 모바일 번호(인증용)** ※ 필수
- **대표 번호(연락용)** (선택)

**데이터베이스 처리:**
- 테넌트(Tenant) 레코드 생성
- `is_active = False` 상태로 생성 (검토 대기)
- 테넌트별 스키마 생성 준비 (승인 후 생성)
- 서비스 제공사 관리자에게 알림 발송

**주의사항:**
- 미등록 회사는 서비스 제공사의 검토 후 등록됩니다
- 검토 완료 전까지는 해당 회사로 가입할 수 없습니다
- 테넌트당 독립적인 스키마로 작성됩니다

#### 3.2.2 기등록 회사: 회사 선택

**프로세스:**
1. 사용자가 기등록 회사 목록에서 회사 선택
2. 선택한 회사로 신규가입 진행
3. 각 테넌트의 관리자가 가입 승인 처리
4. 승인 완료 시 사용자 계정 활성화

**등록 양식:**
- **회사명** ※ 필수 (선택한 회사명 자동 입력)
- **회사 별칭** (선택)
- **사업자 번호** ※ 필수
- **대표 번호** ※ 필수
- **대표 모바일 번호(인증용)** ※ 필수
- **대표 번호(연락용)** (선택)

**데이터베이스 처리:**
- 선택한 테넌트 ID로 사용자(User) 레코드 생성
- `is_active = False` 상태로 생성 (테넌트 관리자 승인 대기)
- 해당 테넌트 관리자에게 가입 신청 알림 발송

**주의사항:**
- 각 가입 승인은 각 테넌트가 각자의 관리 화면에서 처리합니다
- 테넌트 관리자가 승인하기 전까지는 로그인할 수 없습니다
- 승인 거부 시 사용자에게 이메일로 통지됩니다

### 3.3 신규가입 양식

**사용자 정보:**
- **사용자명 (Username)** ※ 필수
- **이메일 주소** ※ 필수
- **비밀번호** ※ 필수
- **비밀번호 확인** ※ 필수
- **이름 (Full Name)** (선택)

**회사 정보:**
- 위 3.2.1 또는 3.2.2의 등록 양식 참조

### 3.4 이메일 인증

**프로세스:**
1. 신규가입 양식 제출 완료
2. 시스템이 인증 토큰 생성 및 저장
3. 인증 이메일 발송
   - 이메일 제목: `[구매대행B2C] 이메일 인증을 완료해주세요`
   - 인증 링크 포함
   - 만료 시간: 12시간
4. 사용자가 이메일의 인증 링크 클릭
5. 시스템이 토큰 검증 및 사용자 활성화

**인증 이메일 내용:**
- 사용자명 표시
- 인증 링크 버튼
- 만료 시간 안내
- 자동 발송 안내

**데이터베이스 처리:**
- `verification_token` 테이블에 토큰 저장
- 사용자(User) 레코드의 `is_active = False` 유지
- 토큰 만료 시간 설정 (기본 12시간)

### 3.5 이메일 인증 완료

**프로세스:**
1. 사용자가 인증 링크 클릭
2. 시스템이 토큰 검증
   - 토큰 유효성 확인
   - 만료 시간 확인
   - 이메일 일치 확인
3. 사용자 계정 활성화
   - `is_active = True`로 변경
   - 인증 토큰 삭제
4. 환영 이메일 발송
5. 로그인 가능 상태로 변경

**환영 이메일 내용:**
- 사용자명 표시
- 이메일 인증 완료 안내
- 서비스 이용 안내

**데이터베이스 처리:**
- 사용자(User) 레코드의 `is_active = True`로 업데이트
- `verification_token` 레코드 삭제
- 환영 이메일 발송 로그 기록

---

## 4. 데이터베이스 스키마

### 4.1 테넌트(Tenant) 모델

**Main DB (public 스키마)**

```sql
tenant
├── id (BigInteger, PK)
├── name (String(100), UNIQUE, NOT NULL)  -- 회사명
├── description (Text, NULLABLE)  -- 회사 설명
├── is_active (Boolean, NOT NULL, DEFAULT True)  -- 활성화 여부
├── business_number (String(20), NULLABLE)  -- 사업자 번호
├── representative_phone (String(20), NULLABLE)  -- 대표 번호
├── representative_mobile (String(20), NULLABLE)  -- 대표 모바일 번호(인증용)
├── contact_phone (String(20), NULLABLE)  -- 대표 번호(연락용)
├── company_alias (String(100), NULLABLE)  -- 회사 별칭
├── created_at (DateTime)
└── updated_at (DateTime)
```

**상태 관리:**
- `is_active = False`: 서비스 제공사 검토 대기 (미등록 회사)
- `is_active = True`: 승인 완료, 정상 운영

### 4.2 사용자(User) 모델

**Main DB (public 스키마)**

```sql
user
├── id (BigInteger, PK)
├── username (String(100), UNIQUE, NOT NULL)
├── email (String(255), UNIQUE, NOT NULL)
├── hashed_password (String(255), NOT NULL)
├── full_name (String(100), NULLABLE)
├── tenant_id (BigInteger, FK -> tenant.id, NOT NULL)
├── is_active (Boolean, NOT NULL, DEFAULT False)  -- 이메일 인증 + 테넌트 승인 완료 시 True
├── is_superuser (Boolean, NOT NULL, DEFAULT False)
├── created_at (DateTime)
└── updated_at (DateTime)
```

**상태 관리:**
- `is_active = False`: 
  - 이메일 인증 미완료
  - 또는 테넌트 관리자 승인 대기
- `is_active = True`: 
  - 이메일 인증 완료
  - 테넌트 관리자 승인 완료
  - 로그인 가능

### 4.3 인증 토큰(VerificationToken) 모델

**Main DB (public 스키마)**

```sql
verification_token
├── id (BigInteger, PK)
├── email (String(255), NOT NULL, INDEX)
├── token (String(255), UNIQUE, NOT NULL, INDEX)
├── user_id (BigInteger, FK -> user.id, NOT NULL)
├── expires_at (DateTime, NOT NULL)
├── created_at (DateTime)
└── updated_at (DateTime)
```

---

## 5. API 엔드포인트

### 5.1 회원가입 관련

#### 5.1.1 신규 회사 등록
```
POST /api/registration/register-company
```

**요청 본문:**
```json
{
  "company_name": "회사명",
  "company_alias": "회사 별칭",
  "business_number": "사업자 번호",
  "representative_phone": "대표 번호",
  "representative_mobile": "대표 모바일 번호",
  "contact_phone": "연락용 번호"
}
```

**응답:**
```json
{
  "message": "회사 등록이 완료되었습니다. 서비스 제공사 검토 후 승인됩니다.",
  "company_id": 123,
  "status": "pending_review"
}
```

#### 5.1.2 기등록 회사 목록 조회
```
GET /api/registration/companies?skip=0&limit=100
```

**응답:**
```json
{
  "companies": [
    {
      "id": 1,
      "name": "회사명",
      "company_alias": "회사 별칭",
      "is_active": true
    }
  ],
  "total": 50
}
```

#### 5.1.3 신규가입
```
POST /api/registration/register
```

**요청 본문:**
```json
{
  "username": "사용자명",
  "email": "user@example.com",
  "password": "비밀번호",
  "full_name": "이름",
  "company_id": 123,  // 기등록 회사 선택 시
  "company_name": "회사명",  // 미등록 회사 등록 시
  "company_alias": "회사 별칭",
  "business_number": "사업자 번호",
  "representative_phone": "대표 번호",
  "representative_mobile": "대표 모바일 번호",
  "contact_phone": "연락용 번호"
}
```

**응답:**
```json
{
  "message": "회원가입이 완료되었습니다. 이메일을 확인하여 인증을 완료해주세요.",
  "username": "사용자명",
  "email": "user@example.com",
  "company_name": "회사명"
}
```

#### 5.1.4 이메일 인증
```
GET /api/registration/verify-email?token={token}&email={email}
```

**응답:**
```json
{
  "message": "이메일 인증이 완료되었습니다",
  "verified": true,
  "email": "user@example.com"
}
```

### 5.2 테넌트 관리자 관련

#### 5.2.1 가입 신청 목록 조회
```
GET /api/tenant/pending-users?skip=0&limit=100
```

**인증:** 테넌트 관리자 권한 필요

**응답:**
```json
{
  "pending_users": [
    {
      "id": 456,
      "username": "사용자명",
      "email": "user@example.com",
      "full_name": "이름",
      "created_at": "2026-02-19T10:00:00Z"
    }
  ],
  "total": 10
}
```

#### 5.2.2 가입 승인
```
POST /api/tenant/approve-user/{user_id}
```

**인증:** 테넌트 관리자 권한 필요

**응답:**
```json
{
  "message": "사용자 가입이 승인되었습니다",
  "user_id": 456,
  "approved_at": "2026-02-19T10:30:00Z"
}
```

#### 5.2.3 가입 거부
```
POST /api/tenant/reject-user/{user_id}
```

**인증:** 테넌트 관리자 권한 필요

**요청 본문:**
```json
{
  "reason": "거부 사유"
}
```

**응답:**
```json
{
  "message": "사용자 가입이 거부되었습니다",
  "user_id": 456,
  "rejected_at": "2026-02-19T10:30:00Z"
}
```

### 5.3 서비스 제공사 관리자 관련

#### 5.3.1 미등록 회사 검토 목록
```
GET /api/admin/pending-companies?skip=0&limit=100
```

**인증:** 서비스 제공사 관리자 권한 필요

#### 5.3.2 회사 승인
```
POST /api/admin/approve-company/{company_id}
```

**인증:** 서비스 제공사 관리자 권한 필요

**응답:**
```json
{
  "message": "회사가 승인되었습니다",
  "company_id": 123,
  "schema_name": "tenant_123",
  "approved_at": "2026-02-19T10:30:00Z"
}
```

**처리 내용:**
- 테넌트 `is_active = True`로 변경
- 테넌트별 스키마 생성 (`tenant_{tenant_id}`)
- 테넌트별 테이블 생성 (ocr_passport, ocr_receipt, verified_passport, verified_receipt, matched, image)

#### 5.3.3 회사 거부
```
POST /api/admin/reject-company/{company_id}
```

**인증:** 서비스 제공사 관리자 권한 필요

**요청 본문:**
```json
{
  "reason": "거부 사유"
}
```

---

## 6. 프로세스 다이어그램

### 6.1 미등록 회사 가입 프로세스

```
사용자
    │
    ├─► 신규 회사 등록 양식 작성
    │
    ├─► 회사 정보 제출
    │
    ├─► 서비스 제공사 검토 대기
    │   │
    │   └─► [서비스 제공사 관리자]
    │       ├─► 검토
    │       │
    │       ├─► 승인 → 회사 활성화 + 스키마 생성
    │       │
    │       └─► 거부 → 사용자에게 통지
    │
    ├─► 승인 완료 후 사용자 정보 입력
    │
    ├─► 이메일 인증
    │
    └─► 로그인 가능
```

### 6.2 기등록 회사 가입 프로세스

```
사용자
    │
    ├─► 기등록 회사 선택
    │
    ├─► 사용자 정보 입력
    │
    ├─► 이메일 인증
    │
    ├─► 테넌트 관리자 승인 대기
    │   │
    │   └─► [테넌트 관리자]
    │       ├─► 검토
    │       │
    │       ├─► 승인 → 사용자 활성화
    │       │
    │       └─► 거부 → 사용자에게 통지
    │
    └─► 로그인 가능
```

---

## 7. 보안 고려사항

### 7.1 비밀번호 보안
- 비밀번호는 해싱하여 저장 (bcrypt 등)
- 최소 길이 및 복잡도 요구사항 적용

### 7.2 이메일 인증
- 인증 토큰은 암호화하여 저장
- 토큰 만료 시간 설정 (기본 12시간)
- 토큰은 일회용으로 사용 후 삭제

### 7.3 회사 정보 검증
- 사업자 번호 유효성 검증
- 중복 사업자 번호 확인
- 대표 모바일 번호 SMS 인증 (향후 구현)

### 7.4 권한 관리
- 테넌트 관리자 권한: 해당 테넌트 사용자 승인만 가능
- 서비스 제공사 관리자 권한: 모든 테넌트 승인 가능
- 일반 사용자: 자신의 정보만 조회/수정 가능

---

## 8. 향후 개선 사항

### 8.1 기능 개선
- [ ] 대표 모바일 번호 SMS 인증
- [ ] 사업자 번호 자동 검증 API 연동
- [ ] 회사 정보 수정 기능
- [ ] 비밀번호 재설정 기능

### 8.2 사용자 경험 개선
- [ ] 가입 진행 상태 표시
- [ ] 이메일 재발송 기능
- [ ] 가입 승인/거부 알림 개선

### 8.3 관리 기능 강화
- [ ] 테넌트 관리자 대시보드
- [ ] 서비스 제공사 관리자 대시보드
- [ ] 가입 통계 및 리포트

---

**문서 버전**: 1.0  
**최종 수정일**: 2026.02.19  
**작성자**: Yun Dae-young
