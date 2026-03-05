import './TenantCard.css';

function TenantCard({ tenant, onViewDetail }) {
  const handleClick = () => {
    onViewDetail(tenant.id);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div 
      className={`tenant-card ${tenant.is_active ? 'active' : 'pending'}`}
      onClick={handleClick}
    >
      <div className="tenant-card-content">
        <div className="tenant-alias">
          {tenant.alias || tenant.name || '-'}
        </div>
        <div className="tenant-meta">
          <span className="tenant-date">
            등록일: {formatDate(tenant.created_at || tenant.db_created_at)}
          </span>
          <span className={`status-badge ${tenant.is_active ? 'active' : 'pending'}`}>
            {tenant.is_active ? '승인됨' : '승인 대기'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default TenantCard;
