import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { logout } from '../api/auth/authApi';
import useCurrentUser from '../hooks/useCurrentUser';
import Sidebar from './Sidebar';
import SessionHeader from './SessionHeader';
import '../styles/appLayout.css';
import '../styles/commonUi.css';

function DashboardShell({
  title,
  children,
  contentClassName = '',
  requireAdmin = false,
  unauthorizedPath = '/dashboard/data-mapping',
}) {
  const navigate = useNavigate();
  const { currentUser, isAdmin, loadCurrentUser } = useCurrentUser();
  const mainClassName = ['app-content', contentClassName].filter(Boolean).join(' ');

  useEffect(() => {
    if (requireAdmin && currentUser && currentUser.role !== 'admin') {
      navigate(unauthorizedPath, { replace: true });
    }
  }, [currentUser, navigate, requireAdmin, unauthorizedPath]);

  return (
    <div className="app-layout">
      <Sidebar isAdmin={isAdmin} />
      <div className="app-main">
        <SessionHeader
          title={title}
          currentUser={currentUser}
          onLogout={logout}
          onProfileUpdated={loadCurrentUser}
        />
        <main className={mainClassName}>{children}</main>
      </div>
    </div>
  );
}

export default DashboardShell;
