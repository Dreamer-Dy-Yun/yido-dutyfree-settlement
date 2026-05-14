import { formatKoDateTime } from '../../../utils/dateFormat';

function TenantDetailEditForm({ tenant, formData, saving, onChange, onSubmit }) {
  return (
    <form id="tenant-form" onSubmit={onSubmit} className="tenant-form">
      <div className="tenant-detail-content">
        <div className="common-card detail-section">
          <h2>기본 정보</h2>
          <div className="form-grid">
            <div className="form-item">
              <label>회사명 <span className="required">*</span></label>
              <input type="text" name="name" value={formData.name} onChange={onChange} required />
            </div>
            <div className="form-item">
              <label>별칭</label>
              <input type="text" name="alias" value={formData.alias} onChange={onChange} />
            </div>
            <div className="form-item">
              <label>사업자번호</label>
              <input type="text" value={tenant.business_no || ''} disabled className="disabled-input" />
            </div>
            <div className="form-item">
              <label>국가 코드</label>
              <input type="text" value={tenant.country_code || ''} disabled className="disabled-input" />
            </div>
          </div>
        </div>

        <div className="common-card detail-section">
          <h2>연락처 정보</h2>
          <div className="form-grid">
            <div className="form-item">
              <label>연락처</label>
              <input type="text" name="contact" value={formData.contact} onChange={onChange} />
            </div>
            <div className="form-item">
              <label>이메일</label>
              <input type="email" name="email" value={formData.email} onChange={onChange} />
            </div>
            <div className="form-item full-width">
              <label>주소</label>
              <input type="text" name="address" value={formData.address} onChange={onChange} />
            </div>
          </div>
        </div>

        <div className="common-card detail-section">
          <h2>시스템 정보</h2>
          <div className="form-grid">
            <div className="form-item">
              <label>스키마명</label>
              <input type="text" value={tenant.schema_name || ''} disabled className="disabled-input" />
            </div>
            <div className="form-item">
              <label>루트 경로</label>
              <input type="text" value={tenant.dir_base || ''} disabled className="disabled-input" />
            </div>
            <div className="form-item">
              <label>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={onChange}
                  disabled={saving}
                />
                활성화
              </label>
            </div>
          </div>
        </div>

        <div className="common-card detail-section">
          <h2>등록 정보</h2>
          <div className="form-grid">
            {tenant.created_at && (
              <div className="form-item">
                <label>등록일시</label>
                <input
                  type="text"
                  value={formatKoDateTime(tenant.created_at)}
                  disabled
                  className="disabled-input"
                />
              </div>
            )}
            {tenant.updated_at && (
              <div className="form-item">
                <label>수정일시</label>
                <input
                  type="text"
                  value={formatKoDateTime(tenant.updated_at)}
                  disabled
                  className="disabled-input"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </form>
  );
}

export default TenantDetailEditForm;
