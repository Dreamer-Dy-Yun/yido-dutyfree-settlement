import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getServiceAccountDetail, createServiceAccount, updateServiceAccount } from '../../api/admin/systemAdminApi';
import { notifyUser } from '../../utils/userFeedback';
import './ServiceAccountDetailPage.css';

function ServiceAccountDetailPage() {
  const navigate = useNavigate();
  const { accountId } = useParams();
  const isNew = accountId === 'new';
  
  const [formData, setFormData] = useState({
    alias: '',
    e_mail: '',
    password: '',
    role: 'smtp_sender',
    description: '',
    is_active: true,
  });
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const loadAccountDetail = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getServiceAccountDetail(accountId);
      setFormData({
        alias: data.alias || '',
        e_mail: data.e_mail || '',
        password: '', // 보안상 비밀번호는 표시하지 않음
        role: data.role || 'smtp_sender',
        description: data.description || '',
        is_active: data.is_active !== undefined ? data.is_active : true,
      });
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || '서비스 어카운트 정보를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  useEffect(() => {
    if (!isNew) {
      loadAccountDetail();
    }
  }, [isNew, loadAccountDetail]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.e_mail) {
      notifyUser('이메일을 입력해주세요.');
      return;
    }
    
    if (isNew && !formData.password) {
      notifyUser('비밀번호를 입력해주세요.');
      return;
    }

    try {
      setSaving(true);
      
      if (isNew) {
        await createServiceAccount(formData);
        notifyUser('서비스 어카운트가 등록되었습니다.');
      } else {
        // 수정 시 비밀번호가 비어있으면 제외
        const updateData = { ...formData };
        if (!updateData.password) {
          delete updateData.password;
        }
        await updateServiceAccount(accountId, updateData);
        notifyUser('서비스 어카운트 정보가 수정되었습니다.');
      }
      
      navigate('/admin/service-accounts');
    } catch (err) {
      notifyUser(err.response?.data?.detail || '저장에 실패했습니다');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="common-page service-account-detail-page">
        <div className="common-card common-state">로딩 중...</div>
      </div>
    );
  }

  if (error && !isNew) {
    return (
      <div className="common-page service-account-detail-page">
        <div className="common-card common-state error">에러: {error}</div>
        <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/service-accounts')}>
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="common-page service-account-detail-page">
      <div className="common-card common-card-header detail-toolbar">
        <h1>{isNew ? '새 서비스 어카운트 추가' : '서비스 어카운트 상세 정보'}</h1>
        <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/service-accounts')}>
          목록으로
        </button>
      </div>

      <form onSubmit={handleSubmit} className="common-card account-form">
        <div className="form-section">
          <h2>기본 정보</h2>
          <div className="form-grid">
            <div className="form-item">
              <label>별칭</label>
              <input
                type="text"
                name="alias"
                value={formData.alias}
                onChange={handleChange}
                placeholder="계정 별칭 (선택사항)"
              />
            </div>

            <div className="form-item">
              <label>이메일 <span className="required">*</span></label>
              <input
                type="email"
                name="e_mail"
                value={formData.e_mail}
                onChange={handleChange}
                required
                disabled={!isNew}
                placeholder="example@email.com"
              />
              {!isNew && <small>이메일은 수정할 수 없습니다</small>}
            </div>

            <div className="form-item">
              <label>비밀번호 {isNew && <span className="required">*</span>}</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required={isNew}
                placeholder={isNew ? "비밀번호를 입력하세요" : "변경하려면 입력하세요 (비워두면 변경 안함)"}
              />
            </div>

            <div className="form-item">
              <label>역할 <span className="required">*</span></label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                required
              >
                <option value="smtp_sender">SMTP 송신</option>
                <option value="smtp_receiver">SMTP 수신</option>
                <option value="monitor">모니터링</option>
                <option value="backup">백업</option>
                <option value="api">API</option>
                <option value="notification">알림</option>
              </select>
            </div>

            <div className="form-item full-width">
              <label>설명</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="3"
                placeholder="계정 용도 설명 (선택사항)"
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

        <div className="form-actions">
          <button
            type="button"
            className="common-btn common-btn-secondary"
            onClick={() => navigate('/admin/service-accounts')}
            disabled={saving}
          >
            취소
          </button>
          <button
            type="submit"
            className="common-btn common-btn-primary"
            disabled={saving}
          >
            {saving ? '저장 중...' : (isNew ? '생성' : '수정')}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ServiceAccountDetailPage;
