import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { isAuthenticated } from './services/auth';
import CompanySelectionPage from './pages/CompanySelectionPage';
import LoginPage from './pages/LoginPage';
import CompanyRegisterPage from './pages/CompanyRegisterPage';
import TenantAdminPage from './pages/TenantAdminPage';
import './App.css';

// 보호된 라우트 컴포넌트
const ProtectedRoute = ({ children }) => {
  return isAuthenticated() ? children : <Navigate to="/" replace />;
};

// 공개 라우트 컴포넌트 (이미 로그인한 경우 리다이렉트)
const PublicRoute = ({ children }) => {
  return !isAuthenticated() ? children : <Navigate to="/dashboard" replace />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <PublicRoute>
              <CompanySelectionPage />
            </PublicRoute>
          }
        />
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/company/register"
          element={
            <PublicRoute>
              <CompanyRegisterPage />
            </PublicRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <TenantAdminPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
