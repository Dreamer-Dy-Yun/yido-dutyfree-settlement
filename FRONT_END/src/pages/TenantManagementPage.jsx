import { useState, useEffect } from 'react';
import { getCurrentUser } from '../services/auth';
import Sidebar from '../components/Sidebar';
import './TenantManagementPage.css';

function TenantManagementPage() {
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    loadCurrentUser();
  }, []);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  };

  const isAdmin = currentUser?.role === 'admin';

  return (
    <div className="tenant-management-page">
      <Sidebar isAdmin={isAdmin} />
      <div className="page-header">
        <h1>테넌트 관리</h1>
      </div>
      <div className="page-content">
        <p>테넌트 관리 기능은 준비 중입니다.</p>
      </div>
    </div>
  );
}

export default TenantManagementPage;
