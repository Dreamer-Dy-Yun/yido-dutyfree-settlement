# YIDO — CI/CD 및 웹 배포 준비 사항

이 문서는 현재 저장소 상태를 기준으로 **CI/CD 파이프라인**과 **프로덕션 웹 배포**까지 가기 위해 추가로 정리·결정·구현할 항목을 정리한 것입니다.

---

## 1. 현재 상태 (요약)

| 영역 | 상태 |
|------|------|
| **CI 설정** | `.github/workflows`, GitLab CI 등 **파이프라인 파일 없음** |
| **컨테이너 이미지** | 앱용 **Dockerfile 없음**. `docker-compose.yml`은 Postgres·Redis·Nginx·워커용이며, 백엔드 API는 호스트의 `uvicorn`(기본 포트 **10000**)을 전제로 함 |
| **백엔드** | FastAPI + `uvicorn` (`WEB_SERVER/main_web.py`, `main.py`), `requirements.txt` 기준 의존성 |
| **프론트** | React + Vite (`FRONT_END`), 빌드 산출물은 `FRONT_END/dist` |
| **리버스 프록시** | `nginx/compose.default.conf`(Compose용), `nginx/nginx.conf.template` + `deploy_nginx.py`(서버 배포용) |
| **백그라운드** | `match_worker`, `edi_unified_worker`(Redis + `WEB_API_BASE_URL`로 API 호출) |
| **테스트** | `DATABASE/tests` 등 여러 경로에 `pytest` 스타일 테스트 존재. 루트 `pytest.ini`는 `testpaths = TEST`인데 **`TEST` 디렉터리는 없음**. `requirements.txt`에 **pytest 미포함** |

즉, **로컬/수동 배포는 README·nginx README로 가능하지만, 자동 빌드·검증·배포는 아직 “정의되지 않은” 상태**입니다.

---

## 2. CI(지속적 통합)에서 할 일

### 2.1 플랫폼 선택

- GitHub → **GitHub Actions**
- GitLab → **`.gitlab-ci.yml`**
- 기타 → Jenkins, Azure DevOps 등

저장소 호스팅과 동일한 곳에 두는 것이 시크릿·권한 관리가 쉽습니다.

### 2.2 파이프라인 단계(권장)

1. **트리거**: `push`/`pull_request` 대상 브랜치(예: `main`, `backend`) 지정  
2. **백엔드**
   - Python 버전 고정(예: 3.11, 워커와 맞춤)
   - `pip install -r requirements.txt`
   - (선택) `ruff` / `black` 등 린트·포맷
   - **테스트**: `pytest` 실행 전에 아래 정리 필요(섹션 2.3)
3. **프론트**
   - `cd FRONT_END && npm ci && npm run build && npm run lint`
4. **산출물(아티팩트)** (선택)
   - `FRONT_END/dist` 압축, 또는 Docker 이미지(이미지 전략을 쓸 경우)

### 2.3 테스트·`pytest` 정리 (필수에 가까움)

- `pytest.ini`의 `testpaths = TEST`와 실제 테스트 위치가 **불일치**합니다. 다음 중 하나를 선택하는 것이 좋습니다.
  - `testpaths`를 실제 모듈 테스트 디렉터리에 맞게 수정하거나,
  - 통합 테스트만 모은 `TEST/` 디렉터리를 두고 그쪽만 CI에서 돌리기
- **`requirements.txt`(또는 `requirements-dev.txt`)에 `pytest`, `pytest-asyncio` 등 명시** — CI와 로컬이 동일하게 재현되도록
- DB·Redis를 쓰는 통합 테스트는 **CI에서 서비스 컨테이너**(GitHub Actions의 `services:` 등)로 띄우거나, **마커로 분리**해 PR에서는 단위 테스트만 돌리는 식으로 정책을 정함

### 2.4 시크릿·환경 변수 (CI 전용)

- DB URL, JWT 시크릿, Redis URL 등은 **저장소에 넣지 않고** CI 시크릿 변수로 주입  
- 프론트 빌드 시 API 베이스 URL: `FRONT_END`의 `VITE_API_BASE_URL`은 **빌드 시점에 박힘** — 스테이징/프로덕션별로 CI에서 다른 값을 넣어 **별도 빌드**가 필요할 수 있음

---

## 3. CD(지속적 배포) 및 웹 배포

### 3.1 배포 타깃 결정

| 방식 | 특징 |
|------|------|
| **단일 VM + Nginx + systemd** | 현재 `nginx/nginx.conf.template`, `deploy_nginx.py`와 잘 맞음. API는 `127.0.0.1:10000` 등으로 프록시 |
| **Docker Compose on 서버** | DB·Redis·워커까지 한 번에 — 단, **프로덕션용 compose**(비밀번호 하드코딩 제거, 볼륨·재시작 정책) 정리 필요 |
| **Kubernetes / PaaS** | 별도 매니페스트·헬스체크·시크릿 스토어 설계 필요 |

### 3.2 웹(프론트) 배포 체크리스트

1. **프로덕션 빌드**: `npm run build` → `FRONT_END/dist`  
2. **`VITE_API_BASE_URL`**: 사용자 브라우저가 접근 가능한 **공개 API URL**(예: `https://api.example.com` 또는 동일 오리진의 `/api/`만 쓰는 경우 상대 경로 전략)으로 설정  
3. **Nginx**
   - 정적 파일: `root`를 `dist` 경로로  
   - SPA: `try_files ... /index.html` (이미 `compose.default.conf`·템플릿에 반영됨)  
   - `/api/` → FastAPI 업스트림 (`nginx.conf.template`의 `FASTAPI_PROXY_HOST`, `FASTAPI_PORT`)  
4. **HTTPS**: Let’s Encrypt 등으로 인증서·자동 갱신(cron / certbot)  
5. **캐시·헤더**: 정적 자산 캐시, `index.html`은 캐시 무력화 등(필요 시)

### 3.3 백엔드(API) 프로덕션 체크리스트

1. **`WEB_SERVER_RELOAD=false`**, 적절한 `WEB_SERVER_HOST`/`WEB_SERVER_PORT`  
2. **프로세스 관리자**: `systemd` 유닛 또는 **gunicorn + uvicorn worker** 등 — 단일 `uvicorn` 프로세스만으로도 가능하나 부하·재시작 정책은 검토  
3. **`.env`**: 서버에만 두고, 민감 정보는 권한 제한  
4. **DB 마이그레이션**: `setup_db`·시드 정책(`DATABASE/`)을 배포 스크립트에 포함할지 결정  
5. **헬스 엔드포인트**: 로드밸런서·오케스트레이터용 `/health` 등(없으면 추가 검토)

### 3.4 워커·Redis·Postgres

- `match_worker`, `edi_unified_worker`는 **`WEB_API_BASE_URL`이 배포 환경에서 도달 가능한 주소**여야 함(내부 DNS 또는 `http://127.0.0.1:포트`)  
- 프로덕션에서는 **같은 호스트**인지 **별 컨테이너**인지에 따라 URL을 분리해 설정

### 3.5 보안·운영

- `docker-compose.yml`의 DB 비밀번호 등 **개발용 기본값은 프로덕션에 그대로 쓰지 말 것** — 환경 변수·시크릿으로 치환  
- 배포 후 **스모크 테스트**: 로그인, 대표 API 한두 개  
- (선택) 배포 승인, 블루/그린, 롤백 절차 문서화

---

## 4. 저장소·엔지니어링 보완 (선택이지만 효과 큼)

- **프로덕션용 Dockerfile** (백엔드 멀티스테이지, non-root 유저) — VM 대신 컨테이너 표준화 시 유리  
- **`docker-compose.prod.yml` + `.env.example` 완성** — 새 환경 재현용  
- **버전 태그·CHANGELOG** — 릴리스와 롤백 기준  
- **브랜치 전략**: `main` 배포, `develop` 스테이징 등

---

## 5. 한눈에 보는 “해야 할 일” 목록

1. CI 플랫폼 선택 및 **워크플로우 YAML** 추가  
2. **`pytest` 경로·의존성 정리** 후 CI에서 테스트 실행  
3. 프론트: **`npm ci` / `build` / `lint`** 자동화, 환경별 **`VITE_API_BASE_URL`** 전략 확정  
4. 배포 서버: **Nginx + 정적 `dist` + API 프록시** 또는 **Compose/컨테이너** 중 하나로 표준화  
5. **시크릿·DB·Redis·JWT**를 코드/compose 밖으로 완전 분리  
6. **워커 `WEB_API_BASE_URL`** 프로덕션 값 확인  
7. (권장) **헬스체크**, HTTPS, 배포 후 스모크 테스트

---

## 6. 관련 기존 문서

- 루트 `README.md` — 로컬 실행, 포트, 구조  
- `nginx/README.md` — `nginx.env`, `deploy_nginx.py`, 템플릿 변수  
- `docker-compose.yml` — 로컬 스택 구성(주석: 백엔드는 호스트 10000 전제)

이 문서는 **현재 코드베이스 스냅샷**을 기준으로 작성되었으며, 인프라 선택에 따라 항목을 추가·삭제하면 됩니다.
