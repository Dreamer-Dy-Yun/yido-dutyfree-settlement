function DetailItem({ label, value, children }) {
  return (
    <div className="detail-item">
      <span className="label">{label}</span>
      <span className="value">{children || value}</span>
    </div>
  );
}

function TenantDetailReadView({ tenant }) {
  return (
    <div className="tenant-detail-content">
      <div className="common-card detail-section">
        <h2>기본 정보</h2>
        <div className="detail-grid">
          <DetailItem label="회사명" value={tenant.name} />
          {tenant.alias && <DetailItem label="별칭" value={tenant.alias} />}
          {tenant.business_no && <DetailItem label="사업자번호" value={tenant.business_no} />}
          {tenant.country_code && <DetailItem label="국가 코드" value={tenant.country_code} />}
        </div>
      </div>

      <div className="common-card detail-section">
        <h2>연락처 정보</h2>
        <div className="detail-grid">
          {tenant.contact && <DetailItem label="연락처" value={tenant.contact} />}
          {tenant.email && <DetailItem label="이메일" value={tenant.email} />}
          {tenant.address && <DetailItem label="주소" value={tenant.address} />}
        </div>
      </div>

      <div className="common-card detail-section">
        <h2>시스템 정보</h2>
        <div className="detail-grid">
          <DetailItem label="스키마명" value={tenant.schema_name} />
          <DetailItem label="루트 경로" value={tenant.dir_base} />
          <DetailItem label="활성화 여부">
            <span className={`value status-badge ${tenant.is_active ? 'active' : 'inactive'}`}>
              {tenant.is_active ? '활성' : '비활성'}
            </span>
          </DetailItem>
        </div>
      </div>

      <div className="common-card detail-section">
        <h2>등록 정보</h2>
        <div className="detail-grid">
          {tenant.created_at && (
            <DetailItem label="등록일시" value={new Date(tenant.created_at).toLocaleString('ko-KR')} />
          )}
          {tenant.updated_at && (
            <DetailItem label="수정일시" value={new Date(tenant.updated_at).toLocaleString('ko-KR')} />
          )}
        </div>
      </div>
    </div>
  );
}

export default TenantDetailReadView;
