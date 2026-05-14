import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { logout, getCurrentUser } from '../services/auth';
import {
  getTenantUsers,
  createTenantUser,
  updateTenantUser,
  userActivate,
  deleteTenantUser,
  resetUserPassword,
  getUsage,
} from '../services/tenant';
import Sidebar from '../components/Sidebar';
import SessionHeader from '../components/SessionHeader';
import CommonTabsRow from '../components/CommonTabsRow';
import './WorkspacePage.css';

function WorkspacePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);

  const searchParams = new URLSearchParams(location.search);
  const tabFromUrl = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(tabFromUrl || 'users');

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
  const [userFormData, setUserFormData] = useState({
    name: '',
    e_mail: '',
    password: '',
    passwordConfirm: '',
    role: 'user',
    department: '',
    contact: '',
  });

  useEffect(() => {
    loadCurrentUser();
  }, []);

  useEffect(() => {
    if (currentUser && currentUser.role !== 'admin') {
      navigate('/dashboard/data-mapping', { replace: true });
    }
  }, [currentUser, navigate]);

  useEffect(() => {
    const nextParams = new URLSearchParams(location.search);
    const nextTab = nextParams.get('tab') || 'users';
    setActiveTab(nextTab);
  }, [location.search]);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'usage') {
      loadUsage();
    }
  }, [activeTab]);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  };

  const loadUsers = async () => {
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
  };

  const loadUsage = async () => {
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
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleCreateUser = () => {
    setEditingUser(null);
    setUserFormData({
      name: '',
      e_mail: '',
      password: '',
      passwordConfirm: '',
      role: 'user',
      department: '',
      contact: '',
    });
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
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || '유저 저장에 실패했습니다');
    }
  };

  const handleUserActivation = async (user) => {
    const actionLabel = user.is_active ? '비활성화' : '활성화';
    if (!window.confirm(`정말 이 유저를 ${actionLabel}하시겠습니까?`)) {
      return;
    }
    try {
      await userActivate(user.id, !user.is_active);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || '유저 활성 상태 변경에 실패했습니다');
    }
  };

  const handleDeleteUser = async (user) => {
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
    if (!deletingUser) return;
    if (deleteConfirmText.trim() !== '지금 삭제') return;

    setIsDeletingUser(true);
    try {
      await deleteTenantUser(deletingUser.id);
      closeDeleteConfirmModal();
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || '유저 삭제에 실패했습니다');
    } finally {
      setIsDeletingUser(false);
    }
  };

  const handleResetPassword = async (userId) => {
    if (!window.confirm('해당 유저의 비밀번호를 임시 비밀번호로 재설정하고,\n등록된 이메일로 발송하시겠습니까?')) {
      return;
    }

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
          onLogout={handleLogout}
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
            <div className="workspace-users-section">
              <div className="workspace-section-header">
                <h2>유저 목록</h2>
                <button onClick={handleCreateUser} className="workspace-create-button">
                  유저 추가
                </button>
              </div>

              {loading ? (
                <div className="workspace-loading">로딩 중...</div>
              ) : (
                <table className="workspace-users-table">
                  <thead>
                    <tr>
                      <th>이름</th>
                      <th>이메일</th>
                      <th>역할</th>
                      <th>부서</th>
                      <th>연락처</th>
                      <th>상태</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.name}</td>
                        <td>{user.e_mail}</td>
                        <td>{user.role === 'admin' ? '관리자' : '유저'}</td>
                        <td>{user.department || '-'}</td>
                        <td>{user.contact || '-'}</td>
                        <td>
                          <span className={`workspace-status ${user.is_active ? 'active' : 'inactive'}`}>
                            {user.is_active ? '활성' : '비활성'}
                          </span>
                        </td>
                        <td>
                          <div className="workspace-user-action-buttons">
                            <button onClick={() => handleEditUser(user)} className="workspace-edit-button">
                              수정
                            </button>
                            <button
                              onClick={() => handleUserActivation(user)}
                              className={`workspace-activation-button ${user.is_active ? 'deactivate' : 'activate'}`}
                            >
                              {user.is_active ? '비활성화' : '활성화'}
                            </button>
                            <button onClick={() => handleDeleteUser(user)} className="workspace-delete-button">
                              삭제
                            </button>
                            <button
                              onClick={() => handleResetPassword(user.id)}
                              className="workspace-reset-button"
                            >
                              비밀번호 재설정
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {activeTab === 'usage' && (
            <div className="workspace-usage-section">
              <h2>사용량 조회</h2>
              {loading ? (
                <div className="workspace-loading">로딩 중...</div>
              ) : usage ? (
                <div className="workspace-usage-stats">
                  <div className="workspace-stat-card">
                    <div className="workspace-stat-label">이미지</div>
                    <div className="workspace-stat-value">{usage.total_images || 0}</div>
                  </div>
                  <div className="workspace-stat-card">
                    <div className="workspace-stat-label">OCR 여권</div>
                    <div className="workspace-stat-value">{usage.total_ocr_passport || 0}</div>
                  </div>
                  <div className="workspace-stat-card">
                    <div className="workspace-stat-label">OCR 영수증</div>
                    <div className="workspace-stat-value">{usage.total_ocr_receipt || 0}</div>
                  </div>
                  <div className="workspace-stat-card">
                    <div className="workspace-stat-label">검증된 여권</div>
                    <div className="workspace-stat-value">{usage.total_verified_passport || 0}</div>
                  </div>
                  <div className="workspace-stat-card">
                    <div className="workspace-stat-label">검증된 영수증</div>
                    <div className="workspace-stat-value">{usage.total_verified_receipt || 0}</div>
                  </div>
                  <div className="workspace-stat-card">
                    <div className="workspace-stat-label">매칭된 데이터</div>
                    <div className="workspace-stat-value">{usage.total_matched || 0}</div>
                  </div>
                  <div className="workspace-stat-card">
                    <div className="workspace-stat-label">LLM 토큰</div>
                    <div className="workspace-stat-value">{usage.total_llm_tokens || 0}</div>
                  </div>
                </div>
              ) : (
                <div className="workspace-no-data">데이터가 없습니다</div>
              )}
            </div>
          )}

          {showUserModal && (
            <div className="workspace-modal-overlay" onClick={() => setShowUserModal(false)}>
              <div className="workspace-modal-content" onClick={(e) => e.stopPropagation()}>
                <h2>{editingUser ? '유저 수정' : '유저 추가'}</h2>
                <div className="workspace-modal-form">
                  <div className="workspace-form-group">
                    <label>이름 *</label>
                    <input
                      type="text"
                      value={userFormData.name}
                      onChange={(e) => setUserFormData({ ...userFormData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="workspace-form-group">
                    <label>이메일 *</label>
                    <input
                      type="email"
                      value={userFormData.e_mail}
                      onChange={(e) => setUserFormData({ ...userFormData, e_mail: e.target.value })}
                      required
                    />
                  </div>
                  {!editingUser && (
                    <>
                      <div className="workspace-form-group">
                        <label>비밀번호 *</label>
                        <input
                          type="password"
                          value={userFormData.password}
                          onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value })}
                          required
                        />
                      </div>
                      <div className="workspace-form-group">
                        <label>비밀번호 확인 *</label>
                        <input
                          type="password"
                          value={userFormData.passwordConfirm}
                          onChange={(e) => setUserFormData({ ...userFormData, passwordConfirm: e.target.value })}
                          required
                        />
                        {userFormData.passwordConfirm && (
                          <div
                            className={`workspace-password-match-message ${
                              userFormData.password === userFormData.passwordConfirm ? 'match' : 'no-match'
                            }`}
                          >
                            {userFormData.password === userFormData.passwordConfirm
                              ? '✓ 비밀번호가 일치합니다'
                              : '✗ 비밀번호가 일치하지 않습니다'}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                  <div className="workspace-form-group">
                    <label>역할</label>
                    <select
                      value={userFormData.role}
                      onChange={(e) => setUserFormData({ ...userFormData, role: e.target.value })}
                    >
                      <option value="user">유저</option>
                      <option value="admin">관리자</option>
                    </select>
                  </div>
                  <div className="workspace-form-group">
                    <label>부서</label>
                    <input
                      type="text"
                      value={userFormData.department}
                      onChange={(e) => setUserFormData({ ...userFormData, department: e.target.value })}
                    />
                  </div>
                  <div className="workspace-form-group">
                    <label>연락처</label>
                    <input
                      type="text"
                      value={userFormData.contact}
                      onChange={(e) => setUserFormData({ ...userFormData, contact: e.target.value })}
                    />
                  </div>
                  <div className="workspace-modal-actions">
                    <button onClick={() => setShowUserModal(false)} className="workspace-cancel-button">
                      취소
                    </button>
                    <button onClick={handleSaveUser} className="workspace-save-button">
                      저장
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {showDeleteConfirmModal && deletingUser && (
            <div className="workspace-modal-overlay" onClick={closeDeleteConfirmModal}>
              <div className="workspace-modal-content workspace-delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
                <h2>유저 삭제 확인</h2>
                <p className="workspace-delete-confirm-text">
                  <strong>{deletingUser.name || deletingUser.e_mail}</strong> 유저를 삭제합니다.
                  삭제 후 복구할 수 없습니다.
                </p>
                <p className="workspace-delete-confirm-text">
                  삭제를 진행하려면 아래에 <strong>지금 삭제</strong>를 입력하세요.
                </p>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  placeholder='지금 삭제'
                  className="workspace-delete-confirm-input"
                  disabled={isDeletingUser}
                />
                <div className="workspace-modal-actions">
                  <button onClick={closeDeleteConfirmModal} className="workspace-cancel-button" disabled={isDeletingUser}>
                    취소
                  </button>
                  <button
                    onClick={handleConfirmDeleteUser}
                    className="workspace-delete-confirm-button"
                    disabled={isDeletingUser || deleteConfirmText.trim() !== '지금 삭제'}
                  >
                    {isDeletingUser ? '삭제 중...' : '삭제 확인'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default WorkspacePage;
