# YIDO.DUTYFREE 프로젝트 아키텍처 설계 문서

## 1. 프로젝트 개요

### 1.1 프로젝트 목적
본 프로젝트는 **영수증과 여권 이미지로부터 추출한 정보**를 각 **면세점 정보와 비교**하고, **제공된 수수료 정보와 매핑**하여 계산된 결과를 **수수료 수령증과 데이터**로 제공하는 것을 목적으로 합니다.

### 1.2 주요 기능
- **이미지 OCR 처리**: 영수증 및 여권 이미지에서 정보 추출
- **데이터 검증**: OCR 결과의 정확성 검증 및 수동 보정
- **면세점 정보 매칭**: EDI 데이터와 OCR 결과 비교 및 매칭
- **수수료 계산**: 매칭된 데이터 기반 수수료 계산
- **수령증 생성**: 계산된 수수료 기반 수령증 및 리포트 생성

### 1.3 기술 스택
- **Backend**: FastAPI (Python)
- **Frontend**: React (Vite)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (Async)
- **인증**: JWT
- **이메일**: SMTP
- **LLM**: ChatGPT API (OCR 보조)

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌─────────────────┐
│   React Client  │
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/HTTPS
         │
┌────────▼────────┐
│   FastAPI       │
│   (Backend)     │
│  - Routers      │
│  - Services     │
│  - Auth         │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│ Main  │ │ Tenant  │
│  DB   │ │ Schemas │
└───────┘ └─────────┘
```

### 2.2 레이어 구조

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│  (Routers: router_auth, etc.)       │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│         Business Logic Layer        │
│  (Services: service_email, etc.)    │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│         Data Access Layer           │
│  (Repositories: UserRepository,    │
│   TenantRepository, etc.)           │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│         Database Layer              │
│  (Models: BaseModel, etc.)          │
└─────────────────────────────────────┘
```

---

## 3. 데이터베이스 설계

### 3.1 데이터베이스 전략

#### 3.1.1 메인 데이터베이스 (Main DB)
- **목적**: 공통 데이터 및 시스템 관리 데이터 저장
- **저장 데이터**:
  - 사용자 정보 (User)
  - 테넌트 정보 (Tenant)
  - 권한 및 역할 (Role, Permission)
  - 프롬프트 이력 (Prompt)
  - EDI 원본 데이터 (EdiSilla, EdiLotte)
  - LLM 사용 로그 (LlmUsage)

#### 3.1.2 테넌트별 스키마 (Tenant Schemas)
- **전략**: 테넌트별로 독립적인 스키마 분리
- **목적**: 데이터 격리 및 확장성 확보
- **저장 데이터**:
  - 이미지 메타데이터 (Image)
  - OCR 결과 (OcrPassport, OcrReceipt)
  - 검증된 데이터 (VerifiedPassport, VerifiedReceipt)
  - 매칭된 데이터 (Matched)
  - 수수료 계산 결과
  - 테넌트별 설정

#### 3.1.3 스키마 분리 전략
```
PostgreSQL Database
├── public (Main Schema)
│   ├── tenant
│   ├── user
│   ├── role
│   ├── permission
│   ├── prompt
│   ├── edi_silla
│   ├── edi_lotte
│   └── llm_usage
│
└── tenant_{tenant_id} (Tenant Schemas)
    ├── image
    ├── ocr_passport
    ├── ocr_receipt
    ├── verified_passport
    ├── verified_receipt
    └── matched
```

### 3.2 주요 데이터 모델

#### 3.2.1 인증 및 권한 모델 (Main DB)
- **Tenant**: 테넌트(회사) 정보
- **User**: 사용자 정보
- **Role**: 역할 정보
- **Permission**: 권한 정보

#### 3.2.2 OCR 모델 (Tenant Schema)
- **OcrPassport**: 여권 OCR 결과
  - 여권번호, 이름, 생년월일, 만료일 등
  - 이미지 해시 (SHA-256)
  - 테넌트 ID (FK)
  
- **OcrReceipt**: 영수증 OCR 결과
  - 면세점 구분 (LOTTE, SILLA 등)
  - 영수증 번호, 그룹 번호
  - 여권번호, 구매자 이름
  - 이미지 해시 (SHA-256)
  - 테넌트 ID (FK)

#### 3.2.3 검증 모델 (Tenant Schema)
- **VerifiedPassport**: 검증된 여권 정보
  - OCR 결과를 기반으로 인간 작업자가 검증/수정
  - 복합 유니크: (nationality, passport_no, tenant_id)
  - 검증자 정보 (verifier_id, verifier_name)
  - 검증 플래그 (is_verified, is_corrected)

- **VerifiedReceipt**: 검증된 영수증 정보
  - OCR 결과를 기반으로 인간 작업자가 검증/수정
  - 복합 유니크: (dutyfree_company, receipt_no, tenant_id)
  - 검증자 정보 (verifier_id, verifier_name)
  - 검증 플래그 (is_verified, is_corrected)

#### 3.2.4 매칭 모델 (Tenant Schema)
- **Matched**: 여권-영수증 매칭 및 EDI 매칭 결과
  - 여권번호, 면세점 정보
  - 영수증 번호, 상품 정보
  - 매출액 정보 (USD, KRW)
  - 할인액, 포인트, 리베이트 금액
  - 매칭 여부 (is_matched)

#### 3.2.5 EDI 모델 (Main DB)
- **EdiSilla**: 신라면세점 EDI 원본 데이터
- **EdiLotte**: 롯데면세점 EDI 원본 데이터

#### 3.2.6 시스템 모델 (Main DB)
- **Prompt**: 사용된 프롬프트 이력 (SHA-256 해시로 유니크)
- **LlmUsage**: LLM 사용 로그

#### 3.2.7 이미지 메타데이터 모델 (Tenant Schema)
- **Image**: 이미지 파일 메타데이터
  - 이미지 해시 (SHA-256)
  - 이미지 경로
  - 파일 존재 여부
  - 테넌트 ID (FK)
  - 복합 유니크: (hash, company_id)

---

## 4. 비즈니스 프로세스

### 4.1 이미지 업로드 및 OCR 처리 플로우

```
1. 사용자 이미지 업로드
   │
   ├─► 이미지 해시 생성 (SHA-256)
   │
   ├─► Image 테이블에 메타데이터 저장 (Tenant Schema)
   │
   └─► LLM/OCR 서비스 호출
       │
       ├─► 여권 이미지 → OcrPassport 저장 (Tenant Schema)
       │
       └─► 영수증 이미지 → OcrReceipt 저장 (Tenant Schema)
```

### 4.2 데이터 검증 플로우

```
1. OCR 결과 조회
   │
   ├─► 작업자 검토
   │
   ├─► 데이터 수정 (필요시)
   │
   └─► VerifiedPassport/VerifiedReceipt 저장
       │
       └─► is_verified = True
           is_corrected = True (수정된 경우)
```

### 4.3 매칭 및 수수료 계산 플로우

```
1. VerifiedReceipt 조회
   │
   ├─► VerifiedPassport와 매칭 (여권번호 기준)
   │
   ├─► EDI 데이터 조회 (EdiSilla/EdiLotte)
   │
   ├─► 영수증 번호로 EDI 매칭
   │
   ├─► 매칭 결과를 Matched 테이블에 저장
   │
   └─► 수수료 정보 매핑 및 계산
       │
       └─► 수수료 수령증 생성
```

### 4.4 수수료 계산 로직

```
수수료 계산 = f(매칭된 데이터, 수수료 정책)
  │
  ├─► 면세점별 수수료 정책 조회
  │
  ├─► 상품 카테고리별 수수료율 적용
  │
  ├─► 매출액 기반 수수료 계산
  │
  └─► 수수료 수령증 생성 (Excel/PDF)
```

---

## 5. 프로젝트 구조

### 5.1 디렉토리 구조

```
YIDO.DUTYFREE/
├── WEB_SERVER/              # FastAPI 백엔드
│   ├── app.py               # FastAPI 앱 진입점
│   ├── routers/             # API 라우터
│   │   ├── router_auth.py  # 인증 라우터
│   │   └── router_registration.py  # 회원가입 라우터
│   ├── services/            # 비즈니스 로직
│   │   ├── service_email.py  # 이메일 서비스
│   │   └── verification_token.py  # 인증 토큰 서비스
│   └── auth/                # 인증 관련 모듈
│
├── DATABASE/                # 데이터베이스 레이어
│   ├── config.py           # DB 설정
│   ├── models/             # SQLAlchemy 모델
│   │   ├── base_model.py   # 기본 모델
│   │   ├── public_model.py  # Public 스키마 모델 (인증/권한)
│   │   └── tenant_model.py    # Tenant 스키마 모델
│   ├── repositories/       # 데이터 접근 레이어
│   │   └── authorities/    # 인증/권한 리포지토리
│   └── dbms/               # DBMS 구현체
│       └── postgre/        # PostgreSQL 관리자
│
├── FRONT_END/              # React 프론트엔드
│   ├── src/                # 소스 코드
│   └── public/             # 정적 파일
│
├── LLM/                    # LLM 통합
│   ├── llm.py              # LLM 서비스
│   └── dto.py              # 데이터 전송 객체
│
├── CUSTOMIZED/             # 커스텀 유틸리티
│   ├── cust_logger.py      # 로깅
│   ├── cust_hasher.py      # 해싱
│   └── ...
│
├── POC/                    # 프로토타입/테스트
│   └── yido_parser.py      # 파서 테스트
│
└── docs/                   # 문서
    └── ARCHITECTURE.md     # 본 문서
```

### 5.2 주요 컴포넌트

#### 5.2.1 라우터 (Routers)
- **router_auth.py**: 인증 관련 엔드포인트
  - 로그인, 로그아웃
  - JWT 토큰 발급/갱신
  - OAuth 연동 (Google 등)
  
- **router_registration.py**: 회원가입 관련 엔드포인트
  - 사용자 등록
  - 이메일 인증

#### 5.2.2 서비스 (Services)
- **service_email.py**: 이메일 발송 서비스
  - 인증 이메일 발송
  - 환영 이메일 발송
  
- **verification_token.py**: 이메일 인증 토큰 관리

#### 5.2.3 리포지토리 (Repositories)
- **UserRepository**: 사용자 데이터 접근
- **TenantRepository**: 테넌트 데이터 접근
- **RoleRepository**: 역할 데이터 접근
- **PermissionRepository**: 권한 데이터 접근

#### 5.2.4 데이터베이스 관리자
- **PGDBManager**: PostgreSQL 비동기 데이터베이스 관리
  - 연결 풀 관리
  - 트랜잭션 관리
  - 테이블 생성/삭제

---

## 6. 보안 및 인증

### 6.1 인증 방식
- **JWT (JSON Web Token)**: 사용자 인증 토큰
- **OAuth 2.0**: 소셜 로그인 (Google 등)
- **이메일 인증**: 회원가입 시 이메일 인증 필수

### 6.2 권한 관리
- **Role-Based Access Control (RBAC)**
  - 역할(Role) 기반 권한 관리
  - 권한(Permission) 세분화
  - 테넌트별 권한 격리

### 6.3 데이터 보안
- **테넌트 격리**: 스키마 분리로 데이터 격리
- **이미지 해싱**: SHA-256으로 이미지 무결성 검증
- **개인정보 마스킹**: OCR 결과에서 개인정보 마스킹 처리

---

## 7. 데이터 흐름

### 7.1 이미지 처리 파이프라인

```
이미지 업로드
    │
    ├─► 이미지 해시 생성
    │
    ├─► Image 테이블 저장 (Tenant Schema)
    │
    ├─► LLM/OCR 서비스 호출
    │   │
    │   ├─► 여권 이미지
    │   │   └─► OcrPassport 저장 (Tenant Schema)
    │   │
    │   └─► 영수증 이미지
    │       └─► OcrReceipt 저장 (Tenant Schema)
    │
    └─► LlmUsage 로그 저장 (Main DB)
```

### 7.2 검증 및 매칭 파이프라인

```
OCR 결과 조회
    │
    ├─► 작업자 검토
    │
    ├─► VerifiedPassport/VerifiedReceipt 저장
    │
    ├─► 여권-영수증 매칭
    │
    ├─► EDI 데이터 조회 (EdiSilla/EdiLotte)
    │
    ├─► 영수증 번호로 EDI 매칭
    │
    └─► Matched 테이블 저장
```

### 7.3 수수료 계산 파이프라인

```
Matched 데이터 조회
    │
    ├─► 수수료 정책 조회
    │
    ├─► 면세점별/카테고리별 수수료율 적용
    │
    ├─► 수수료 계산
    │
    └─► 수수료 수령증 생성 (Excel/PDF)
```

---

## 8. 확장성 고려사항

### 8.1 테넌트 확장
- **스키마 분리 전략**: 테넌트 추가 시 자동 스키마 생성
- **데이터 격리**: 테넌트별 완전한 데이터 격리
- **리소스 관리**: 테넌트별 리소스 할당 관리

### 8.2 성능 최적화
- **비동기 처리**: FastAPI 비동기 처리
- **연결 풀링**: 데이터베이스 연결 풀 관리
- **인덱싱**: 자주 조회되는 컬럼 인덱싱
- **캐싱**: 자주 조회되는 데이터 캐싱 (향후 Redis 도입 고려)

### 8.3 면세점 확장
- **EDI 파서 확장**: 새로운 면세점 EDI 포맷 추가 용이
- **플러그인 구조**: 면세점별 처리 로직 모듈화

---

## 9. 향후 개선 사항

### 9.1 기능 개선
- [ ] 수수료 정책 관리 시스템
- [ ] 실시간 알림 시스템
- [ ] 대시보드 및 리포트 기능 강화
- [ ] 배치 처리 시스템

### 9.2 기술 개선
- [ ] Redis 캐싱 도입
- [ ] 메시지 큐 도입 (Celery/RabbitMQ)
- [ ] 파일 스토리지 분리 (S3 등)
- [ ] 모니터링 시스템 구축

### 9.3 보안 강화
- [ ] API Rate Limiting
- [ ] 데이터 암호화 강화
- [ ] 감사 로그 시스템

---

## 10. 참고 사항

### 10.1 데이터베이스 마이그레이션
- **Alembic** 사용 (향후 구현)
- 테넌트 스키마 자동 생성/마이그레이션

### 10.2 환경 변수
- 데이터베이스 연결 정보
- SMTP 설정
- JWT 시크릿 키
- LLM API 키

### 10.3 로깅
- **CUSTOMIZED/cust_logger.py** 사용
- 구조화된 로깅
- 에러 추적

---

## 11. 용어 정의

- **테넌트 (Tenant)**: 독립적인 회사/조직 단위
- **OCR**: Optical Character Recognition (광학 문자 인식)
- **EDI**: Electronic Data Interchange (전자 데이터 교환)
- **스키마 (Schema)**: 데이터베이스 내 논리적 구조 단위
- **매칭 (Matching)**: 여권-영수증 또는 영수증-EDI 데이터 연결
- **수수료 (Commission)**: 거래 대가로 지급되는 수수료

---

**문서 버전**: 1.0  
**최종 수정일**: 2026.02.19  
**작성자**: Yun Dae-young
