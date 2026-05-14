import { Navigate } from 'react-router-dom';
import { isAuthenticated, isSuperuser } from '../../api/authApi';

/**
 * 보호된 라우트 컴포넌트
 * 인증이 필요한 페이지에 사용
 */
function ProtectedRoute({ children, requireSuperuser = false }) {
  if (requireSuperuser) {
    if (!isSuperuser()) {
      return <Navigate to="/admin/login" replace />;
    }
    return children;
  }

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
