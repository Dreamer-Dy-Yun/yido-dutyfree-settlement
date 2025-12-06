# 프로젝트 이전 가이드 (Migration Guide)

## 📋 이전 전 체크리스트

### 1. 현재 컴퓨터에서 준비할 것들

#### A. 코드 및 설정 파일
- [x] Git 저장소 (이미 사용 중)
- [ ] 환경 변수 파일 (`.env` 생성 필요)
- [ ] SSH 키 파일들
- [ ] Google Service Account JSON 파일들

#### B. 데이터베이스
- [ ] PostgreSQL 데이터베이스 덤프
- [ ] 데이터베이스 스키마 백업

#### C. 데이터 파일
- [ ] `./data` 디렉토리 (SPEC, MEASURED 등)
- [ ] 기타 필요한 데이터 파일들

---

## 🚀 이전 단계별 가이드

### Step 1: 현재 컴퓨터에서 준비

#### 1-1. Git 커밋 및 푸시
```bash
# 변경사항 커밋
git add .
git commit -m "이전 전 최종 커밋"
git push origin BACK_END
```

#### 1-2. 환경 변수 파일 생성 (`.env`)
프로젝트 루트에 `.env` 파일 생성:
```env
# 데이터베이스 설정
DB_NAME=novas_ez
DB_USER=admin
DB_PASSWORD=123!@#qwe
DB_HOST=localhost
DB_PORT=5432

# 경로 설정
PARENT_PATH_SPEC=C:/Users/user/Novas_Ez/SPEC
PARENT_PATH_MEASURED=C:/Users/user/Novas_Ez/MEASURED

# CORS 설정
CORS_ORIGINS=http://localhost:3001

# API 포트
API_PORT=8000
```

#### 1-3. 데이터베이스 덤프
```bash
# PostgreSQL 덤프 생성
pg_dump -U admin -d novas_ez -F c -f novas_ez_backup.dump

# 또는 SQL 형식으로
pg_dump -U admin -d novas_ez > novas_ez_backup.sql
```

#### 1-4. 민감한 파일 백업
- SSH 키 파일들 (`~/.ssh/` 또는 프로젝트 내)
- Google Service Account JSON 파일들
- 기타 설정 파일들

#### 1-5. 데이터 파일 백업
```bash
# data 디렉토리 압축 (필요한 경우)
tar -czf data_backup.tar.gz ./data
```

---

### Step 2: 새 컴퓨터에서 설정

#### 2-1. 필수 소프트웨어 설치
- [ ] Python 3.11+
- [ ] PostgreSQL (pgvector 확장 포함)
- [ ] Git
- [ ] Docker & Docker Compose (선택사항)

#### 2-2. 프로젝트 클론
```bash
git clone <repository-url>
cd BACK_END
git checkout BACK_END
```

#### 2-3. 가상환경 설정
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 2-4. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 2-5. 환경 변수 설정
`.env` 파일을 새 컴퓨터 경로에 맞게 수정:
```env
DB_HOST=localhost  # 또는 새 DB 서버 주소
PARENT_PATH_SPEC=C:/새경로/SPEC
PARENT_PATH_MEASURED=C:/새경로/MEASURED
```

#### 2-6. 데이터베이스 복원
```bash
# PostgreSQL 데이터베이스 생성
createdb -U admin novas_ez

# 덤프 복원
pg_restore -U admin -d novas_ez novas_ez_backup.dump

# 또는 SQL 파일로
psql -U admin -d novas_ez < novas_ez_backup.sql
```

#### 2-7. pgvector 확장 설치
```sql
-- PostgreSQL에 접속하여
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 2-8. 민감한 파일 복사
- SSH 키 파일들 복사
- Google Service Account JSON 파일들 복사
- 경로 확인 및 업데이트

#### 2-9. 데이터 파일 복사
```bash
# data 디렉토리 복사
# 또는 압축 해제
tar -xzf data_backup.tar.gz
```

---

### Step 3: 테스트 및 검증

#### 3-1. 연결 테스트
```bash
# 데이터베이스 연결 테스트
python -c "from DATABASE.config import db_manager; import asyncio; asyncio.run(db_manager.connect())"
```

#### 3-2. 애플리케이션 실행
```bash
# 개발 모드
uvicorn WEB_SERVER.app:app --reload

# 또는 Docker 사용
docker-compose up -d
```

#### 3-3. Health Check
```bash
# 브라우저 또는 curl로
curl http://localhost:8000/health
```

---

## ⚠️ 주의사항

### 1. 경로 문제
- Windows와 Linux 경로 차이 주의
- 절대 경로 vs 상대 경로 확인

### 2. 데이터베이스 연결
- `DB_HOST` 환경 변수 확인
- 방화벽 설정 확인
- PostgreSQL 접근 권한 확인

### 3. 민감한 정보
- `.env` 파일은 Git에 커밋하지 않기
- `.gitignore`에 `.env` 추가 확인
- SSH 키, 비밀번호 등은 안전하게 전송

### 4. 의존성 문제
- `requirements.txt`의 Git 의존성 확인
- 특정 버전 호환성 확인

---

## 🔧 문제 해결

### 문제 1: 데이터베이스 연결 실패
```bash
# PostgreSQL 서비스 확인
# Windows: services.msc에서 PostgreSQL 확인
# Linux: sudo systemctl status postgresql
```

### 문제 2: 모듈 import 오류
```bash
# 가상환경 활성화 확인
# PYTHONPATH 설정 확인
```

### 문제 3: 경로 오류
- 환경 변수 `PARENT_PATH_*` 확인
- 상대 경로 vs 절대 경로 확인

---

## 📝 체크리스트 요약

### 이전 전 (현재 컴퓨터)
- [ ] Git 커밋 & 푸시
- [ ] `.env` 파일 생성
- [ ] 데이터베이스 덤프
- [ ] 민감한 파일 백업
- [ ] 데이터 파일 백업

### 이전 후 (새 컴퓨터)
- [ ] 필수 소프트웨어 설치
- [ ] 프로젝트 클론
- [ ] 가상환경 설정
- [ ] 의존성 설치
- [ ] 환경 변수 설정
- [ ] 데이터베이스 복원
- [ ] pgvector 확장 설치
- [ ] 민감한 파일 복사
- [ ] 데이터 파일 복사
- [ ] 연결 테스트
- [ ] 애플리케이션 실행 테스트

