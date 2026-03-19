import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getTenantDetail, approveTenant, rejectTenant, deleteTenant, updateTenant } from '../services/systemAdminApi';
import './TenantDetailPage.css';

function TenantDetailPage() {
  const navigate = useNavigate();
  const { tenantId } = useParams();
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    alias: '',
    contact: '',
    email: '',
    address: '',
    is_active: false,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadTenantDetail();
  }, [tenantId]);

  const loadTenantDetail = async () => {
    try {
      setLoading(true);
      const data = await getTenantDetail(tenantId);
      setTenant(data);
      setFormData({
        name: data.name || '',
        alias: data.alias || '',
        contact: data.contact || '',
        email: data.email || '',
        address: data.address || '',
        is_active: data.is_active !== undefined ? data.is_active : false,
      });
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || '테넌트 정보를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
    if (window.confirm('수정을 취소하시겠습니까? 변경사항이 저장되지 않습니다.')) {
      setIsEditing(false);
      // 원래 데이터로 복원
      if (tenant) {
        setFormData({
          name: tenant.name || '',
          alias: tenant.alias || '',
          contact: tenant.contact || '',
          email: tenant.email || '',
          address: tenant.address || '',
          is_active: tenant.is_active !== undefined ? tenant.is_active : false,
        });
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      alert('회사명을 입력해주세요.');
      return;
    }

    try {
      setSaving(true);
      const updateData = {};
      // 수정 가능한 필드만 포함
      if (formData.name !== tenant.name) updateData.name = formData.name;
      if (formData.alias !== (tenant.alias || '')) updateData.alias = formData.alias || null;
      if (formData.contact !== (tenant.contact || '')) updateData.contact = formData.contact || null;
      if (formData.email !== (tenant.email || '')) updateData.email = formData.email || null;
      if (formData.address !== (tenant.address || '')) updateData.address = formData.address || null;
      if (formData.is_active !== tenant.is_active) updateData.is_active = formData.is_active;
      
      if (Object.keys(updateData).length === 0) {
        alert('변경된 내용이 없습니다.');
        return;
      }
      
      await updateTenant(tenantId, updateData);
      alert('테넌트 정보가 수정되었습니다.');
      setIsEditing(false);
      loadTenantDetail();
    } catch (err) {
      console.error('Update error:', err);
      alert(err.response?.data?.detail || '수정에 실패했습니다');
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!window.confirm('이 테넌트를 승인하시겠습니까?')) {
      return;
    }

    try {
      await approveTenant(tenantId);
      alert('승인 완료!');
      loadTenantDetail();
    } catch (err) {
      alert(err.response?.data?.detail || '승인에 실패했습니다');
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      alert('거부 사유를 입력해주세요.');
      return;
    }

    // 최종 확인: 승인 거부 시 삭제됨을 알림
    const finalConfirm = window.confirm(
      '마지막으로 승인을 거부하면 삭제 됩니다.\n정말 거부하시겠습니까?'
    );
    
    if (!finalConfirm) {
      return;
    }

    try {
      await rejectTenant(tenantId, rejectReason);
      alert('거부 완료. 테넌트가 삭제되었습니다.');
      setShowRejectModal(false);
      setRejectReason('');
      navigate('/admin/tenants');
    } catch (err) {
      alert(err.response?.data?.detail || '거부에 실패했습니다');
    }
  };

  const handleDelete = async () => {
    if (deleting) return;
    if (!deleteReason.trim()) {
      alert('삭제 사유를 입력해주세요.');
      return;
    }

    try {
      setDeleting(true);
      await deleteTenant(tenantId, deleteReason);
      alert('삭제 완료');
      setShowDeleteModal(false);
      setDeleteReason('');
      navigate('/admin/tenants');
    } catch (err) {
      alert(err.response?.data?.detail || '삭제에 실패했습니다');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="common-page tenant-detail-page">
        <div className="common-card common-state">로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="common-page tenant-detail-page">
        <div className="common-card common-state error">에러: {error}</div>
        <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/tenants')}>
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="common-page tenant-detail-page">
        <div className="common-card common-state error">테넌트를 찾을 수 없습니다</div>
        <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/tenants')}>
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="common-page tenant-detail-page">
      <div className="common-card common-card-header detail-toolbar">
        <h1>테넌트 상세 정보</h1>
        <div className="detail-actions">
          <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/tenants')}>
            목록으로
          </button>
          {!tenant.is_active && !tenant.is_db_built && (
            <>
              <button className="common-btn common-btn-success" onClick={handleApprove}>
                승인
              </button>
              <button className="common-btn common-btn-danger" onClick={() => setShowRejectModal(true)}>
                거부
              </button>
            </>
          )}
          {tenant.is_db_built === true && !isEditing && (
            <>
              <button className="common-btn common-btn-primary" onClick={handleEdit}>
                수정
              </button>
              <button className="common-btn common-btn-danger" onClick={() => setShowDeleteModal(true)}>
                삭제
              </button>
            </>
          )}
          {tenant.is_db_built === true && isEditing && (
            <>
              <button type="submit" form="tenant-form" className="common-btn common-btn-primary" disabled={saving}>
                {saving ? '저장 중...' : '수정완료'}
              </button>
              <button type="button" className="common-btn common-btn-secondary" onClick={handleCancel} disabled={saving}>
                수정취소
              </button>
            </>
          )}
        </div>
      </div>

      {!isEditing ? (
        // 읽기 모드
        <div className="tenant-detail-content">
          <div className="common-card detail-section">
            <h2>기본 정보</h2>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="label">회사명</span>
                <span className="value">{tenant.name}</span>
              </div>
              {tenant.alias && (
                <div className="detail-item">
                  <span className="label">별칭</span>
                  <span className="value">{tenant.alias}</span>
                </div>
              )}
              {tenant.business_no && (
                <div className="detail-item">
                  <span className="label">사업자번호</span>
                  <span className="value">{tenant.business_no}</span>
                </div>
              )}
              {tenant.country_code && (
                <div className="detail-item">
                  <span className="label">국가 코드</span>
                  <span className="value">{tenant.country_code}</span>
                </div>
              )}
            </div>
          </div>

          <div className="common-card detail-section">
            <h2>연락처 정보</h2>
            <div className="detail-grid">
              {tenant.contact && (
                <div className="detail-item">
                  <span className="label">연락처</span>
                  <span className="value">{tenant.contact}</span>
                </div>
              )}
              {tenant.email && (
                <div className="detail-item">
                  <span className="label">이메일</span>
                  <span className="value">{tenant.email}</span>
                </div>
              )}
              {tenant.address && (
                <div className="detail-item">
                  <span className="label">주소</span>
                  <span className="value">{tenant.address}</span>
                </div>
              )}
            </div>
          </div>

          <div className="common-card detail-section">
            <h2>시스템 정보</h2>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="label">스키마명</span>
                <span className="value">{tenant.schema_name}</span>
              </div>
              <div className="detail-item">
                <span className="label">루트 경로</span>
                <span className="value">{tenant.dir_base}</span>
              </div>
              <div className="detail-item">
                <span className="label">활성화 여부</span>
                <span className={`value status-badge ${tenant.is_active ? 'active' : 'inactive'}`}>
                  {tenant.is_active ? '활성' : '비활성'}
                </span>
              </div>
            </div>
          </div>

          <div className="common-card detail-section">
            <h2>등록 정보</h2>
            <div className="detail-grid">
              {tenant.created_at && (
                <div className="detail-item">
                  <span className="label">등록일시</span>
                  <span className="value">{new Date(tenant.created_at).toLocaleString('ko-KR')}</span>
                </div>
              )}
              {tenant.updated_at && (
                <div className="detail-item">
                  <span className="label">수정일시</span>
                  <span className="value">{new Date(tenant.updated_at).toLocaleString('ko-KR')}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        // 수정 모드
        <form id="tenant-form" onSubmit={handleSubmit} className="tenant-form">
          <div className="tenant-detail-content">
            <div className="common-card detail-section">
              <h2>기본 정보</h2>
              <div className="form-grid">
                <div className="form-item">
                  <label>회사명 <span className="required">*</span></label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-item">
                  <label>별칭</label>
                  <input
                    type="text"
                    name="alias"
                    value={formData.alias}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-item">
                  <label>사업자번호</label>
                  <input
                    type="text"
                    value={tenant.business_no || ''}
                    disabled
                    className="disabled-input"
                  />
                </div>
                <div className="form-item">
                  <label>국가 코드</label>
                  <input
                    type="text"
                    value={tenant.country_code || ''}
                    disabled
                    className="disabled-input"
                  />
                </div>
              </div>
            </div>

            <div className="common-card detail-section">
              <h2>연락처 정보</h2>
              <div className="form-grid">
                <div className="form-item">
                  <label>연락처</label>
                  <input
                    type="text"
                    name="contact"
                    value={formData.contact}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-item">
                  <label>이메일</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-item full-width">
                  <label>주소</label>
                  <input
                    type="text"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            <div className="common-card detail-section">
              <h2>시스템 정보</h2>
              <div className="form-grid">
                <div className="form-item">
                  <label>스키마명</label>
                  <input
                    type="text"
                    value={tenant.schema_name || ''}
                    disabled
                    className="disabled-input"
                  />
                </div>
                <div className="form-item">
                  <label>루트 경로</label>
                  <input
                    type="text"
                    value={tenant.dir_base || ''}
                    disabled
                    className="disabled-input"
                  />
                </div>
                <div className="form-item">
                  <label>
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleChange}
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
                      value={new Date(tenant.created_at).toLocaleString('ko-KR')}
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
                      value={new Date(tenant.updated_at).toLocaleString('ko-KR')}
                      disabled
                      className="disabled-input"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        </form>
      )}

      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>테넌트 거부</h3>
            <p>거부 사유를 입력해주세요:</p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="거부 사유를 입력하세요..."
              rows="4"
            />
            <div className="modal-actions">
              <button
                className="common-btn common-btn-secondary"
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason('');
                }}
              >
                취소
              </button>
              <button
                className="common-btn common-btn-danger"
                onClick={handleReject}
                disabled={!rejectReason.trim()}
              >
                거부
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteModal && (
        <div
          className="modal-overlay"
          onClick={() => {
            if (deleting) return;
            setShowDeleteModal(false);
          }}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>테넌트 삭제</h3>
            <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '12px' }}>
              ⚠️ 주의: 삭제된 데이터는 복구할 수 없습니다.
            </p>
            <p>삭제 사유를 입력해주세요:</p>
            <textarea
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              placeholder="삭제 사유를 입력하세요..."
              rows="4"
              disabled={deleting}
            />
            <div className="modal-actions">
              <button
                className="common-btn common-btn-secondary"
                onClick={() => {
                  if (deleting) return;
                  setShowDeleteModal(false);
                  setDeleteReason('');
                }}
                disabled={deleting}
              >
                취소
              </button>
              <button
                className="common-btn common-btn-danger"
                onClick={handleDelete}
                disabled={deleting || !deleteReason.trim()}
              >
                {deleting ? '삭제 중...' : '삭제'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TenantDetailPage;
