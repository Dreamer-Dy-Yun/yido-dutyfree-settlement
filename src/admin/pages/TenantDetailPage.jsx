import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getTenantDetail, approveTenant, rejectTenant, deleteTenant, updateTenant } from '../../api/admin/systemAdminApi';
import TenantDeleteModal from './tenant-detail/TenantDeleteModal';
import TenantDetailEditForm from './tenant-detail/TenantDetailEditForm';
import TenantDetailReadView from './tenant-detail/TenantDetailReadView';
import TenantRejectModal from './tenant-detail/TenantRejectModal';
import { normalizeApiError } from '../../utils/normalizeApiError';
import { confirmUserAction, notifyUser } from '../../utils/userFeedback';
import './TenantDetailPage.css';

const toTenantForm = (tenant) => ({
  name: tenant.name || '',
  alias: tenant.alias || '',
  contact: tenant.contact || '',
  email: tenant.email || '',
  address: tenant.address || '',
  is_active: tenant.is_active !== undefined ? tenant.is_active : false,
});

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

  const loadTenantDetail = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getTenantDetail(tenantId);
      setTenant(data);
      setFormData(toTenantForm(data));
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err, '테넌트 정보를 불러오는데 실패했습니다'));
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    loadTenantDetail();
  }, [loadTenantDetail]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleCancel = () => {
    if (!confirmUserAction('수정을 취소하시겠습니까? 변경사항이 저장되지 않습니다.')) return;
    setIsEditing(false);
    if (tenant) setFormData(toTenantForm(tenant));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      notifyUser('회사명을 입력해주세요.');
      return;
    }

    try {
      setSaving(true);
      const updateData = {};
      if (formData.name !== tenant.name) updateData.name = formData.name;
      if (formData.alias !== (tenant.alias || '')) updateData.alias = formData.alias || null;
      if (formData.contact !== (tenant.contact || '')) updateData.contact = formData.contact || null;
      if (formData.email !== (tenant.email || '')) updateData.email = formData.email || null;
      if (formData.address !== (tenant.address || '')) updateData.address = formData.address || null;
      if (formData.is_active !== tenant.is_active) updateData.is_active = formData.is_active;

      if (Object.keys(updateData).length === 0) {
        notifyUser('변경된 내용이 없습니다.');
        return;
      }

      await updateTenant(tenantId, updateData);
      notifyUser('테넌트 정보가 수정되었습니다.');
      setIsEditing(false);
      await loadTenantDetail();
    } catch (err) {
      console.error('Update error:', err);
      notifyUser(normalizeApiError(err, '수정에 실패했습니다'));
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!confirmUserAction('이 테넌트를 승인하시겠습니까?')) return;
    try {
      await approveTenant(tenantId);
      notifyUser('승인 완료!');
      await loadTenantDetail();
    } catch (err) {
      notifyUser(normalizeApiError(err, '승인에 실패했습니다'));
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      notifyUser('거부 사유를 입력해주세요.');
      return;
    }
    const finalConfirm = confirmUserAction('마지막으로 승인을 거부하면 삭제 됩니다.\n정말 거부하시겠습니까?');
    if (!finalConfirm) return;

    try {
      await rejectTenant(tenantId, rejectReason);
      notifyUser('거부 완료. 테넌트가 삭제되었습니다.');
      setShowRejectModal(false);
      setRejectReason('');
      navigate('/admin/tenants');
    } catch (err) {
      notifyUser(normalizeApiError(err, '거부에 실패했습니다'));
    }
  };

  const handleDelete = async () => {
    if (deleting) return;
    if (!deleteReason.trim()) {
      notifyUser('삭제 사유를 입력해주세요.');
      return;
    }

    try {
      setDeleting(true);
      await deleteTenant(tenantId, deleteReason);
      notifyUser('삭제 완료');
      setShowDeleteModal(false);
      setDeleteReason('');
      navigate('/admin/tenants');
    } catch (err) {
      notifyUser(normalizeApiError(err, '삭제에 실패했습니다'));
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

  if (error || !tenant) {
    return (
      <div className="common-page tenant-detail-page">
        <div className="common-card common-state error">
          {error ? `에러: ${error}` : '테넌트를 찾을 수 없습니다'}
        </div>
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
              <button className="common-btn common-btn-primary" onClick={() => setIsEditing(true)}>
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
        <TenantDetailReadView tenant={tenant} />
      ) : (
        <TenantDetailEditForm
          tenant={tenant}
          formData={formData}
          saving={saving}
          onChange={handleChange}
          onSubmit={handleSubmit}
        />
      )}

      {showRejectModal && (
        <TenantRejectModal
          rejectReason={rejectReason}
          onChangeReason={setRejectReason}
          onClose={() => {
            setShowRejectModal(false);
            setRejectReason('');
          }}
          onReject={handleReject}
        />
      )}

      {showDeleteModal && (
        <TenantDeleteModal
          deleteReason={deleteReason}
          deleting={deleting}
          onChangeReason={setDeleteReason}
          onClose={() => {
            if (deleting) return;
            setShowDeleteModal(false);
            setDeleteReason('');
          }}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}

export default TenantDetailPage;
