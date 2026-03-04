# 토큰 키 분리 구현 계획 (시스템 관리자 / 일반 유저 세션 공존)

## 목표
- **같은 브라우저(같은 origin)**에서 시스템 관리자 로그인과 일반(테넌트) 로그인이 **동시에 유효**하도록 함.
- 시스템 관리자가 로그인한 상태에서 `/` 또는 `/login`(일반 로그인 화면)에 들어가면 **로그인 폼이 보이고**, `/admin/login`에 들어가면 **시스템 관리자 로그인 폼이 보이지 않고 `/admin`으로 리다이렉트**되는 현재 동작은 유지 (이미 로그인된 경우에만 리다이렉트).

## 전제
- 백엔드는 이미 **시스템 관리자(`system_admin` 테이블)**와 **테넌트 유저(테넌트 스키마)**를 분리하고, `/api/auth/system-admin/*` vs `/api/auth/login` 등으로 엔드포인트가 나뉘어 있음.
- **프론트만 수정**하며, 백엔드 API 스펙(토큰 발급/검증 방식)은 변경하지 않음.

---

## 1. 저장소(키) 설계

| 구분 | 키 이름 | 설정 시점 | 삭제 시점 |
|------|---------|-----------|-----------|
| 테넌트(일반) | `access_token`, `tenant_id`, `tenant_schema` | 테넌트 로그인 성공 시 | 테넌트 로그아웃 시, 테넌트 API 401 시 |
| 시스템 관리자 | `admin_access_token` | 시스템 관리자 로그인 성공 시 | 시스템 관리자 로그아웃 시, 시스템 관리자 API 401 시 |

- 두 세션은 **동시에 존재 가능**하므로, 한쪽 로그인/로그아웃 시 **다른 쪽 키는 건드리지 않음**.

---

## 2. 수정 대상 파일 및 상세 변경 내용

### 2.1 `FRONT_END/src/services/auth.js`

| 위치 | 현행 | 변경 내용 |
|------|------|-----------|
| **login()** | `localStorage.setItem('access_token', ...)` 등 | 유지. `admin_access_token`은 건드리지 않음 (테넌트 로그인만 처리). |
| **logout()** | `access_token`, `tenant_id`, `tenant_schema` 제거 | 유지. **`admin_access_token`은 제거하지 않음.** |
| **systemAdminLogin()** | `localStorage.setItem('access_token', ...)` | **`localStorage.setItem('admin_access_token', response.data.access_token)`** 로 변경. `access_token`은 설정하지 않음. `tenant_id`, `tenant_schema` 제거하는 동작은 유지해도 됨(선택). |
| **systemAdminLogout()** | `access_token`, `tenant_id`, `tenant_schema` 제거 후 `window.location.href = '/'` | **`admin_access_token`만 제거.** `access_token` 등은 제거하지 않음. 리다이렉트는 `/` 또는 `/admin/login` 중 정책에 맞게 유지. |
| **getCurrentSystemAdmin()** | (api 사용) | 호출부 변경 없음. **api 요청 시 admin 토큰을 붙이도록 api.js에서 URL 기준 분기** (아래 2.2 참고). |
| **isAuthenticated()** | `!!localStorage.getItem('access_token')` | **그대로 유지.** “테넌트 유저로 로그인했는지”만 의미. |
| **getTokenPayload()** | `access_token` 기준 디코딩 | **그대로 유지.** 테넌트 토큰 payload 전용. |
| **추가** | - | **`isAdminAuthenticated()`** 추가: `return !!localStorage.getItem('admin_access_token');` |
| **추가** | - | **`getAdminTokenPayload()`** 추가 (필요 시): `admin_access_token`을 읽어 JWT payload 반환. |
| **isSuperuser()** | `getTokenPayload()`에서 `is_superuser`/`role` 확인 | **`return isAdminAuthenticated();`** 로 변경. (시스템 관리자 전용 로그인으로만 `admin_access_token`이 설정되므로, 존재 여부만으로 판단해도 됨.) |

- 정리: 테넌트는 기존 키·함수 유지, 시스템 관리자만 `admin_access_token` + `isAdminAuthenticated()`(및 필요 시 `getAdminTokenPayload()`)로 분리.

---

### 2.2 `FRONT_END/src/services/api.js`

| 위치 | 현행 | 변경 내용 |
|------|------|----------|
| **요청 인터셉터** | 모든 요청에 `localStorage.getItem('access_token')`을 Authorization에 설정 | **요청 URL에 따라 토큰 분기.** 예: `config.url`에 `'/api/auth/system-admin'` 또는 `'/api/system-admin'`가 포함되면 `admin_access_token` 사용, 그 외에는 `access_token` 사용. 사용한 토큰 종류를 **응답 인터셉터에서 구분할 수 있도록** `config._useAdminToken = true` 등 플래그를 설정. |
| **응답 인터셉터 (401)** | `access_token`, `tenant_id`, `tenant_schema` 제거 후 `window.location.href = '/'` | **요청 시 사용한 토큰만 제거.** `config._useAdminToken === true`이면 `admin_access_token`만 제거하고 리다이렉트는 `/admin/login` 또는 `/` 중 하나로. 그 외에는 기존처럼 `access_token` 등만 제거하고 `window.location.href = '/login'` 또는 `'/'` 유지. |

- 백엔드 prefix 정리 (참고):  
  - 시스템 관리자: `/api/auth` 아래 `.../system-admin/...`, `/api/system-admin/...`  
  - 테넌트/일반: 그 외 (`/api/auth/login`, `/api/tenant/...`, `/api/company/...` 등)

---

### 2.3 `FRONT_END/src/App.jsx`

| 위치 | 현행 | 변경 내용 |
|------|------|----------|
| **PublicRoute** | `isAuthenticated()`로 “로그인 여부” 판단, `isSuperuser()`로 `/admin` vs `/dashboard` 리다이렉트 | **`/admin/login` 전용 분기만 유지.** `skipRedirect === false`인 경우(현재는 `/admin/login`만 해당): **`isSuperuser()`(= 시스템 관리자 로그인 여부)만 확인.** true이면 `/admin`으로 리다이렉트, false이면 children(시스템 관리자 로그인 페이지) 표시. **`isAuthenticated()`는 이 경로에서는 사용하지 않음** (일반 로그인 여부와 무관하게 동작). |
| **`/`, `/login`** | `skipRedirect={true}` | 변경 없음. 이미 “이미 로그인돼 있어도 로그인 폼 표시”이므로, 테넌트·시스템 관리자 토큰 분리 후에도 동작 유지. |

- 요약: PublicRoute에서 “이미 로그인된 경우 리다이렉트”는 **시스템 관리자 로그인 페이지(`/admin/login`)에만** 적용하고, 그때는 **시스템 관리자 토큰(`isSuperuser()`)** 만 보면 됨.

---

### 2.4 `FRONT_END/src/common/components/ProtectedRoute.jsx`

| 위치 | 현행 | 변경 내용 |
|------|------|----------|
| **requireSuperuser === true** (예: `/admin/*`) | 먼저 `!isAuthenticated()`이면 `/login`으로, 그다음 `requireSuperuser && !isSuperuser()`이면 `/dashboard`로 | **시스템 관리자 전용 라우트는 “테넌트 로그인”을 보지 않음.** `requireSuperuser === true`이면 **`!isSuperuser()`일 때만** 검사하여 **`<Navigate to="/admin/login" />`** 로 보냄. `isAuthenticated()`는 **requireSuperuser일 때는 호출하지 않음.** |
| **requireSuperuser === false** (예: `/dashboard/*`) | `!isAuthenticated()`이면 `/login`으로 | 유지. **`isAuthenticated()`만 사용** (테넌트 토큰만 확인). |

- 정리:  
  - `/admin/*` → `isSuperuser()`만 보고, 미로그인 시 `/admin/login`.  
  - `/dashboard/*` → `isAuthenticated()`만 보고, 미로그인 시 `/login`.

---

### 2.5 `FRONT_END/src/pages/LoginPage.jsx`

| 위치 | 현행 | 변경 내용 |
|------|------|----------|
| **handleSubmit 내** | 로그인 성공 후 `localStorage.getItem('access_token')`으로 payload 확인, `is_superuser`/`role === 'system_admin'`이면 `/admin`으로 이동 | 테넌트 로그인 API는 **테넌트용 토큰만** 내려주므로, 이 분기(`/admin`으로 보내는 부분)는 **실제로 타지 않을 가능성이 높음.** 안전하게 유지하려면: **테넌트 로그인 성공 시에는 항상 `navigate('/dashboard')`만 수행**하도록 단순화하거나, 위 분기는 그대로 두어도 됨 (테넌트 토큰에는 보통 `role === 'system_admin'`이 없을 것이므로). **추가로 `access_token`이 아닌 다른 키를 참조하지 않도록** 확인만 하면 됨. |

- 이 파일에서는 **저장 키를 바꾸지 않음.** 테넌트 로그인은 계속 `access_token`만 사용.

---

### 2.6 기타 확인 사항 (변경 없거나 최소한)

- **`FRONT_END/src/services/sessionTTL.js`**  
  - 현재는 “마지막 API 응답” 기준으로 하나의 TTL만 유지.  
  - 토큰 분리 후에도, **admin 페이지에서는 admin API만**, **테넌트 페이지에서는 tenant API만** 호출되므로, 각 화면에서는 “해당 세션” TTL만 갱신되는 효과.  
  - **별도 수정 없이** 두어도 됨. 나중에 “admin/tenant TTL을 각각 표시”하려면 그때 admin/tenant 구분 로직 추가 가능.

- **`FRONT_END/src/admin/services/systemAdminApi.js`**  
  - 모두 `api` 인스턴스 사용, URL이 `/api/system-admin/...`이므로 **api.js 인터셉터에서 `admin_access_token`을 붙이도록만** 하면 됨. **이 파일 자체는 수정 불필요.**

- **`FRONT_END/src/hooks/useSessionTTL.js`**  
  - AdminLayout / TenantHeader에서 사용. 위와 같이 **지금은 수정하지 않아도 됨.**

---

## 3. 구현 순서 제안

1. **auth.js**  
   - `admin_access_token` 읽기/쓰기 추가.  
   - `systemAdminLogin` / `systemAdminLogout`를 위 표대로 수정.  
   - `isAdminAuthenticated()` 추가, `isSuperuser()`를 `isAdminAuthenticated()` 기반으로 변경.

2. **api.js**  
   - 요청 인터셉터: URL 기준으로 `access_token` vs `admin_access_token` 선택, 필요 시 `config._useAdminToken` 설정.  
   - 401 응답 시: `config._useAdminToken`에 따라 제거할 키와 리다이렉트 경로 분기.

3. **ProtectedRoute.jsx**  
   - `requireSuperuser === true`일 때는 `isSuperuser()`만 검사하고, 실패 시 `/admin/login`으로 리다이렉트.

4. **App.jsx**  
   - PublicRoute에서 `skipRedirect === false`인 경우, `isSuperuser()`만 사용하도록 정리.

5. **LoginPage.jsx**  
   - 테넌트 로그인 후 리다이렉트가 “항상 `/dashboard`”로만 가도 되는지 확인 후, 필요하면 단순화 (선택).

6. **동작 확인**  
   - 시스템 관리자 로그인 → `/admin` 정상, `/`/`/login` 접속 시 일반 로그인 폼 노출.  
   - 일반 로그인 → `/dashboard` 정상.  
   - 같은 브라우저에서 먼저 시스템 관리자 로그인 후 일반 로그인 화면 접속 시 로그인 폼 유지.  
   - 각각 로그아웃 시 해당 토큰만 제거되고, 다른 역할 세션은 유지되는지 확인.

---

## 4. 요약 표

| 파일 | 변경 요약 |
|------|-----------|
| **auth.js** | 테넌트는 `access_token` 유지. 시스템 관리자는 `admin_access_token` 사용. `isAdminAuthenticated()` 추가, `isSuperuser()`는 admin 토큰 존재 여부로 변경. 로그인/로그아웃 시 상대쪽 키는 건드리지 않음. |
| **api.js** | URL에 `/api/auth/system-admin` 또는 `/api/system-admin` 포함 시 `admin_access_token` 사용, 그 외 `access_token`. 401 시 사용한 토큰만 제거하고 해당 역할에 맞는 경로로 리다이렉트. |
| **App.jsx** | PublicRoute에서 `/admin/login`용 리다이렉트는 `isSuperuser()`만 사용하도록 정리. |
| **ProtectedRoute.jsx** | `requireSuperuser`일 때는 `isSuperuser()`만 검사, 실패 시 `/admin/login`으로. 테넌트 라우트는 `isAuthenticated()`만 검사. |
| **LoginPage.jsx** | 선택적 정리(테넌트 로그인 후 리다이렉트). 저장 키는 `access_token` 유지. |
| **sessionTTL / useSessionTTL / systemAdminApi.js** | 현행 유지. (api.js 분기만으로 동작 가능.) |

이 순서대로 적용하면, 포트를 나누지 않고도 “시스템 관리자”와 “일반 운영관리자/작업자” 세션이 같은 브라우저에서 공존할 수 있습니다.
