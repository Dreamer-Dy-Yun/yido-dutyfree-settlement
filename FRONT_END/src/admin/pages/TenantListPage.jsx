import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getTenants, getPendingTenants, approveTenant, rejectTenant, deleteTenant } from '../services/systemAdminApi';
import TenantCard from '../components/TenantCard';
import './TenantListPage.css';

function TenantListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // URL 쿼리 파라미터와 pathname에서 초기 필터 값 읽기
  const searchParams = new URLSearchParams(location.search);
  const isActiveParam = searchParams.get('is_active');
  let initialFilter = 'all';
  if (location.pathname === '/admin/tenants/pending') {
    initialFilter = 'pending';
  } else if (isActiveParam === 'true') {
    initialFilter = 'active';
  } else if (isActiveParam === 'false') {
    initialFilter = 'inactive';
  }
  
  const [filter, setFilter] = useState(initialFilter);
  const [search, setSearch] = useState('');
  const [skip, setSkip] = useState(0);
  const [limit] = useState(20);

  useEffect(() => {
    loadTenants();
  }, [filter, skip]);

  const loadTenants = async () => {
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
  };

  const handleViewDetail = (tenantId) => {
    navigate(`/admin/tenants/${tenantId}`);
  };

  const handleApprove = async (tenantId) => {
    if (!confirm('이 테넌트를 승인하시겠습니까?')) return;
    
    try {
      await approveTenant(tenantId);
      alert('테넌트가 승인되었습니다');
      loadTenants();
    } catch (err) {
      alert(err.response?.data?.detail || '승인에 실패했습니다');
    }
  };

  const handleReject = async (tenantId) => {
    const reason = prompt('거부 사유를 입력하세요:');
    if (!reason) return;
    
    try {
      await rejectTenant(tenantId, reason);
      alert('테넌트가 거부되었습니다');
      loadTenants();
    } catch (err) {
      alert(err.response?.data?.detail || '거부에 실패했습니다');
    }
  };

  const handleDelete = async (tenantId) => {
    if (!confirm('이 테넌트를 삭제(비활성화)하시겠습니까?')) return;
    
    try {
      await deleteTenant(tenantId);
      alert('테넌트가 삭제되었습니다');
      loadTenants();
    } catch (err) {
      alert(err.response?.data?.detail || '삭제에 실패했습니다');
    }
  };

  const handleSearch = () => {
    setSkip(0);
    loadTenants();
  };

  return (
    <div className="tenant-list-page">
      <div className="page-header">
        <h1>테넌트 관리</h1>
      </div>

      <div className="filters">
        <div className="filter-buttons">
          <button
            className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setFilter('all');
              setSkip(0);
            }}
          >
            전체
          </button>
          <button
            className={`btn ${filter === 'active' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setFilter('active');
              setSkip(0);
            }}
          >
            활성
          </button>
          <button
            className={`btn ${filter === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setFilter('pending');
              setSkip(0);
            }}
          >
            승인 대기
          </button>
          <button
            className={`btn ${filter === 'inactive' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setFilter('inactive');
              setSkip(0);
            }}
          >
            비활성
          </button>
        </div>
        <div className="search-box">
          <input
            type="text"
            placeholder="검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn btn-primary" onClick={handleSearch}>
            검색
          </button>
        </div>
      </div>

      {loading && <div className="loading">로딩 중...</div>}
      {error && <div className="error">에러: {error}</div>}

      {!loading && !error && (
        <>
          <div className="tenant-list">
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
