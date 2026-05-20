import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSystemStats } from '../../api/admin/systemAdminApi';
import { normalizeApiError } from '../../utils/normalizeApiError';
import './SystemAdminDashboard.css';

function SystemAdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await getSystemStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err, '통계를 불러오는데 실패했습니다'));
    } finally {
      setLoading(false);
    }
  };


  if (loading) {
    return <div className="common-card common-state">로딩 중...</div>;
  }

  if (error) {
    return <div className="common-card common-state dashboard-error">에러: {error}</div>;
  }
 
  return (
    <div className="common-page system-admin-dashboard">
      {stats && !stats.has_smtp_account && (
        <div className="smtp-warning">
          <div className="warning-icon">⚠️</div>
          <div className="warning-content">
            <strong>SMTP 송신 계정이 등록되지 않았습니다.</strong>
            <p>회사 등록 및 승인 안내 메일이 발송되지 않을 수 있습니다. 서비스 어카운트 관리에서 SMTP 송신 계정을 등록해주세요.</p>
          </div>
          <button
            className="common-btn common-btn-primary"
            onClick={() => navigate('/admin/service-accounts')}
          >
            서비스 어카운트 관리
          </button>
        </div>
      )}
      <div className="stats-grid">
        <div 
          className="stat-card clickable"
          onClick={() => navigate('/admin/tenants')}
        >
          <div className="stat-label">전체 테넌트</div>
          <div className="stat-value">{stats?.total_tenants || 0}</div>
        </div>

        <div 
          className="stat-card active clickable"
          onClick={() => navigate('/admin/tenants?is_active=true')}
        >
          <div className="stat-label">활성 테넌트</div>
          <div className="stat-value">{stats?.active_tenants || 0}</div>
        </div>

        <div 
          className="stat-card pending clickable"
          onClick={() => navigate('/admin/tenants/pending')}
        >
          <div className="stat-label">승인 대기</div>
          <div className="stat-value">{stats?.pending_tenants || 0}</div>
        </div>

        <div 
          className="stat-card clickable"
          onClick={() => navigate('/admin/service-accounts')}
        >
          <div className="stat-label">전체 서비스 어카운트</div>
          <div className="stat-value">{stats?.total_service_accounts || 0}</div>
        </div>

        <div 
          className="stat-card active clickable"
          onClick={() => navigate('/admin/service-accounts?is_active=true')}
        >
          <div className="stat-label">활성 서비스 어카운트</div>
          <div className="stat-value">{stats?.active_service_accounts || 0}</div>
        </div>
      </div>
    </div>
  );
}

export default SystemAdminDashboard;
