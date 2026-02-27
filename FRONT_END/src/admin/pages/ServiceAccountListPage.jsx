import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getServiceAccounts, deleteServiceAccount } from '../services/systemAdminApi';
import './ServiceAccountListPage.css';

function ServiceAccountListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // URL 쿼리 파라미터에서 초기 필터 값 읽기
  const searchParams = new URLSearchParams(location.search);
  const initialFilter = searchParams.get('is_active') === 'true' ? 'active' : 'all';
  
  const [filter, setFilter] = useState(initialFilter);
  const [roleFilter, setRoleFilter] = useState('');

  useEffect(() => {
    loadAccounts();
  }, [filter, roleFilter]);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const data = await getServiceAccounts({
        is_active: filter === 'all' ? undefined : filter === 'active',
        role: roleFilter || undefined,
      });
      setAccounts(data.service_accounts || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || '서비스 어카운트 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = (accountId) => {
    navigate(`/admin/service-accounts/${accountId}`);
  };

  const handleDelete = async (accountId) => {
    if (!confirm('이 서비스 어카운트를 삭제하시겠습니까?')) return;
    
    try {
      await deleteServiceAccount(accountId);
      alert('서비스 어카운트가 삭제되었습니다');
      loadAccounts();
    } catch (err) {
      alert(err.response?.data?.detail || '삭제에 실패했습니다');
    }
  };

  return (
    <div className="service-account-list-page">
      <div className="page-header">
        <h1>서비스 어카운트 관리</h1>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => navigate('/admin/service-accounts/new')}>
            새 계정 추가
          </button>
        </div>
      </div>

      <div className="filters">
        <div className="filter-buttons">
          <button
            className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setFilter('all');
            }}
          >
            전체
          </button>
          <button
            className={`btn ${filter === 'active' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setFilter('active');
            }}
          >
            활성
          </button>
          <button
            className={`btn ${filter === 'inactive' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setFilter('inactive');
            }}
          >
            비활성
          </button>
        </div>
        <div className="role-filter">
          <label>역할:</label>
          <select
            className="select-input"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
          >
            <option value="">전체</option>
            <option value="smtp_sender">SMTP 송신</option>
            <option value="smtp_receiver">SMTP 수신</option>
            <option value="monitor">모니터링</option>
            <option value="backup">백업</option>
            <option value="api">API</option>
            <option value="notification">알림</option>
          </select>
        </div>
      </div>

      {loading && <div className="loading">로딩 중...</div>}
      {error && <div className="error">에러: {error}</div>}

      {!loading && !error && (
        <div className="account-list">
          {accounts.length === 0 ? (
            <div className="empty-state">서비스 어카운트가 없습니다</div>
          ) : (
            <table className="account-table">
              <thead>
                <tr>
                  <th>별칭</th>
                  <th>이메일</th>
                  <th>역할</th>
                  <th>설명</th>
                  <th>상태</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((account) => (
                  <tr key={account.id} className={!account.is_active ? 'inactive' : ''}>
                    <td>{account.alias || '-'}</td>
                    <td>{account.e_mail}</td>
                    <td>{account.role}</td>
                    <td>{account.description || '-'}</td>
                    <td>
                      <span className={`status-badge ${account.is_active ? 'active' : 'inactive'}`}>
                        {account.is_active ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn btn-primary"
                          onClick={() => handleViewDetail(account.id)}
                        >
                          상세
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={() => handleDelete(account.id)}
                        >
                          삭제
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
    </div>
  );
}

export default ServiceAccountListPage;
