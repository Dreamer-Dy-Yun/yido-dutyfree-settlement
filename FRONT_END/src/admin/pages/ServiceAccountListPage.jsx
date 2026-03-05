import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getServiceAccounts, updateServiceAccount, deleteServiceAccount } from '../services/systemAdminApi';
import CommonTabsRow from '../../components/CommonTabsRow';
import CommonDataTable from '../components/CommonDataTable';
import './ServiceAccountListPage.css';

function ServiceAccountListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const getFilterFromLocation = () => {
    const searchParams = new URLSearchParams(location.search);
    const isActive = searchParams.get('is_active');
    if (isActive === 'true') return 'active';
    if (isActive === 'false') return 'inactive';
    return 'all';
  };

  const getRoleFromLocation = () => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.get('role') || '';
  };

  const [filter, setFilter] = useState(getFilterFromLocation);
  const [roleFilter, setRoleFilter] = useState(getRoleFromLocation);

  useEffect(() => {
    setFilter(getFilterFromLocation());
    setRoleFilter(getRoleFromLocation());
  }, [location.pathname, location.search]);

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

  const navigateWithFilters = (nextFilter, nextRole) => {
    const params = new URLSearchParams();
    if (nextFilter === 'active') {
      params.set('is_active', 'true');
    } else if (nextFilter === 'inactive') {
      params.set('is_active', 'false');
    }
    if (nextRole) {
      params.set('role', nextRole);
    }

    const query = params.toString();
    navigate(query ? `/admin/service-accounts?${query}` : '/admin/service-accounts');
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

  const handleDeactivate = async (accountId) => {
    if (!confirm('이 서비스 어카운트를 비활성화하시겠습니까?')) return;

    try {
      await updateServiceAccount(accountId, { is_active: false });
      alert('서비스 어카운트가 비활성화되었습니다');
      loadAccounts();
    } catch (err) {
      alert(err.response?.data?.detail || '비활성화에 실패했습니다');
    }
  };

  const handleActivate = async (accountId) => {
    if (!confirm('이 서비스 어카운트를 활성화하시겠습니까?')) return;

    try {
      await updateServiceAccount(accountId, { is_active: true });
      alert('서비스 어카운트가 활성화되었습니다');
      loadAccounts();
    } catch (err) {
      alert(err.response?.data?.detail || '활성화에 실패했습니다');
    }
  };

  return (
    <div className="common-page service-account-list-page">
      <CommonTabsRow
        tabs={[
          { key: 'all', label: '전체' },
          { key: 'active', label: '활성' },
          { key: 'inactive', label: '비활성' },
        ]}
        activeKey={filter}
        onTabChange={(nextFilter) => navigateWithFilters(nextFilter, roleFilter)}
        rightAction={
          <button className="common-btn common-btn-primary" onClick={() => navigate('/admin/service-accounts/new')}>
            새 서비스 어카운트 추가
          </button>
        }
      />

      <div className="common-card common-toolbar filters">
        <div className="role-filter">
          <label>역할:</label>
          <select
            className="select-input"
            value={roleFilter}
            onChange={(e) => navigateWithFilters(filter, e.target.value)}
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

      {loading && <div className="common-card common-state">로딩 중...</div>}
      {error && <div className="common-card common-state error">에러: {error}</div>}

      {!loading && !error && (
        <div className="common-card">
          <CommonDataTable
            tableClassName="account-table"
            columns={[
              { key: 'alias', label: '별칭', render: (account) => account.alias || '-' },
              { key: 'email', label: '이메일', render: (account) => account.e_mail },
              { key: 'role', label: '역할' },
              { key: 'description', label: '설명', render: (account) => account.description || '-' },
              {
                key: 'status',
                label: '상태',
                render: (account) => (
                  <span className={`status-badge ${account.is_active ? 'active' : 'inactive'}`}>
                    {account.is_active ? '활성' : '비활성'}
                  </span>
                ),
              },
              {
                key: 'actions',
                label: '작업',
                isAction: true,
                render: (account) => (
                  <>
                    <button
                      className="common-btn common-btn-primary"
                      onClick={() => handleViewDetail(account.id)}
                    >
                      상세보기
                    </button>
                    {account.is_active ? (
                      <button
                        className="common-btn common-btn-secondary"
                        onClick={() => handleDeactivate(account.id)}
                      >
                        비활성화
                      </button>
                    ) : (
                      <>
                        <button
                          className="common-btn common-btn-success"
                          onClick={() => handleActivate(account.id)}
                        >
                          활성화
                        </button>
                        <button
                          className="common-btn common-btn-secondary"
                          onClick={() => handleDelete(account.id)}
                        >
                          삭제
                        </button>
                      </>
                    )}
                  </>
                ),
              },
            ]}
            rows={accounts}
            emptyMessage="서비스 어카운트가 없습니다"
            getRowClassName={(account) => (!account.is_active ? 'inactive' : '')}
          />
        </div>
      )}
    </div>
  );
}

export default ServiceAccountListPage;
