import { Navigate } from 'react-router-dom';
import { isAuthenticated, isSuperuser } from '../../services/auth';

/**
 * 보호된 라우트 컴포넌트
 * 인증이 필요한 페이지에 사용
 */
function ProtectedRoute({ children, requireSuperuser = false }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  // 시스템 어드민 권한이 필요한 경우 체크
  if (requireSuperuser && !isSuperuser()) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export default ProtectedRoute;
