# FastAPI Backend Template

FastAPI 기반 웹 서비스 백엔드 템플릿입니다.

## 주요 기능

- ✅ FastAPI 프레임워크
- ✅ SQLAlchemy ORM
- ✅ JWT 인증 시스템
- ✅ 데이터베이스 마이그레이션 (Alembic)
- ✅ 환경 변수 관리
- ✅ 에러 처리
- ✅ API 문서화 (자동 생성)
- ✅ 프로젝트 구조화

## 프로젝트 구조

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 설정 관리
│   ├── database.py          # 데이터베이스 연결
│   ├── models/              # SQLAlchemy 모델
│   ├── schemas/             # Pydantic 스키마
│   ├── api/                 # API 라우터
│   │   ├── __init__.py
│   │   ├── deps.py          # 의존성 주입
│   │   └── v1/              # API v1
│   │       ├── __init__.py
│   │       ├── auth.py      # 인증 엔드포인트
│   │       └── users.py     # 사용자 엔드포인트
│   ├── core/                # 핵심 기능
│   │   ├── __init__.py
│   │   ├── security.py      # 보안 관련 (JWT, 비밀번호)
│   │   └── exceptions.py    # 예외 처리
│   └── utils/               # 유틸리티 함수
├── alembic/                 # 데이터베이스 마이그레이션
├── .env.example             # 환경 변수 예제
├── requirements.txt         # Python 패키지
└── README.md

```

## 설치 및 실행

### 1. 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 값들을 설정하세요.

```bash
cp .env.example .env
```

### 4. 데이터베이스 마이그레이션

```bash
# 마이그레이션 초기화 (최초 1회)
alembic init alembic

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 적용
alembic upgrade head
```

### 5. 서버 실행

```bash
uvicorn app.main:app --reload
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### 인증
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `GET /api/v1/auth/me` - 현재 사용자 정보 (인증 필요)

### 사용자
- `GET /api/v1/users` - 사용자 목록 (인증 필요)
- `GET /api/v1/users/{id}` - 사용자 상세 (인증 필요)

## 개발 가이드

### 새로운 API 엔드포인트 추가

1. `app/schemas/`에 Pydantic 스키마 생성
2. `app/api/v1/`에 라우터 파일 생성
3. `app/main.py`에 라우터 등록

### 데이터베이스 모델 추가

1. `app/models/`에 SQLAlchemy 모델 생성
2. `app/database.py`에 모델 import
3. 마이그레이션 생성 및 적용

## 기술 스택

- **FastAPI**: 웹 프레임워크
- **SQLAlchemy**: ORM
- **Alembic**: 데이터베이스 마이그레이션
- **Pydantic**: 데이터 검증
- **JWT**: 인증 토큰
- **PostgreSQL**: 데이터베이스 (또는 SQLite)

## 라이선스

MIT
