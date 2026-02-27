import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { systemAdminLogout, getCurrentSystemAdmin } from '../../services/auth';
import useSessionTTL from '../../hooks/useSessionTTL';
import './AdminLayout.css';

const pageTitles = {
  '/admin': '대시보드',
  '/admin/tenants': '테넌트 목록',
  '/admin/tenants/pending': '승인 대기 목록',
  '/admin/service-accounts': '서비스 어카운트',
};

function AdminLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(null);
  const { ttl, minutes, seconds } = useSessionTTL();

  useEffect(() => {
    loadCurrentUser();
  }, []);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentSystemAdmin();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  };

  const handleLogout = async () => {
    await systemAdminLogout();
  };

  const getDisplayName = () => {
    if (!currentUser) return '관리자';
    const { name, alias } = currentUser;

    if (name && alias && name !== alias) {
      return `${name} (${alias})`;
    }
    return name || alias || '관리자';
  };

  const getPageTitle = () => {
    if (pageTitles[location.pathname]) {
      return pageTitles[location.pathname];
    }

    if (
      location.pathname.startsWith('/admin/tenants/') &&
      location.pathname !== '/admin/tenants/pending'
    ) {
      return '테넌트 상세';
    }
    if (location.pathname.startsWith('/admin/service-accounts/')) {
      return '서비스 어카운트 상세';
    }

    return '시스템 관리';
  };

  const isOnDashboard = location.pathname === '/admin';

  return (
    <div className="admin-layout">
      <header className="admin-header">
        <div className="header-left">
          <button
            className={`btn-home ${isOnDashboard ? 'btn-home--current' : ''}`}
            onClick={isOnDashboard ? undefined : () => navigate('/admin')}
            title={isOnDashboard ? '이미 홈 화면입니다' : '대시보드로 이동'}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                cx="10"
                cy="10"
                r="8"
                stroke="currentColor"
                strokeWidth="1.5"
                fill={isOnDashboard ? 'currentColor' : 'none'}
              />
            </svg>
          </button>
          <h1 className="page-title">{getPageTitle()}</h1>
        </div>
        <div className="header-right">
          {currentUser && (
            <div className="user-info">
              <div className="user-details">
                <span className="user-name">{getDisplayName()}</span>
                {currentUser.department && (
                  <span className="user-department">{currentUser.department}</span>
                )}
                <span className="user-email">{currentUser.e_mail}</span>
                {ttl !== null && (
                  <span className="session-timer">
                    세션 남은 시간:{' '}
                    <strong>
                      {minutes}분 {String(seconds).padStart(2, '0')}초
                    </strong>
                  </span>
                )}
              </div>
              <button className="btn-logout" onClick={handleLogout}>
                로그아웃
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="admin-content">{children}</main>
    </div>
  );
}

export default AdminLayout;

