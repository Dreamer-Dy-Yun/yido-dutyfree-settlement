import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  systemAdminLogout,
  getCurrentSystemAdmin,
  verifyPassword,
  updateSystemAdminProfile,
  changePassword,
} from '../../services/auth';
import useSessionTTL from '../../hooks/useSessionTTL';
import ProfileModal from '../../components/ProfileModal';
import Sidebar from '../../components/Sidebar';
import AppHeader from '../../components/AppHeader';
import './AppLayout.css';

const DEFAULT_TITLE = '구매대행B2C';
const ADMIN_TITLE = '구매대행B2C-SYSADMIN';

const pageTitles = {
  '/admin': '대시보드',
};

function SystemAdminLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(null);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const { ttl, minutes, seconds } = useSessionTTL();

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentSystemAdmin();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  };

  useEffect(() => {
    document.title = ADMIN_TITLE;
    return () => {
      document.title = DEFAULT_TITLE;
    };
  }, []);

  useEffect(() => {
    const initializeCurrentUser = async () => {
      try {
        const user = await getCurrentSystemAdmin();
        setCurrentUser(user);
      } catch (err) {
        console.error('Failed to load current user:', err);
      }
    };
    initializeCurrentUser();
  }, []);

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

    if (location.pathname.startsWith('/admin/tenants')) {
      return '테넌트 관리';
    }
    if (location.pathname.startsWith('/admin/service-accounts')) {
      return '서비스 어카운트 관리';
    }
    if (location.pathname.startsWith('/admin/llm-api-keys')) {
      return 'API KEY 관리';
    }
    if (location.pathname.startsWith('/admin/prompts')) {
      return '프롬프트 관리';
    }

    return '시스템 관리';
  };

  const isOnDashboard = location.pathname === '/admin';

  return (
    <div className="app-layout">
      <Sidebar variant="system-admin" />
      <div className="app-main">
        <AppHeader
          title={getPageTitle()}
          sticky={true}
          showHomeButton={true}
          isHomeCurrent={isOnDashboard}
          onHomeClick={() => navigate('/admin')}
          homeTitle={isOnDashboard ? '이미 홈 화면입니다' : '대시보드로 이동'}
          onOpenProfile={() => setProfileModalOpen(true)}
          displayName={getDisplayName()}
          department={currentUser?.department}
          email={currentUser?.e_mail}
          minutes={ttl !== null ? minutes : undefined}
          seconds={ttl !== null ? seconds : undefined}
          onLogout={handleLogout}
        />
        <main className="app-content">{children}</main>
      </div>

      <ProfileModal
        open={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        user={currentUser}
        variant="system_admin"
        onVerifyPassword={verifyPassword}
        onUpdateProfile={updateSystemAdminProfile}
        onChangePassword={changePassword}
        onSaved={loadCurrentUser}
      />
    </div>
  );
}

export default SystemAdminLayout;
