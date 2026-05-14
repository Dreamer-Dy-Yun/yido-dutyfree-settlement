# Nginx 설정 파일

Nginx 웹서버 설정을 위한 템플릿 및 배포 스크립트입니다.

## 파일 구조

```
nginx/
├── nginx.conf.template      # Nginx 설정 템플릿 (%{VAR}% 형식 사용)
├── nginx.env.example        # 환경 변수 예제 파일
├── nginx.env                # 실제 환경 변수 파일 (프로젝트별로 생성)
├── deploy_nginx.py          # Python 배포 스크립트 (모든 플랫폼)
└── README.md                # 이 파일
```

## 사용 방법

### 1. 환경 변수 파일 생성

```bash
cd nginx
cp nginx.env.example nginx.env
```

`nginx.env` 파일을 열어 프로젝트에 맞게 수정하세요:

```bash
NGINX_LISTEN_PORT=80
NGINX_MAIN_DOMAIN=yourdomain.com
NGINX_ADMIN_DOMAIN=admin.yourdomain.com
NGINX_MAIN_FRONTEND_PATH=/var/www/production-frontend/dist
NGINX_ADMIN_FRONTEND_PATH=/var/www/TEMPLATE.WEB/admin-frontend/dist
FASTAPI_PORT=8000
```

### 2. 설정 파일 생성 및 적용

**설정 파일만 생성 (권장):**
```bash
cd nginx
python deploy_nginx.py
# 또는
python3 deploy_nginx.py
```

**자동으로 Nginx에 적용:**
```bash
cd nginx
python deploy_nginx.py --apply
# 또는
python3 deploy_nginx.py -a
```

자동 적용 시 다음 작업이 수행됩니다:
1. 설정 파일 생성
2. `/etc/nginx/sites-available/`에 복사
3. `/etc/nginx/sites-enabled/`에 심볼릭 링크 생성
4. Nginx 설정 검증 (`nginx -t`)
5. Nginx 재시작 (`systemctl reload nginx`)

**참고:** 
- 템플릿 파일은 `%{VAR}%` 형식을 사용합니다
- 자동 적용은 Linux/Mac에서만 지원됩니다 (sudo 권한 필요)
- `nginx.env`에 `NGINX_PROJECT_NAME`을 설정하면 프로젝트별로 다른 이름 사용 가능

### 3. 수동으로 Nginx에 적용 (선택사항)

자동 적용을 사용하지 않는 경우:

```bash
# 생성된 설정 파일 확인
cat nginx.conf.generated

# Nginx 설정 디렉토리로 복사
sudo cp nginx.conf.generated /etc/nginx/sites-available/your-project.conf

# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/your-project.conf /etc/nginx/sites-enabled/

# 설정 파일 검증
sudo nginx -t

# Nginx 재시작
sudo systemctl reload nginx
```

## 환경 변수 설명

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `NGINX_LISTEN_PORT` | Nginx 리스닝 포트 | 80 |
| `NGINX_MAIN_DOMAIN` | 메인 도메인 (실제 서비스) | - |
| `NGINX_ADMIN_DOMAIN` | 관리자 페이지 도메인 | - |
| `NGINX_MAIN_FRONTEND_PATH` | 메인 프론트엔드 빌드 경로 | - |
| `NGINX_ADMIN_FRONTEND_PATH` | 관리자 페이지 빌드 경로 | - |
| `FASTAPI_PORT` | FastAPI 백엔드 포트 | 8000 |
| `NGINX_PROJECT_NAME` | Nginx 설정 파일 이름 (자동 적용 시) | your-project |

## 템플릿 형식

템플릿 파일은 `%{VAR}%` 형식을 사용합니다:
- `%{NGINX_MAIN_DOMAIN}%` - 환경 변수 치환
- `%{FASTAPI_PORT:-8000}%` - 기본값 포함 (환경 변수가 없으면 8000 사용)

## 주의사항

- `nginx.env` 파일은 프로젝트별로 다르므로 버전 관리에 포함하지 마세요
- `.gitignore`에 `nginx.env`와 `nginx.conf.generated`를 추가하는 것을 권장합니다
- `envsubst`는 `${VAR}` 형식만 지원하므로 이 템플릿과는 호환되지 않습니다
