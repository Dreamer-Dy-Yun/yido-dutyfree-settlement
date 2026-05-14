# YIDO 프로젝트 골격 (Project Skeleton)

다른 프로젝트의 뼈대 참고 또는 본 프로젝트 확장 시 활용하기 위한 **아키텍처·구조·구현 패턴** 요약.  
상세 API·테이블 목록은 제외하고, 레이어·진입점·확장 포인트 위주로 정리함.

---

## 1. 프로젝트 정체

- **도메인**: 멀티테넌트 B2C 웹 서비스 (구매대행, 면세점 EDI·데이터 매핑).
- **역할**: 시스템 관리자 / 테넌트(운영) 관리자 / 작업자.  
  인증은 JWT + Redis 세션, 시스템 관리자·일반 유저 토큰 분리(`admin_access_token` / `access_token`).

---

## 2. 실행 흐름 (진입점)

| 진입점 | 역할 |
|--------|------|
| **`main.py`** (루트) | `load_dotenv()` → `setup_db()` → `start_web_server()` → 종료 시 `db_manager.dispose_pool()`. |
| **`WEB_SERVER.main_web.start_web_server()`** | uvicorn으로 `WEB_SERVER.app:app` 기동. 호스트/포트/리로드는 환경변수. |
| **`WEB_SERVER.app:app`** | FastAPI 앱. lifespan에서 `db_manager.create_tables(schema="public")`, CORS·라우터 등록. |

- **개발 시**: `uvicorn WEB_SERVER.app:app --reload --port 10000` 직접 사용 가능.
- **DB 초기화**: `DATABASE.setup_db.setup_db()` → `db_manager.create_tables(schema="public")` (public 스키마만; 테넌트 스키마·테이블은 별도 프로비저닝).

---

## 3. 레이어 구조 (디렉터리 → 역할)

```
루트
├── main.py                    # 앱 메인: DB 설정 + 웹 서버 기동
├── WEB_SERVER/                # HTTP API 레이어 (FastAPI)
├── DATABASE/                  # DB 레이어 (모델, 엔진, 리포지토리)
├── LLM/                       # LLM 추상 + 구현 (ChatGPT 등)
├── PROCESSOR_DATA/            # EDI 파서·프로세서
├── PROCESSOR_IMAGE/           # 이미지 처리 (POC)
├── CUSTOMIZED/                # 프로젝트 공통 유틸 (로거, 데코, 엑셀 등)
├── FRONT_END/                 # React + Vite (admin / pages / services)
├── docs/                      # 설계·문서
└── nginx/                     # 배포용 Nginx·스크립트
```

- **실제 서비스 진입점**: `WEB_SERVER.app:app`.  
- **`app/`** (루트): 별도/레거시 구조로, 현재 메인 서버는 `WEB_SERVER` 사용.

---

## 4. WEB_SERVER (FastAPI 레이어)

- **`app.py`**: FastAPI 앱 생성, lifespan, CORS, `app.state.sessions`, 라우터 `include_router` (auth, company, tenant, system_admin).  
  prefix 예: `/api/auth`, `/api/tenant`, `/api/system-admin` 등.
- **`auth/`**: JWT 인코딩/디코딩, OAuth2 스킴, Redis 세션, 비밀번호 해시, Google OAuth, **의존성** (`get_current_user`, `get_current_tenant_admin`, `get_current_superuser`).  
  의존성에서 JWT + Redis 검증 후 `tenant_schema`를 담아 테넌트 스키마에서 User 조회하고, `user.tenant_schema`로 후속 라우터에 전달.
- **`routers/`**:  
  - **`settings.py`**: `get_db_manager`, `get_user_repository`, `get_tenant_repository` (모두 `lru_cache`).  
  - 라우터들은 이 의존성으로 DB/Repository 주입받고, 필요 시 `Depends(get_current_user)` 등으로 인증.
- **`services/`**: 이메일, 이미지 OCR, 검증 토큰 등 비즈니스 로직. `service.py`는 re-export 스텁.

**확장**: 새 라우터 추가 시 `app.py`에서 `include_router` 한 번 추가. 인증 필요 시 `Depends(get_current_user)` 등 사용.

---

## 5. DATABASE 레이어

### 5.1 구성 요소

| 요소 | 위치 | 역할 |
|------|------|------|
| **설정** | `config.py` | `PGDBManager` 인스턴스 생성 (환경변수: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_POOL_SIZE, DB_MAX_OVERFLOW). `UserRepository`, `TenantRepository` 인스턴스 생성. |
| **테이블 초기화** | `setup_db.py` | `setup_db()` → `db_manager.create_tables(schema="public")`. |
| **추상 DB 매니저** | `dbms/db_manager.py` | `DBManager`(ABC): `upsert_batch`, `update_batch`, `execute_query`, `open_session(schemas=...)`, `create_tables(schema=)`, `drop_tables(schema=)`, `convert_*_for_db` 등. |
| **PostgreSQL 구현** | `dbms/postgre/pg_manager.py` | `PGDBManager(DBManager)`: asyncpg, 비동기 엔진/세션, **스키마별 search_path** 지원. `create_tables(schema=)`로 스키마 지정 가능. |
| **모델** | `models/` | `base_model.py` → `BaseModel`. `public_model.py` → `BaseModelPublic` + public 스키마 테이블. `tenant_model.py` → tenant용 테이블 (스키마 미지정). `__init__.py`에서 통합 export. |
| **리포지토리** | `repositories/` | `BaseRepository(db_manager)`. `UserRepository`, `TenantRepository` 등. DB 접근 래퍼. |

### 5.2 스키마 전략

- **public 스키마**: 전역 데이터 (시스템 관리자, 테넌트 메타, 서비스 계정, LLM API 키, 프롬프트 등).  
  모델: `BaseModelPublic(BaseModel)` + `__table_args__ = {"schema": "public"}`.
- **tenant 스키마**: 테넌트별 데이터 (User, OCR/검증 테이블, EDI, 이미지, LLM 사용량 등).  
  모델: `BaseModel`만 상속, `__table_args__`에 스키마 없음.  
  **런타임에** `open_session(schemas=[tenant_schema, "public"])` 또는 `execute_query(..., schemas=[tenant_schema, "public"])`로 스키마 지정.

### 5.3 모델·리포지토리 확장

- **public 테이블 추가**: `BaseModelPublic` 상속, `public_model.py` 또는 별도 모듈에 정의 후 `create_tables(schema="public")`에 포함되도록 메타데이터 등록.
- **tenant 테이블 추가**: `BaseModel` 상속, `tenant_model.py` 등에 정의. 모든 DB 접근 시 `schemas=[tenant_schema, "public"]` 전달.
- **리포지토리 추가**: `BaseRepository(db_manager)` 상속, `config.py`에서 인스턴스 생성, 필요 시 `routers/settings.py`에 `get_*_repository` (lru_cache) 추가.

---

## 6. LLM 레이어

- **`llm.py`**: `LLM` 추상 클래스. `ask(request)`, `ask_stream` (선택), httpx 기반 HTTP 예외 → LLM 전용 예외로 변환.
- **`ChatGPT/api.py`**: `ChatGPT(LLM)` 구현. OpenAI Responses API, `LLMRequest`/이미지 base64/스트리밍 지원.
- **`dto.py`**, **`exceptions.py`**: 요청/응답 DTO, LLM 예외.
- **`prompt/`**: 프롬프트 텍스트 파일.

**확장**: 새 LLM 제공자 추가 시 `LLM` 상속 구현체 추가, API 키·모델 등은 public 또는 tenant 설정에서 로드.

---

## 7. 기타 모듈 (요약)

- **PROCESSOR_DATA**: EDI 파서(롯데/신라), 공통 EDI 프로세서, xlsx 패치 등.  
- **PROCESSOR_IMAGE**: 이미지 ZIP 처리 등 POC.  
- **CUSTOMIZED**: 로거, 재시도 데코레이터, 엑셀/웹 헬퍼 등.  
- **FRONT_END**: React + Vite. `src/admin`(시스템 관리자), `src/pages`, `src/services`, `src/components` 등.  
- **nginx**: Nginx 설정·배포 스크립트.

---

## 8. 환경·의존성

- **환경 변수**: 루트 `.env`. DB 접속, CORS_ORIGINS, 웹 서버 호스트/포트/리로드, Redis, JWT 등.
- **패키지**: 루트 `requirements.txt` (FastAPI, uvicorn, SQLAlchemy, asyncpg, pydantic, python-dotenv, jose, passlib, bcrypt, redis, httpx, pandas, openpyxl, pgvector 등). `pyproject.toml` 없음.

---

## 9. 확장 시 체크리스트

| 목적 | 위치·행동 |
|------|-----------|
| 새 API 그룹 추가 | `WEB_SERVER/routers/`에 라우터 작성 → `app.py`에서 `include_router` |
| 새 public 테이블 | `DATABASE/models/`에 `BaseModelPublic` 상속 모델 추가 → public 스키마 생성 시 자동 반영 |
| 새 tenant 테이블 | `DATABASE/models/`에 `BaseModel` 상속 모델 추가 → 모든 접근에 `schemas=[tenant_schema, "public"]` 사용 |
| 새 리포지토리 | `DATABASE/repositories/`에 `BaseRepository` 상속 → `config.py` 인스턴스 생성 → 필요 시 `routers/settings.py`에 getter 추가 |
| 새 인증 역할 | `auth/dependencies.py`에 새 의존성 함수 (예: `get_current_xxx`) 추가, JWT payload + Redis 검증 후 스키마·User 설정 |
| 새 LLM 백엔드 | `LLM/` 하위에 `LLM` 상속 클래스 구현 |

---

*문서 목적: 프로젝트 “뼈대”만 유지해 다른 프로젝트 참고 또는 본 프로젝트 기능 확장 시 일관된 패턴 적용.*
