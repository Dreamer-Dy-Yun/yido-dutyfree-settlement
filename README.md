# 구매대행 B2C (YIDO)

면세점 EDI 연동 및 데이터 매핑을 위한 웹 서비스입니다.

## 주요 기능

- **역할 분리**: 시스템 관리자 / 테넌트(운영) 관리자 / 작업자
- **인증**: JWT, 테넌트별 스키마. 시스템 관리자·일반 유저 세션 분리(`admin_access_token` / `access_token`)
- **EDI 업로드**: 롯데·신라 면세점 엑셀(.xlsx, .xls) 업로드 → 파싱 후 테넌트 스키마 EDI 테이블 반영
- **이미지 업로드**: 데이터 매핑 화면에서 ZIP 업로드 (엔드포인트·UI 껍데기 구현, 처리 로직 추후)
- **테넌트·유저 관리**: 테넌트 승인/거부, 테넌트별 사용자·사용량 관리
- **API 문서**: Swagger UI (`/docs`), ReDoc (`/redoc`)

## 프로젝트 구조

```
.
├── WEB_SERVER/           # FastAPI 백엔드
│   ├── app.py            # (사용 시) uvicorn 진입점
│   ├── main_web.py       # 웹 서버 기동
│   ├── auth/             # JWT, 세션, 의존성
│   └── routers/          # API 라우터 (auth, tenant, system-admin, company, registration)
├── DATABASE/             # DB 레이어
│   ├── config.py         # DB 매니저 설정
│   ├── models/           # SQLAlchemy 모델 (public, tenant)
│   ├── dbms/             # PostgreSQL 비동기 엔진/매니저
│   └── repositories/     # 테넌트·유저 등 리포지토리
├── PROCESSOR_DATA/       # EDI 처리
│   ├── parsers/          # 롯데·신라 파서 (edi_lotte, edi_silla)
│   ├── edi_processor.py  # 공통 EDI 프로세서
│   ├── patch.py          # xlsx 날짜 문자열 패치 (신라)
│   └── test_parser.py    # 파서 테스트
├── PROCESSOR_IMAGE/      # 이미지 처리 (POC)
│   └── test.py           # ZIP 바이너리 → 파일 저장 POC
├── CUSTOMIZED/           # 프로젝트 전용 유틸 (엑셀, 웹 헬퍼, 데코 등)
├── FRONT_END/            # React + Vite 프론트
│   └── src/
│       ├── admin/        # 시스템 관리자 (/admin)
│       ├── pages/        # 로그인, 대시보드, 데이터 매핑 등
│       └── services/     # api, auth, tenant
├── docs/                 # 설계 문서 (프론트 아키텍처 등)
├── nginx/                # Nginx 설정 템플릿·배포
├── main.py               # 앱 메인 (DB 설정 + 웹 서버)
├── requirements.txt
└── README.md
```

## 설치 및 실행

### 1. 가상 환경

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

### 3. 환경 변수

프로젝트 루트에 `.env`를 두고 DB URL, Redis, CORS 등 설정. (예시는 프로젝트 내 `.env.example` 참고.)

### 4. 백엔드 실행

```bash
# 방법 1: uvicorn 직접 (개발 시 흔히 사용)
uvicorn WEB_SERVER.app:app --reload --port 10000

# 방법 2: main.py 경유 (DB 설정 후 웹 서버 기동)
python main.py
```

- API 문서: http://localhost:10000/docs (또는 사용 포트)

### 5. 프론트엔드 실행

```bash
cd FRONT_END
npm install
npm run dev
```

- Node가 PATH에 없으면 사용자 PATH에 `C:\Program Files\nodejs` 추가 또는 터미널에서 `$env:Path += ";C:\Program Files\nodejs"` 후 실행.

## API 개요

| 구분        | prefix              | 용도                     |
|-------------|---------------------|--------------------------|
| 인증        | `/api/auth`         | 로그인, 로그아웃, JWT, 시스템 관리자 로그인 |
| 회사/등록   | `/api/company`, `/api/registration` | 회사 검색, 회사 등록    |
| 테넌트      | `/api/tenant`       | 유저 관리, EDI 업로드, 이미지 ZIP 업로드, 사용량 |
| 시스템 관리자 | `/api/system-admin` | 테넌트·서비스 어카운트 관리 |

- **EDI 업로드**: `POST /api/tenant/data-mapping/edi-upload` (form: `file`, `edi_source=lotte|silla`)
- **이미지 ZIP 업로드**: `POST /api/tenant/data-mapping/image-upload` (form: `file`, .zip만 허용, 현재 껍데기)

## 기술 스택

- **백엔드**: FastAPI, SQLAlchemy(비동기), PostgreSQL, Redis(세션), JWT
- **프론트**: React, Vite
- **EDI/이미지**: pandas, openpyxl, zipfile (Python 표준)

## 문서

- `docs/FRONTEND_ARCHITECTURE.md` — 프론트 역할·라우팅·API 구조
- `docs/TOKEN_SPLIT_IMPLEMENTATION_PLAN.md` — 시스템 관리자/일반 유저 토큰 분리 설계
- `nginx/README.md` — Nginx 배포 방법

## 라이선스

MIT
