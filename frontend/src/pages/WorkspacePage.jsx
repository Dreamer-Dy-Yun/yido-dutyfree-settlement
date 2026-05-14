import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { logout, getCurrentUser } from '../api/authApi';
import {
  getTenantUsers,
  createTenantUser,
  updateTenantUser,
  userActivate,
  deleteTenantUser,
  resetUserPassword,
  getUsage,
} from '../api/tenantApi';
import Sidebar from '../components/Sidebar';
import SessionHeader from '../components/SessionHeader';
import CommonTabsRow from '../components/CommonTabsRow';
import WorkspaceUsersSection from './workspace/WorkspaceUsersSection';
import WorkspaceUsageSection from './workspace/WorkspaceUsageSection';
import WorkspaceUserModal from './workspace/WorkspaceUserModal';
import WorkspaceDeleteConfirmModal from './workspace/WorkspaceDeleteConfirmModal';
import './WorkspacePage.css';

const EMPTY_USER_FORM = {
  name: '',
  e_mail: '',
  password: '',
  passwordConfirm: '',
  role: 'user',
  department: '',
  contact: '',
};

function WorkspacePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState(new URLSearchParams(location.search).get('tab') || 'users');

  const isAdmin = currentUser?.role === 'admin';
  const [users, setUsers] = useState([]);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false);
  const [deletingUser, setDeletingUser] = useState(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isDeletingUser, setIsDeletingUser] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userFormData, setUserFormData] = useState(EMPTY_USER_FORM);

  const loadCurrentUser = useCallback(async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  }, []);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTenantUsers();
      setUsers(data.users || data);
    } catch (err) {
      setError(err.response?.data?.detail || '유저 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUsage = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUsage();
      setUsage(data);
    } catch (err) {
      setError(err.response?.data?.detail || '사용량을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  useEffect(() => {
    if (currentUser && currentUser.role !== 'admin') {
      navigate('/dashboard/data-mapping', { replace: true });
    }
  }, [currentUser, navigate]);

  useEffect(() => {
    const nextParams = new URLSearchParams(location.search);
    setActiveTab(nextParams.get('tab') || 'users');
  }, [location.search]);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'usage') {
      loadUsage();
    }
  }, [activeTab, loadUsage, loadUsers]);

  const handleCreateUser = () => {
    setEditingUser(null);
    setUserFormData(EMPTY_USER_FORM);
    setShowUserModal(true);
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    setUserFormData({
      name: user.name || '',
      e_mail: user.e_mail || '',
      password: '',
      passwordConfirm: '',
      role: user.role || 'user',
      department: user.department || '',
      contact: user.contact || '',
    });
    setShowUserModal(true);
  };

  const handleSaveUser = async () => {
    setError(null);
    if (!editingUser) {
      if (!userFormData.password || !userFormData.passwordConfirm) {
        setError('비밀번호와 비밀번호 확인을 모두 입력해주세요');
        return;
      }
      if (userFormData.password !== userFormData.passwordConfirm) {
        setError('비밀번호가 일치하지 않습니다');
        return;
      }
    }

    try {
      const dataToSend = { ...userFormData };
      delete dataToSend.passwordConfirm;
      if (editingUser) {
        await updateTenantUser(editingUser.id, dataToSend);
      } else {
        await createTenantUser(dataToSend);
      }
      setShowUserModal(false);
      await loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || '유저 저장에 실패했습니다');
    }
  };

  const handleUserActivation = async (user) => {
    const actionLabel = user.is_active ? '비활성화' : '활성화';
    if (!window.confirm(`정말 이 유저를 ${actionLabel}하시겠습니까?`)) return;
    try {
      await userActivate(user.id, !user.is_active);
      await loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || '유저 활성 상태 변경에 실패했습니다');
    }
  };

  const handleDeleteUser = (user) => {
    setError(null);
    setDeletingUser(user);
    setDeleteConfirmText('');
    setShowDeleteConfirmModal(true);
  };

  const closeDeleteConfirmModal = () => {
    if (isDeletingUser) return;
    setShowDeleteConfirmModal(false);
    setDeletingUser(null);
    setDeleteConfirmText('');
  };

  const handleConfirmDeleteUser = async () => {
    if (!deletingUser || deleteConfirmText.trim() !== '지금 삭제') return;

    setIsDeletingUser(true);
    try {
      await deleteTenantUser(deletingUser.id);
      closeDeleteConfirmModal();
      await loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || '유저 삭제에 실패했습니다');
    } finally {
      setIsDeletingUser(false);
    }
  };

  const handleResetPassword = async (userId) => {
    const message = '해당 유저의 비밀번호를 임시 비밀번호로 재설정하고,\n등록된 이메일로 발송하시겠습니까?';
    if (!window.confirm(message)) return;

    try {
      await resetUserPassword(userId);
      alert('임시 비밀번호가 등록된 이메일로 발송되었습니다');
    } catch (err) {
      setError(err.response?.data?.detail || '비밀번호 재설정에 실패했습니다');
    }
  };

  return (
    <div className="app-layout">
      <Sidebar isAdmin={isAdmin} />
      <div className="app-main">
        <SessionHeader
          title="테넌트 관리"
          currentUser={currentUser}
          onLogout={logout}
          onProfileUpdated={loadCurrentUser}
        />

        <main className="app-content workspace-content">
          <CommonTabsRow
            tabs={[
              { key: 'users', label: '유저 관리' },
              { key: 'usage', label: '사용량 조회' },
            ]}
            activeKey={activeTab}
            onTabChange={(nextTab) => {
              setActiveTab(nextTab);
              navigate(nextTab === 'usage' ? '/dashboard?tab=usage' : '/dashboard');
            }}
          />

          {error && <div className="workspace-error-message">{error}</div>}

          {activeTab === 'users' && (
            <WorkspaceUsersSection
              loading={loading}
              users={users}
              onCreateUser={handleCreateUser}
              onEditUser={handleEditUser}
              onToggleUserActivation={handleUserActivation}
              onDeleteUser={handleDeleteUser}
              onResetPassword={handleResetPassword}
            />
          )}

          {activeTab === 'usage' && <WorkspaceUsageSection loading={loading} usage={usage} />}

          {showUserModal && (
            <WorkspaceUserModal
              editingUser={editingUser}
              userFormData={userFormData}
              onChangeForm={setUserFormData}
              onClose={() => setShowUserModal(false)}
              onSave={handleSaveUser}
            />
          )}

          {showDeleteConfirmModal && deletingUser && (
            <WorkspaceDeleteConfirmModal
              deletingUser={deletingUser}
              deleteConfirmText={deleteConfirmText}
              isDeletingUser={isDeletingUser}
              onChangeConfirmText={setDeleteConfirmText}
              onClose={closeDeleteConfirmModal}
              onConfirm={handleConfirmDeleteUser}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default WorkspacePage;
