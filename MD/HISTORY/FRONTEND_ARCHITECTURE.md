# 프론트엔드 아키텍처 설계

## 개요

프론트엔드는 사용자 역할에 따라 **3가지 독립적인 애플리케이션**으로 분리하여 구성합니다.

1. **시스템 어드민 (System Admin)** - 서비스 제공사 관리자용
2. **테넌트 어드민 (Tenant Admin)** - 각 회사(테넌트) 관리자용
3. **작업 화면 (Work Screen)** - 일반 사용자 작업용

---

## 1. 시스템 어드민 (System Admin)

### 1.1 역할 및 권한
- **대상**: 서비스 제공사 관리자 (`is_superuser = True`)
- **권한**: 전체 테넌트 관리, 승인/거부, 시스템 설정
- **접근**: `https://admin.yido-dutyfree.com` 또는 `/admin` 경로

### 1.2 주요 기능

#### 테넌트 관리
- ✅ 신규 회사 등록 요청 목록 조회
- ✅ 테넌트 승인 (`POST /api/admin/tenants/{tenant_id}/approve`)
- ✅ 테넌트 거부 (`POST /api/admin/tenants/{tenant_id}/reject`)
- ✅ 테넌트 목록 조회 (`GET /api/admin/tenants`)
- ✅ 승인 대기 테넌트 필터링 (`GET /api/admin/tenants/pending`)

#### 시스템 설정
- ✅ 전체 테넌트 통계
- ✅ 시스템 사용량 모니터링
- ✅ 글로벌 설정 관리

### 1.3 기술 스택
- **라우팅**: `/admin/*` 경로
- **인증**: `get_current_superuser` 의존성
- **API Base**: `/api/admin/*`

### 1.4 디렉토리 구조 (제안)
```
FRONT_END/
├── src/
│   ├── admin/                    # 시스템 어드민 전용
│   │   ├── pages/
│   │   │   ├── TenantListPage.jsx
│   │   │   ├── TenantApprovalPage.jsx
│   │   │   ├── SystemSettingsPage.jsx
│   │   │   └── DashboardPage.jsx
│   │   ├── components/
│   │   │   ├── TenantCard.jsx
│   │   │   ├── ApprovalModal.jsx
│   │   │   └── StatisticsWidget.jsx
│   │   ├── services/
│   │   │   └── adminApi.js
│   │   └── routes.jsx
│   └── ...
```

---

## 2. 테넌트 어드민 (Tenant Admin)

### 2.1 역할 및 권한
- **대상**: 각 테넌트(회사)의 관리자 (`role = "admin"`, `tenant_id` 소속)
- **권한**: 자신의 테넌트 내 사용자 관리, 설정, 데이터 조회
- **접근**: `https://app.yido-dutyfree.com/dashboard` 또는 `/dashboard` 경로

### 2.2 주요 기능

#### 사용자 관리
- ✅ 사용자 목록 조회 (`GET /api/tenant/users`)
- ✅ 사용자 생성 (`POST /api/tenant/users`)
- ✅ 사용자 수정 (`PUT /api/tenant/users/{user_id}`)
- ✅ 사용자 비활성화/삭제

#### 테넌트 설정
- ✅ 회사 정보 수정
- ✅ 테넌트별 설정 관리
- ✅ 부서/팀 관리

#### 데이터 조회
- ✅ OCR 결과 조회 (자신의 테넌트 스키마)
- ✅ 영수증/여권 데이터 통계
- ✅ 사용량 리포트

### 2.3 기술 스택
- **라우팅**: `/dashboard/*` 경로
- **인증**: `get_current_tenant_admin` 의존성
- **API Base**: `/api/tenant/*`
- **스키마**: 각 테넌트의 전용 스키마 (`tenant_schema`)

### 2.4 디렉토리 구조 (제안)
```
FRONT_END/
├── src/
│   ├── tenant-admin/             # 테넌트 어드민 전용
│   │   ├── pages/
│   │   │   ├── UserManagementPage.jsx
│   │   │   ├── TenantSettingsPage.jsx
│   │   │   ├── DataOverviewPage.jsx
│   │   │   └── ReportsPage.jsx
│   │   ├── components/
│   │   │   ├── UserTable.jsx
│   │   │   ├── UserForm.jsx
│   │   │   └── DataChart.jsx
│   │   ├── services/
│   │   │   └── tenantApi.js
│   │   └── routes.jsx
│   └── ...
```

---

## 3. 작업 화면 (Work Screen)

### 3.1 역할 및 권한
- **대상**: 일반 사용자 (`role = "user"`, `tenant_id` 소속)
- **권한**: 자신의 작업 데이터 입력/조회, OCR 결과 확인
- **접근**: `https://app.yido-dutyfree.com/work` 또는 `/work` 경로

### 3.2 주요 기능

#### OCR 작업
- ✅ 이미지 업로드 (여권/영수증)
- ✅ OCR 결과 확인 및 수정
- ✅ 검증 완료 데이터 제출

#### 데이터 조회
- ✅ 자신이 처리한 데이터 목록
- ✅ 검증 대기/완료 상태 필터링
- ✅ 개인 작업 통계

#### 프로필 관리
- ✅ 비밀번호 변경
- ✅ 개인 정보 수정

### 3.3 기술 스택
- **라우팅**: `/work/*` 경로
- **인증**: `get_current_active_user` 의존성
- **API Base**: `/api/work/*` 또는 테넌트별 API
- **스키마**: 각 테넌트의 전용 스키마 (`tenant_schema`)

### 3.4 디렉토리 구조 (제안)
```
FRONT_END/
├── src/
│   ├── work/                     # 작업 화면 전용
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx
│   │   │   ├── OcrResultPage.jsx
│   │   │   ├── DataListPage.jsx
│   │   │   └── ProfilePage.jsx
│   │   ├── components/
│   │   │   ├── ImageUploader.jsx
│   │   │   ├── OcrViewer.jsx
│   │   │   ├── DataTable.jsx
│   │   │   └── VerificationForm.jsx
│   │   ├── services/
│   │   │   └── workApi.js
│   │   └── routes.jsx
│   └── ...
```

---

## 4. 공통 인증 및 라우팅

### 4.1 인증 플로우

```
1. 회사 선택 화면 (공개)
   └─> /company/register (신규 회사 등록)

2. 로그인 화면 (공개)
   └─> JWT 토큰 발급
       ├─> role + is_superuser 확인
       │
       ├─> is_superuser = True
       │   └─> /admin/* (시스템 어드민)
       │
       ├─> role = "admin"
       │   └─> /dashboard/* (테넌트 어드민)
       │
       └─> role = "user"
           └─> /work/* (작업 화면)
```

### 4.2 라우팅 구조 (제안)

```jsx
// App.jsx
<Router>
  <Routes>
    {/* 공개 라우트 */}
    <Route path="/" element={<CompanySelectionPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/company/register" element={<CompanyRegisterPage />} />
    
    {/* 시스템 어드민 라우트 */}
    <Route path="/admin/*" element={
      <ProtectedRoute requireSuperuser>
        <AdminApp />
      </ProtectedRoute>
    } />
    
    {/* 테넌트 어드민 라우트 */}
    <Route path="/dashboard/*" element={
      <ProtectedRoute requireAdmin>
        <TenantAdminApp />
      </ProtectedRoute>
    } />
    
    {/* 작업 화면 라우트 */}
    <Route path="/work/*" element={
      <ProtectedRoute>
        <WorkApp />
      </ProtectedRoute>
    } />
  </Routes>
</Router>
```

### 4.3 공통 컴포넌트

```
FRONT_END/
├── src/
│   ├── common/                   # 공통 모듈
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Header.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   └── Footer.jsx
│   │   │   ├── Auth/
│   │   │   │   ├── ProtectedRoute.jsx
│   │   │   │   └── RoleGuard.jsx
│   │   │   └── UI/
│   │   │       ├── Button.jsx
│   │   │       ├── Input.jsx
│   │   │       └── Modal.jsx
│   │   ├── services/
│   │   │   ├── api.js            # 공통 API 클라이언트
│   │   │   └── auth.js           # 인증 서비스
│   │   ├── hooks/
│   │   │   ├── useAuth.js
│   │   │   └── useTenant.js
│   │   └── utils/
│   │       ├── constants.js
│   │       └── helpers.js
│   └── ...
```

---

## 5. 구현 단계 (제안)

### Phase 1: 기본 구조 설정
- [ ] 라우팅 구조 설계 및 적용
- [ ] 인증 미들웨어 구현 (`ProtectedRoute`, `RoleGuard`)
- [ ] 공통 레이아웃 컴포넌트 생성
- [ ] API 클라이언트 분리 (admin, tenant, work)

### Phase 2: 시스템 어드민 구현
- [ ] 테넌트 목록/승인 페이지
- [ ] 시스템 설정 페이지
- [ ] 통계 대시보드

### Phase 3: 테넌트 어드민 구현
- [ ] 사용자 관리 페이지
- [ ] 테넌트 설정 페이지
- [ ] 데이터 조회/리포트 페이지

### Phase 4: 작업 화면 구현
- [ ] 이미지 업로드/OCR 결과 페이지
- [ ] 데이터 목록/검증 페이지
- [ ] 프로필 관리 페이지

---

## 6. 보안 고려사항

### 6.1 역할 기반 접근 제어 (RBAC)
- **프론트엔드**: 라우트 가드로 UI 접근 차단
- **백엔드**: API 엔드포인트에서 역할 검증 (이중 방어)

### 6.2 JWT 토큰 관리
- 토큰에 `role`, `tenant_id`, `is_superuser` 포함
- 토큰 만료 시 자동 로그아웃 및 리다이렉트
- 리프레시 토큰 전략 고려

### 6.3 테넌트 격리
- 각 테넌트는 자신의 스키마만 접근
- API 요청 시 `tenant_id` 자동 주입
- 크로스 테넌트 데이터 접근 방지

---

## 7. 상태 관리 (제안)

### 7.1 전역 상태
- **인증 상태**: `useAuth` 훅 또는 Context API
- **테넌트 정보**: `useTenant` 훅
- **사용자 정보**: JWT 디코딩 또는 API 조회

### 7.2 로컬 상태
- 각 앱별로 독립적인 상태 관리
- 필요 시 Redux/Zustand 도입 고려

---

## 8. 배포 전략

### 8.1 단일 앱 vs 멀티 앱
- **옵션 A**: 단일 React 앱 내에서 경로로 분리 (현재 구조 유지)
- **옵션 B**: 완전히 독립된 3개 앱으로 분리 (별도 빌드/배포)

### 8.2 권장사항
- 초기에는 **옵션 A**로 시작 (빠른 개발, 코드 공유 용이)
- 규모 확대 시 **옵션 B**로 마이그레이션 고려

---

## 9. 참고사항

- 백엔드 API 엔드포인트는 이미 역할별로 분리되어 있음:
  - `/api/admin/*` - 시스템 어드민
  - `/api/tenant/*` - 테넌트 관리
  - `/api/work/*` 또는 테넌트별 API - 작업 화면
- 현재 프론트엔드는 기본 라우팅만 구현된 상태
- 점진적으로 각 앱별 기능을 추가 구현 예정

---

**작성일**: 2026-02-24  
**작성자**: Cursor AI  
**버전**: 1.0.0
