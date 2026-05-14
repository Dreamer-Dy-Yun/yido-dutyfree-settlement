import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getTenants, getPendingTenants } from '../services/systemAdminApi';
import TenantCard from '../components/TenantCard';
import CommonTabsRow from '../../components/CommonTabsRow';
import './TenantListPage.css';

function TenantListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const filterFromLocation = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    const isActiveParam = searchParams.get('is_active');
    if (location.pathname === '/admin/tenants/pending') {
      return 'pending';
    }
    if (isActiveParam === 'true') {
      return 'active';
    }
    if (isActiveParam === 'false') {
      return 'inactive';
    }
    return 'all';
  }, [location.pathname, location.search]);
  
  const [filter, setFilter] = useState(filterFromLocation);
  const [search, setSearch] = useState('');
  const [skip, setSkip] = useState(0);
  const [limit] = useState(20);

  // 사이드바/URL 이동 시 탭 상태를 URL 기준으로 동기화
  useEffect(() => {
    setFilter(filterFromLocation);
    setSkip(0);
  }, [filterFromLocation]);

  const loadTenants = useCallback(async () => {
    try {
      setLoading(true);
      let data;
      
      if (filter === 'pending') {
        data = await getPendingTenants({ skip, limit });
        setTenants(data.pending_tenants || []);
      } else {
        data = await getTenants({
          skip,
          limit,
          is_active: filter === 'active' ? true : filter === 'inactive' ? false : undefined,
          search: search || undefined,
        });
        setTenants(data.tenants || []);
      }
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || '테넌트 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [filter, limit, search, skip]);

  useEffect(() => {
    loadTenants();
  }, [loadTenants]);

  const handleViewDetail = (tenantId) => {
    navigate(`/admin/tenants/${tenantId}`);
  };

  const handleSearch = () => {
    setSkip(0);
    loadTenants();
  };

  return (
    <div className="common-page tenant-list-page">
      <CommonTabsRow
        tabs={[
          { key: 'all', label: '전체' },
          { key: 'active', label: '활성' },
          { key: 'pending', label: '승인 대기' },
          { key: 'inactive', label: '비활성' },
        ]}
        activeKey={filter}
        onTabChange={(nextFilter) => {
          if (nextFilter === 'all') navigate('/admin/tenants');
          if (nextFilter === 'active') navigate('/admin/tenants?is_active=true');
          if (nextFilter === 'pending') navigate('/admin/tenants/pending');
          if (nextFilter === 'inactive') navigate('/admin/tenants?is_active=false');
        }}
      />

      <div className="common-card common-toolbar filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="common-btn common-btn-primary" onClick={handleSearch}>
            검색
          </button>
        </div>
      </div>

      {loading && <div className="common-card common-state">로딩 중...</div>}
      {error && <div className="common-card common-state error">에러: {error}</div>}

      {!loading && !error && (
        <>
          <div className="common-card tenant-list">
            {tenants.length === 0 ? (
              <div className="empty-state">테넌트가 없습니다</div>
            ) : (
              tenants.map((tenant) => (
                <TenantCard
                  key={tenant.id}
                  tenant={tenant}
                  onViewDetail={handleViewDetail}
                />
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default TenantListPage;
