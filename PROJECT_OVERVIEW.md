# NOVAS EZ 프로젝트 개요

## 📋 프로젝트 소개

NOVAS EZ는 ICT(In-Circuit Test) 장비에서 측정 데이터를 자동으로 수집, 저장, 분석하는 백엔드 시스템입니다. PostgreSQL과 pgvector를 활용한 벡터 유사도 검색 기능을 제공하며, FastAPI 기반의 REST API를 통해 프론트엔드와 연동됩니다.

**작성자**: Yun Dae-young  
**연락처**: Dreamer.Dy.Yun@Gmail.com  
**버전**: 1.0.0

---

## 🏗️ 시스템 아키텍처

### 전체 구조

```
┌─────────────────┐
│   ICT 장비들     │
│  (SSH 접속)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  File Retriever │  ← 파일 리스트 확보 및 다운로드
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Archiver   │  ← CSV 파싱 및 Parquet 변환
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │  ← 데이터 저장 (pgvector 포함)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │  ← REST API 제공
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Frontend      │
└─────────────────┘
```

---

## 🔧 주요 기능

### 1. 파일 리트리빙 (File Retrieval)

**목적**: ICT 장비에서 측정 데이터 파일(CSV)을 자동으로 다운로드

**주요 컴포넌트**:
- `FileRetriever` (`data_retriever.py`): 파일 리스트 확보 및 다운로드 로직
- `ICTRetrieveRunner` (`main_retriever.py`): 스케줄러를 통한 자동 실행
- `OpenSSHConnector` (`OPEN_SSH/ssh_connector.py`): SSH 연결 및 SFTP 파일 전송

**동작 흐름**:
1. DB에서 활성화된 ICT 장비 목록 조회
2. 각 장비에 SSH 연결 시도
3. 모델별 폴더 구조 탐색 (모델 > YYYY > MM > DD > CSV 파일)
4. 최종 다운로드 일시 이후 생성된 파일 목록 확보
5. 파일 목록을 DB의 `process` 테이블에 저장
6. 배치 단위로 파일 다운로드 실행
7. 다운로드 성공/실패 상태를 DB에 반영

**특징**:
- 동시 다운로드 제한 (배치 크기 설정 가능)
- 재시도 로직 포함
- 연결 실패 시 장비 접근 가능 여부(`accessible`) 자동 업데이트
- 파일 해시값을 통한 중복 방지

---

### 2. 데이터 아카이빙 (Data Archiving)

**목적**: 다운로드된 CSV 파일을 파싱하여 구조화된 데이터로 변환 및 저장

**주요 컴포넌트**:
- `DataArchiver` (`data_archiver.py`): 파싱 및 DB 저장 로직
- `ICTArchiveRunner` (`main_archiver.py`): 스케줄러를 통한 자동 실행
- `ICTDataExtractor` (`OPEN_SSH/ict_data_extractor.py`): CSV 파일 파싱

**동작 흐름**:
1. DB에서 파싱되지 않은 파일 목록 조회 (`is_parsed=False`)
2. CSV 파일을 파싱하여 측정 데이터 추출
3. 스펙(Spec) 정보와 측정(Measured) 데이터를 분리
4. Parquet 형식으로 변환하여 저장
5. DB에 스펙 및 측정 데이터 저장
6. 정규화된 벡터 데이터 생성 및 저장 (`normalized` 테이블)
7. 파싱 성공/실패 상태를 DB에 반영

**저장 구조**:
```
base_dir/
├── SPEC/
│   └── {model_name}/
│       └── {spec_file}.parquet
└── MEASURED/
    └── {model_name}/
        └── {measured_file}.parquet
```

**특징**:
- 동시 처리 제한 (세마포어 사용)
- 파싱 실패 시 에러 로그 기록
- 벡터 정규화를 통한 유사도 검색 준비

---

### 3. 데이터 분석 (Data Analysis)

**목적**: 측정 데이터를 통계적으로 분석하여 품질 관리 정보 제공

**주요 컴포넌트**:
- `SpecAnalyzer` (`ANALYZER/spec_analyzer.py`): PMF(Probability Mass Function) 계산
- `WEB_SERVER/services/service.py`: 분석 결과를 API로 제공

**주요 분석 기능**:

#### 3.1 PMF (Probability Mass Function) 분석
- 두 데이터셋을 비교하는 바이올린 차트 데이터 생성
- 스펙 기준 정규화
- 양자화 및 확률 질량 함수 계산
- 해상도 조절 가능 (10~400)

#### 3.2 단일 항목 트렌드 분석
- 특정 시리얼번호의 측정값 변화 추이 분석
- 시간에 따른 데이터 변화 시각화

#### 3.3 시계열 데이터 조회
- 모델별 인덱스별 시계열 데이터 제공
- 날짜 범위 및 ICT 장비 필터링 지원

---

### 4. 벡터 유사도 검색 (Vector Similarity Search)

**목적**: 불량 데이터와 유사한 패턴을 가진 시리얼을 검색

**주요 컴포넌트**:
- `Normalized` 테이블: pgvector를 사용한 벡터 저장
- `CRUDer.get_relative_similarities()`: 코사인 유사도 계산
- `CRUDer.get_absolute_similarities()`: 절대 유사도 계산

**동작 방식**:
1. 측정 데이터를 정규화하여 3000차원 벡터로 변환
2. pgvector의 DiskANN 인덱스 사용
3. 불량 시리얼과 유사한 패턴을 가진 시리얼 검색
4. 상위 N% 시리얼 반환

**유사도 지표**:
- Cosine Similarity (코사인 유사도)
- L2 Distance (유클리드 거리)
- Inner Product (내적)

---

### 5. REST API (FastAPI)

**목적**: 프론트엔드와의 데이터 교환 인터페이스 제공

**주요 엔드포인트**:

#### 5.1 PMF 관련 (`/api/pmf`)
- `GET /get/pmf_data`: PMF 차트 데이터 조회
- `GET /get/single_item_trend`: 단일 항목 트렌드 조회
- `GET /get/instruments`: ICT 장비 목록 조회
- `GET /get/models`: 모델 목록 조회
- `GET /get/time_series`: 시계열 데이터 조회

#### 5.2 유사도 관련 (`/api/similarity`)
- `GET /get/trends`: 불량 유사도 트렌드 조회
- `GET /download/xlsx/defects_similars`: 불량 유사도 Excel 다운로드
- `POST /set/normalize_and_upsert_all_models`: 모델 정규화 및 벡터 업서트
- `POST /set/defect`: 불량 데이터 동기화
- `GET /get/url/google_spreadsheet/defects`: Google 스프레드시트 URL 조회

#### 5.3 루트 (`/`)
- `GET /`: 서버 상태 확인
- `GET /health`: 헬스 체크 (DB 연결 상태 포함)
- `POST /upsert/instrument`: ICT 장비 정보 등록/수정

**특징**:
- GZIP 압축 응답 지원
- CORS 설정 (환경변수로 관리)
- 에러 핸들링 데코레이터
- 캐싱 지원 (`@alru_cache`)

---

### 6. Google 스프레드시트 연동

**목적**: 외부 불량 데이터를 Google 스프레드시트에서 동기화

**주요 컴포넌트**:
- `data_retriever_defect.py`: Google 스프레드시트에서 불량 데이터 읽기
- `scheduler_defect.py`: 스케줄러를 통한 자동 동기화

**동작 흐름**:
1. Google Service Account를 통한 인증
2. 스프레드시트에서 불량 데이터 읽기
3. 시리얼번호 검증 (DB에 존재하는 시리얼만 처리)
4. `external_defect` 테이블에 업서트

---

## 🗄️ 데이터베이스 구조

### 주요 테이블

#### `instrument`
- ICT 장비 정보
- SSH 연결 정보, 경로 설정 등

#### `model`
- PCB 모델 정보

#### `spec`
- 스펙 정보 (Parquet 파일 경로, 해시값)
- 복합 유니크 키: `(model_name, path_sub_datafile)`

#### `measured`
- 측정 데이터 (Parquet 파일 경로, 해시값, 측정값 배열)
- 복합 유니크 키: `(serial_no, path_sub_datafile)`

#### `normalized`
- 정규화된 벡터 데이터 (pgvector 사용)
- 유니크 키: `measured_id`

#### `process`
- 파일 리트리빙 이력 관리
- 복합 유니크 키: `(instrument_name, model_name, path_full_source)`
- 상태: `PENDING`, `RETRIEVED`, `PARSED`, `ARCHIVED`, `ERROR`
- Lock 메커니즘: `is_locked` (동시성 제어)

#### `external_defect`
- 외부 불량 데이터 (Google 스프레드시트에서 동기화)

#### `google_service_account`
- Google Service Account 설정 정보

---

## 🔄 스케줄러 작업

### 1. 파일 리트리버 작업
- **실행 주기**: 5초마다 (`CronTrigger(second='*/5')`)
- **최대 인스턴스**: 1개
- **기능**: ICT 장비에서 파일 목록 확보 및 다운로드

### 2. 데이터 아카이버 작업
- **실행 주기**: 5초마다 (`CronTrigger(second='*/5')`)
- **최대 인스턴스**: 5개
- **기능**: 다운로드된 CSV 파일 파싱 및 저장

---

## 🛠️ 기술 스택

### 백엔드
- **Python**: 3.11+
- **FastAPI**: REST API 프레임워크
- **SQLAlchemy**: ORM
- **asyncpg**: 비동기 PostgreSQL 드라이버
- **pandas**: 데이터 처리
- **numpy**: 수치 연산

### 데이터베이스
- **PostgreSQL**: 메인 데이터베이스
- **pgvector**: 벡터 유사도 검색
- **vectorscale**: 벡터 인덱스 (DiskANN)

### 네트워크
- **asyncssh**: 비동기 SSH/SFTP 클라이언트

### 스케줄링
- **APScheduler**: 비동기 작업 스케줄러

### 외부 연동
- **gspread**: Google 스프레드시트 API
- **google-auth**: Google 인증

---

## 📁 프로젝트 구조

```
BACK_END/
├── DATABASE/              # 데이터베이스 관련
│   ├── config.py         # DB 설정 및 연결 관리
│   ├── cruder.py         # CRUD 작업
│   ├── models.py         # SQLAlchemy ORM 모델
│   ├── pg_manager.py     # PostgreSQL 관리자 (Upsert 로직 포함)
│   └── setup_db.py       # DB 초기화
│
├── OPEN_SSH/             # SSH 관련
│   ├── ssh_connector.py  # SSH 연결 및 파일 전송
│   └── ict_data_extractor.py  # CSV 파싱
│
├── WEB_SERVER/           # FastAPI 서버
│   ├── app.py            # FastAPI 앱 설정
│   ├── main_web.py       # 웹 서버 실행
│   ├── routers/          # API 라우터
│   │   ├── router_pmf.py        # PMF 관련 API
│   │   ├── router_similarity.py # 유사도 관련 API
│   │   └── router_root.py       # 루트 API
│   └── services/         # 서비스 레이어
│       └── service.py    # 비즈니스 로직
│
├── ANALYZER/             # 데이터 분석
│   └── spec_analyzer.py  # PMF 분석 로직
│
├── GOOGLE_DRIVE/         # Google 스프레드시트 연동
│   └── data_retriever_defect.py
│
├── CUSTOMIZED/           # 커스텀 유틸리티
│   ├── cust_logger.py    # 로깅
│   ├── cust_powershell.py # PowerShell DSL
│   ├── cust_parser.py    # 파서
│   └── ...
│
├── data_retriever.py     # 파일 리트리버
├── data_archiver.py      # 데이터 아카이버
├── main_retriever.py     # 리트리버 실행기
├── main_archiver.py       # 아카이버 실행기
└── main.py               # 메인 진입점
```

---

## 🔐 환경 변수 설정

`.env` 파일을 통해 환경 변수를 관리합니다:

```env
# 데이터베이스 설정
DB_NAME=novas_ez
DB_USER=admin
DB_PASSWORD=123!@#qwe
DB_HOST=localhost
DB_PORT=5432
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50

# 경로 설정
DIR_BASE_FOR_PARQUET=C:/Users/user/ict_parquets

# CORS 설정
CORS_ORIGINS=http://localhost:3001,http://192.168.0.19:3001,http://172.23.112.1:3001
```

**참고**: `.env` 파일은 `DATABASE/__init__.py`에서 자동으로 로드됩니다.

---

## 🚀 실행 방법

### 전체 시스템 실행
```bash
python main.py
```

### 웹 서버만 실행
```bash
python WEB_SERVER/main_web.py
```

### 리트리버만 실행
```bash
python main_retriever.py
```

### 아카이버만 실행
```bash
python main_archiver.py
```

---

## 📊 주요 데이터 흐름

### 1. 파일 리트리빙 흐름
```
ICT 장비 → SSH 연결 → 파일 목록 확보 → DB 저장 (process 테이블)
→ 파일 다운로드 → 로컬 저장 → DB 상태 업데이트
```

### 2. 데이터 아카이빙 흐름
```
CSV 파일 → 파싱 (ICTDataExtractor) → 데이터 추출
→ Parquet 변환 → 파일 저장 → DB 저장 (spec, measured 테이블)
→ 벡터 정규화 → DB 저장 (normalized 테이블)
```

### 3. API 요청 흐름
```
프론트엔드 → FastAPI → Service Layer → CRUDer → PostgreSQL
→ 데이터 반환 → GZIP 압축 → 응답
```

---

## 🔍 주요 알고리즘

### 1. Upsert 로직
- **위치**: `DATABASE/pg_manager.py::upsert_dataframe()`
- **동작**: PostgreSQL의 `ON CONFLICT DO UPDATE` 사용
- **특징**:
  - 자동으로 Primary Key 또는 Unique Key 감지
  - DataFrame을 받아 자동 처리
  - 유니크 키 컬럼 존재 검증 포함

### 2. PMF 계산
- **위치**: `ANALYZER/spec_analyzer.py::SpecAnalyzer`
- **알고리즘**:
  1. 데이터 클리핑 (극값 제거)
  2. 양자화 (해상도에 따라 구간 분할)
  3. 확률 질량 함수 계산
  4. 정규화

### 3. 벡터 유사도 검색
- **위치**: `DATABASE/cruder.py::get_relative_similarities()`
- **방식**: pgvector의 DiskANN 인덱스 활용
- **지표**: 코사인 유사도, L2 거리, 내적

---

## ⚙️ 설정 및 튜닝

### 리트리버 설정
- `DOWNLOAD_BATCH_SIZE`: 동시 다운로드 파일 수 (기본: 10)
- `FETCH_LIST_LIMIT`: 한 번에 가져올 파일 목록 수 (기본: 20)

### 아카이버 설정
- `max_concurrent`: 동시 파싱 작업 수 (기본: 8)

### 스케줄러 설정
- 리트리버: `max_instances=1` (동시 실행 1개만)
- 아카이버: `max_instances=5` (동시 실행 최대 5개)

---

## 📝 주요 특징

1. **비동기 처리**: 모든 I/O 작업은 비동기로 처리
2. **동시성 제어**: Lock 메커니즘을 통한 중복 처리 방지
3. **에러 처리**: 재시도 로직 및 상세한 에러 로깅
4. **성능 최적화**: 벡터화 연산, 인덱스 활용, 캐싱
5. **확장성**: 모듈화된 구조로 기능 추가 용이

---

## 🔄 데이터 상태 관리

### Process 테이블 상태
- `PENDING`: 리스트만 확보, 다운로드 전
- `RETRIEVED`: 다운로드 완료, 파싱 전
- `PARSED`: 파싱 완료, 아카이빙 완료
- `ARCHIVED`: 아카이빙 완료
- `ERROR`: 에러 발생

### Lock 메커니즘
- `is_locked`: 동시 처리 방지
- `FOR UPDATE SKIP LOCKED`: PostgreSQL의 동시성 제어 활용

---

## 📌 주의사항

1. **유니크 키 검증**: Upsert 시 모든 유니크 키 컬럼이 DataFrame에 있어야 함
2. **인코딩**: CSV 파일은 주로 `euc-kr` 인코딩 사용
3. **경로 설정**: Windows 경로 형식 사용 (`C:/Users/...`)
4. **벡터 차원**: 정규화된 벡터는 3000차원 고정

---

## 🐛 알려진 이슈

1. 리팩토링 필요: `data_retriever.py` (주석에 명시됨)
2. 모델별 테이블 분리: `normalized` 테이블은 현재 통합 관리 (TODO)
3. 경로 구조: ICT 장비 내부 폴더 구조는 추정 중

---

## 📚 참고 문서

- `MIGRATION_GUIDE.md`: 프로젝트 이전 가이드
- 각 모듈의 주석: 상세한 설명 포함

---

## 👤 작성자 정보

**Yun Dae-young**  
Email: Dreamer.Dy.Yun@Gmail.com

---

*문서 생성일: 2025년*

