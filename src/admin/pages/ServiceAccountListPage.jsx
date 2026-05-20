import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getServiceAccounts, updateServiceAccount, deleteServiceAccount } from '../../api/admin/systemAdminApi';
import CommonTabsRow from '../../components/CommonTabsRow';
import { formatRecordTimestamp } from '../../utils/dateFormat';
import { normalizeApiError } from '../../utils/normalizeApiError';
import { confirmUserAction, notifyUser } from '../../utils/userFeedback';
import CommonDataTable from '../components/CommonDataTable';
import './ServiceAccountListPage.css';

function ServiceAccountListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const filterFromLocation = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    const isActive = searchParams.get('is_active');
    if (isActive === 'true') return 'active';
    if (isActive === 'false') return 'inactive';
    return 'all';
  }, [location.search]);

  const roleFromLocation = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.get('role') || '';
  }, [location.search]);

  const [filter, setFilter] = useState(filterFromLocation);
  const [roleFilter, setRoleFilter] = useState(roleFromLocation);

  useEffect(() => {
    setFilter(filterFromLocation);
    setRoleFilter(roleFromLocation);
  }, [filterFromLocation, roleFromLocation]);

  const loadAccounts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getServiceAccounts({
        is_active: filter === 'all' ? undefined : filter === 'active',
        role: roleFilter || undefined,
      });
      setAccounts(data.service_accounts || []);
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err, '서비스 어카운트 목록을 불러오는데 실패했습니다'));
    } finally {
      setLoading(false);
    }
  }, [filter, roleFilter]);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

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
    if (!confirmUserAction('이 서비스 어카운트를 삭제하시겠습니까?')) return;
    
    try {
      await deleteServiceAccount(accountId);
      notifyUser('서비스 어카운트가 삭제되었습니다');
      loadAccounts();
    } catch (err) {
      notifyUser(normalizeApiError(err, '삭제에 실패했습니다'));
    }
  };

  const handleDeactivate = async (accountId) => {
    if (!confirmUserAction('이 서비스 어카운트를 비활성화하시겠습니까?')) return;

    try {
      await updateServiceAccount(accountId, { is_active: false });
      notifyUser('서비스 어카운트가 비활성화되었습니다');
      loadAccounts();
    } catch (err) {
      notifyUser(normalizeApiError(err, '비활성화에 실패했습니다'));
    }
  };

  const handleActivate = async (accountId) => {
    if (!confirmUserAction('이 서비스 어카운트를 활성화하시겠습니까?')) return;

    try {
      await updateServiceAccount(accountId, { is_active: true });
      notifyUser('서비스 어카운트가 활성화되었습니다');
      loadAccounts();
    } catch (err) {
      notifyUser(normalizeApiError(err, '활성화에 실패했습니다'));
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
              { key: 'created_at', label: '등록일', render: (account) => formatRecordTimestamp(account) },
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
