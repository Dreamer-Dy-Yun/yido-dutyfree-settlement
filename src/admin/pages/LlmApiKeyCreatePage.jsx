import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createLlmApiKey, getLlmApiKeyDetail, updateLlmApiKey } from '../../api/systemAdminApi';
import './LlmApiKeyCreatePage.css';

function LlmApiKeyCreatePage() {
  const navigate = useNavigate();
  const { apiKeyId } = useParams();
  const isEdit = Boolean(apiKeyId);
  const [formData, setFormData] = useState({
    purpose: 'OCR',
    llm_provider: 'OPEN AI',
    llm_model: 'gpt-4o',
    api_key: '',
    is_active: false,
  });
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadDetail = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getLlmApiKeyDetail(apiKeyId);
      setFormData({
        purpose: data.purpose || 'OCR',
        llm_provider: String(data.llm_provider || 'OPEN AI').toUpperCase(),
        llm_model: data.llm_model || '',
        api_key: '',
        is_active: Boolean(data.is_active),
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'API KEY 정보를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [apiKeyId]);

  useEffect(() => {
    if (!isEdit) return;
    loadDetail();
  }, [isEdit, loadDetail]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.purpose.trim() || !formData.llm_provider.trim() || !formData.llm_model.trim()) {
      setError('용도, 제공사, 모델을 모두 입력해주세요.');
      return;
    }
    if (!isEdit && !formData.api_key.trim()) {
      setError('API KEY를 입력해주세요.');
      return;
    }

    try {
      setSaving(true);
      if (isEdit) {
        const payload = {
          purpose: formData.purpose.trim(),
          llm_provider: formData.llm_provider.trim().toUpperCase(),
          llm_model: formData.llm_model.trim(),
          is_active: formData.is_active,
        };
        if (formData.api_key.trim()) {
          payload.api_key = formData.api_key.trim();
        }
        await updateLlmApiKey(apiKeyId, payload);
        alert('API KEY가 수정되었습니다.');
      } else {
        await createLlmApiKey({
          purpose: formData.purpose.trim(),
          llm_provider: formData.llm_provider.trim().toUpperCase(),
          llm_model: formData.llm_model.trim(),
          api_key: formData.api_key.trim(),
          is_active: formData.is_active,
        });
        alert('API KEY가 등록되었습니다.');
      }
      navigate('/admin/llm-api-keys');
    } catch (err) {
      setError(err.response?.data?.detail || `API KEY ${isEdit ? '수정' : '등록'}에 실패했습니다.`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="common-page llm-api-key-create-page">
        <div className="common-card common-state">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="common-page llm-api-key-create-page">
      <div className="common-card common-card-header llm-api-key-create-header">
        <h1>{isEdit ? 'API KEY 수정' : 'API KEY 추가'}</h1>
        <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/llm-api-keys')}>
          목록으로
        </button>
      </div>

      {error && <div className="common-card common-state error">{error}</div>}

      <form className="common-card llm-api-key-create-form" onSubmit={handleSubmit}>
        <div className="llm-api-key-form-grid">
          <div className="llm-api-key-form-item">
            <label htmlFor="purpose">용도 (Purpose)</label>
            <select
              id="purpose"
              name="purpose"
              value={formData.purpose}
              onChange={handleChange}
              required
            >
              <option value="OCR">OCR</option>
            </select>
          </div>

          <div className="llm-api-key-form-item">
            <label htmlFor="llm_provider">LLM 제공사</label>
            <select
              id="llm_provider"
              name="llm_provider"
              value={formData.llm_provider}
              onChange={handleChange}
              required
            >
              <option value="OPEN AI">OPEN AI</option>
            </select>
          </div>

          <div className="llm-api-key-form-item">
            <label htmlFor="llm_model">LLM 모델</label>
            <select
              id="llm_model"
              name="llm_model"
              value={formData.llm_model}
              onChange={handleChange}
              required
            >
              <option value="">모델을 선택하세요</option>
              {/* GPT-5 계열 */}
              <option value="gpt-5.4">GPT-5.4</option>
              <option value="gpt-5.4-pro">GPT-5.4 pro</option>
              <option value="gpt-5-mini">GPT-5 mini</option>
              <option value="gpt-5-nano">GPT-5 nano</option>
              <option value="gpt-5">GPT-5</option>

              {/* GPT-4 계열 (기존 기본값 포함) */}
              <option value="gpt-4.1">GPT-4.1</option>
              {/* <option value="gpt-4o">GPT-4o</option> API 및 매개변수 상이 */}
            </select>
          </div>

          <div className="llm-api-key-form-item llm-api-key-full-width">
            <label htmlFor="api_key">API KEY</label>
            <input
              id="api_key"
              name="api_key"
              type="password"
              value={formData.api_key}
              onChange={handleChange}
              placeholder={isEdit ? '변경 시에만 입력하세요' : 'API KEY를 입력하세요'}
              required={!isEdit}
            />
          </div>

          <div className="llm-api-key-form-item">
            <label className="llm-api-key-checkbox-label">
              <input
                name="is_active"
                type="checkbox"
                checked={formData.is_active}
                onChange={handleChange}
              />
              등록 후 활성화
            </label>
          </div>
        </div>

        <div className="llm-api-key-form-actions">
          <button
            type="button"
            className="common-btn common-btn-secondary"
            onClick={() => navigate('/admin/llm-api-keys')}
            disabled={saving}
          >
            취소
          </button>
          <button type="submit" className="common-btn common-btn-primary" disabled={saving}>
            {saving ? '저장 중...' : isEdit ? '수정' : '저장'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default LlmApiKeyCreatePage;
