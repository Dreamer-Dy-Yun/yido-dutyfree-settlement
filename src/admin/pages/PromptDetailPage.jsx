import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getPromptDetail } from '../../api/admin/systemAdminApi';
import './PromptDetailPage.css';

function PromptDetailPage() {
  const navigate = useNavigate();
  const { promptId } = useParams();
  const [row, setRow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDetail = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getPromptDetail(promptId);
      setRow(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prompt 상세 조회에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [promptId]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const handleClone = () => {
    if (!row) return;
    navigate('/admin/prompts/new', {
      state: {
        clonedPrompt: {
          purpose: row.purpose,
          type: row.type,
          prompt: row.prompt,
          note: row.note,
          is_active: row.is_active,
        },
      },
    });
  };

  if (loading) {
    return (
      <div className="common-page prompt-detail-page">
        <div className="common-card common-state">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="common-page prompt-detail-page">
      <div className="common-card common-card-header prompt-detail-header">
        <h1>Prompt 상세보기</h1>
        <div className="prompt-detail-header-actions">
          <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/prompts')}>
            목록으로
          </button>
          <button className="common-btn common-btn-primary" onClick={handleClone} disabled={!row}>
            프롬프트 복제
          </button>
        </div>
      </div>

      {error && <div className="common-card common-state error">{error}</div>}

      {!error && row && (
        <div className="common-card prompt-detail-body">
          <div className="prompt-detail-grid">
            <div className="prompt-detail-item">
              <label>Purpose</label>
              <input value={row.purpose || '-'} readOnly />
            </div>
            <div className="prompt-detail-item">
              <label>Type</label>
              <input value={row.type || '-'} readOnly />
            </div>
            <div className="prompt-detail-item">
              <label>Active</label>
              <input value={row.is_active ? 'Y' : 'N'} readOnly />
            </div>
            <div className="prompt-detail-item">
              <label>Hash</label>
              <input value={row.hash || '-'} readOnly />
            </div>
            <div className="prompt-detail-item prompt-detail-full-width">
              <label>Note</label>
              <input value={row.note || '-'} readOnly />
            </div>
            <div className="prompt-detail-item prompt-detail-full-width">
              <label>Prompt</label>
              <textarea value={row.prompt || ''} readOnly rows={14} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PromptDetailPage;
