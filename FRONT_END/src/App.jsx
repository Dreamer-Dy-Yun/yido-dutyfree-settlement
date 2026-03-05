import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { isSuperuser } from './services/auth';
import LoginPage from './pages/LoginPage';
import SystemAdminLoginPage from './pages/SystemAdminLoginPage';
import CompanyRegisterPage from './pages/CompanyRegisterPage';
import WorkspacePage from './pages/WorkspacePage';
import TenantManagementPage from './pages/TenantManagementPage';
import DataMappingPage from './pages/DataMappingPage';
import SystemAdminDashboard from './admin/pages/SystemAdminDashboard';
import TenantListPage from './admin/pages/TenantListPage';
import TenantDetailPage from './admin/pages/TenantDetailPage';
import ServiceAccountListPage from './admin/pages/ServiceAccountListPage';
import ServiceAccountDetailPage from './admin/pages/ServiceAccountDetailPage';
import LlmApiKeyListPage from './admin/pages/LlmApiKeyListPage';
import LlmApiKeyCreatePage from './admin/pages/LlmApiKeyCreatePage';
import PromptListPage from './admin/pages/PromptListPage';
import PromptCreatePage from './admin/pages/PromptCreatePage';
import PromptDetailPage from './admin/pages/PromptDetailPage';
import SystemAdminLayout from './admin/components/SystemAdminLayout';
import ProtectedRoute from './common/components/ProtectedRoute';
import './App.css';

// 공개 라우트 컴포넌트 (이미 로그인한 경우 리다이렉트, 단 로그인 페이지와 회사 등록 페이지는 제외)
const PublicRoute = ({ children, skipRedirect = false }) => {
  if (skipRedirect) {
    return children;
  }
  // /admin/login 전용: 시스템 관리자 로그인 여부만 확인
  if (isSuperuser()) {
    return <Navigate to="/admin" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <PublicRoute skipRedirect={true}>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/login"
          element={
            <PublicRoute skipRedirect={true}>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/admin/login"
          element={
            <PublicRoute>
              <SystemAdminLoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/company/register"
          element={
            <PublicRoute skipRedirect={true}>
              <CompanyRegisterPage />
            </PublicRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <WorkspacePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/tenant"
          element={
            <ProtectedRoute>
              <TenantManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/data-mapping"
          element={
            <ProtectedRoute>
              <DataMappingPage />
            </ProtectedRoute>
          }
        />
        {/* 시스템 어드민 라우트 */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <SystemAdminDashboard />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/tenants"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <TenantListPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/tenants/pending"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <TenantListPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/tenants/:tenantId"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <TenantDetailPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/service-accounts"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <ServiceAccountListPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/service-accounts/:accountId"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <ServiceAccountDetailPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/llm-api-keys"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <LlmApiKeyListPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/llm-api-keys/new"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <LlmApiKeyCreatePage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/llm-api-keys/:apiKeyId/edit"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <LlmApiKeyCreatePage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/prompts"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <PromptListPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/prompts/new"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <PromptCreatePage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/prompts/:promptId"
          element={
            <ProtectedRoute requireSuperuser>
              <SystemAdminLayout>
                <PromptDetailPage />
              </SystemAdminLayout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
