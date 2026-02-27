import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { logout, getCurrentUser } from '../services/auth';
import {
  getTenantUsers,
  createTenantUser,
  updateTenantUser,
  deleteTenantUser,
  resetUserPassword,
  getUsage,
  getUserTokenUsage,
} from '../services/tenant';
import Sidebar from '../components/Sidebar';
import TenantHeader from '../components/TenantHeader';
import './TenantAdminPage.css';

function TenantAdminPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);
  
  // URL 파라미터에서 탭 정보 가져오기
  const searchParams = new URLSearchParams(location.search);
  const tabFromUrl = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(tabFromUrl || 'users'); // 'users' or 'usage'
  
  // 관리자 권한 확인
  const isAdmin = currentUser?.role === 'admin';
  const [users, setUsers] = useState([]);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);
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
    // URL 파라미터 변경 시 탭 업데이트
    const searchParams = new URLSearchParams(location.search);
    const tabFromUrl = searchParams.get('tab') || 'users';
    setActiveTab(tabFromUrl);
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
    
    // 유저 추가 시 비밀번호 확인
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
      // passwordConfirm은 서버로 전송하지 않음
      const { passwordConfirm, ...dataToSend } = userFormData;
      
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

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('정말 이 유저를 비활성화하시겠습니까?')) {
      return;
    }
    try {
      await deleteTenantUser(userId);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || '유저 삭제에 실패했습니다');
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
    <div className="tenant-admin-page">
      <Sidebar isAdmin={isAdmin} />
      <TenantHeader
        title="테넌트 관리"
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      <div className="admin-tabs">
        <button
          className={activeTab === 'users' ? 'active' : ''}
          onClick={() => {
            setActiveTab('users');
            navigate('/dashboard');
          }}
        >
          유저 관리
        </button>
        <button
          className={activeTab === 'usage' ? 'active' : ''}
          onClick={() => {
            setActiveTab('usage');
            navigate('/dashboard?tab=usage');
          }}
        >
          사용량 조회
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {activeTab === 'users' && (
        <div className="users-section">
          <div className="section-header">
            <h2>유저 목록</h2>
            <button onClick={handleCreateUser} className="create-button">
              유저 추가
            </button>
          </div>

          {loading ? (
            <div className="loading">로딩 중...</div>
          ) : (
            <table className="users-table">
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
                      <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button onClick={() => handleEditUser(user)} className="edit-button">
                          수정
                        </button>
                        <button onClick={() => handleDeleteUser(user.id)} className="delete-button">
                          비활성화
                        </button>
                        <button
                          onClick={() => handleResetPassword(user.id)}
                          className="reset-button"
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
        <div className="usage-section">
          <h2>사용량 조회</h2>
          {loading ? (
            <div className="loading">로딩 중...</div>
          ) : usage ? (
            <div className="usage-stats">
              <div className="stat-card">
                <div className="stat-label">이미지</div>
                <div className="stat-value">{usage.total_images || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">OCR 여권</div>
                <div className="stat-value">{usage.total_ocr_passport || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">OCR 영수증</div>
                <div className="stat-value">{usage.total_ocr_receipt || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">검증된 여권</div>
                <div className="stat-value">{usage.total_verified_passport || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">검증된 영수증</div>
                <div className="stat-value">{usage.total_verified_receipt || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">매칭된 데이터</div>
                <div className="stat-value">{usage.total_matched || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">LLM 토큰</div>
                <div className="stat-value">{usage.total_llm_tokens || 0}</div>
              </div>
            </div>
          ) : (
            <div className="no-data">데이터가 없습니다</div>
          )}
        </div>
      )}

      {showUserModal && (
        <div className="modal-overlay" onClick={() => setShowUserModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingUser ? '유저 수정' : '유저 추가'}</h2>
            <div className="modal-form">
              <div className="form-group">
                <label>이름 *</label>
                <input
                  type="text"
                  value={userFormData.name}
                  onChange={(e) => setUserFormData({ ...userFormData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
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
                  <div className="form-group">
                    <label>비밀번호 *</label>
                    <input
                      type="password"
                      value={userFormData.password}
                      onChange={(e) =>
                        setUserFormData({ ...userFormData, password: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>비밀번호 확인 *</label>
                    <input
                      type="password"
                      value={userFormData.passwordConfirm}
                      onChange={(e) =>
                        setUserFormData({ ...userFormData, passwordConfirm: e.target.value })
                      }
                      required
                    />
                    {userFormData.passwordConfirm && (
                      <div
                        className={`password-match-message ${
                          userFormData.password === userFormData.passwordConfirm
                            ? 'match'
                            : 'no-match'
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
              <div className="form-group">
                <label>역할</label>
                <select
                  value={userFormData.role}
                  onChange={(e) => setUserFormData({ ...userFormData, role: e.target.value })}
                >
                  <option value="user">유저</option>
                  <option value="admin">관리자</option>
                </select>
              </div>
              <div className="form-group">
                <label>부서</label>
                <input
                  type="text"
                  value={userFormData.department}
                  onChange={(e) =>
                    setUserFormData({ ...userFormData, department: e.target.value })
                  }
                />
              </div>
              <div className="form-group">
                <label>연락처</label>
                <input
                  type="text"
                  value={userFormData.contact}
                  onChange={(e) => setUserFormData({ ...userFormData, contact: e.target.value })}
                />
              </div>
              <div className="modal-actions">
                <button onClick={() => setShowUserModal(false)} className="cancel-button">
                  취소
                </button>
                <button onClick={handleSaveUser} className="save-button">
                  저장
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TenantAdminPage;
