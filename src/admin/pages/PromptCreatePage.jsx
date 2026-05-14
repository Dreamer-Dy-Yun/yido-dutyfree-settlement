import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { createPrompt } from '../../api/admin/systemAdminApi';
import { notifyUser } from '../../utils/userFeedback';
import './PromptCreatePage.css';

function PromptCreatePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [inputMode, setInputMode] = useState('file'); // file | direct
  const [promptText, setPromptText] = useState('');
  const [formData, setFormData] = useState({
    purpose: 'OCR',
    type: 'SYSTEM',
    note: '',
    is_active: false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [isClonedDraft, setIsClonedDraft] = useState(false);

  useEffect(() => {
    const clonedPrompt = location.state?.clonedPrompt;
    if (!clonedPrompt) return;

    setFormData((prev) => ({
      ...prev,
      purpose: clonedPrompt.purpose || 'OCR',
      type: clonedPrompt.type || 'SYSTEM',
      note: clonedPrompt.note || '',
      is_active: Boolean(clonedPrompt.is_active),
    }));
    setPromptText(clonedPrompt.prompt || '');
    setInputMode('direct');
    setIsClonedDraft(true);
  }, [location.state]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleTxtSelect = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.txt')) {
      setError('TXT 파일만 선택할 수 있습니다.');
      return;
    }
    try {
      const text = await file.text();
      setPromptText(text);
      setError('');
    } catch {
      setError('파일 내용을 읽지 못했습니다.');
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    await handleTxtSelect(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!promptText.trim()) {
      setError('프롬프트 내용을 입력해주세요.');
      return;
    }

    try {
      setSaving(true);
      await createPrompt({
        purpose: formData.purpose,
        type: formData.type,
        prompt: promptText.trim(),
        note: formData.note.trim() || null,
        is_active: formData.is_active,
      });
      notifyUser('Prompt가 등록되었습니다.');
      setIsClonedDraft(false);
      navigate('/admin/prompts');
    } catch (err) {
      setError(err.response?.data?.detail || 'Prompt 등록에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="common-page prompt-create-page">
      <div className="common-card common-card-header prompt-create-header">
        <h1>Prompt 추가</h1>
        <button className="common-btn common-btn-secondary" onClick={() => navigate('/admin/prompts')}>
          목록으로
        </button>
      </div>

      {isClonedDraft && (
        <div className="common-card prompt-clone-warning">
          이 프롬프트는 복제된 프롬프트입니다. 저장하지 않으면 반영되지 않습니다.
        </div>
      )}

      {error && <div className="common-card common-state error">{error}</div>}

      <form className="common-card prompt-create-form" onSubmit={handleSubmit}>
        <div className="prompt-form-grid">
          <div className="prompt-form-item">
            <label htmlFor="purpose">목적</label>
            <select id="purpose" name="purpose" value={formData.purpose} onChange={handleChange}>
              <option value="OCR">OCR</option>
            </select>
          </div>

          <div className="prompt-form-item">
            <label htmlFor="type">타입</label>
            <select id="type" name="type" value={formData.type} onChange={handleChange}>
              <option value="SYSTEM">SYSTEM</option>
              <option value="USER">USER</option>
            </select>
          </div>

          <div className="prompt-form-item prompt-full-width">
            <label>입력 방식</label>
            <div className="prompt-mode-row">
              <label>
                <input
                  type="radio"
                  name="input_mode"
                  checked={inputMode === 'file'}
                  onChange={() => setInputMode('file')}
                />
                TXT 파일 선택/드래그
              </label>
              <label>
                <input
                  type="radio"
                  name="input_mode"
                  checked={inputMode === 'direct'}
                  onChange={() => setInputMode('direct')}
                />
                프롬프트 직접 입력
              </label>
            </div>
          </div>

          {inputMode === 'file' ? (
            <div className="prompt-form-item prompt-full-width">
              <label>TXT 업로드</label>
              <div className="prompt-dropzone" onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
                <input
                  type="file"
                  accept=".txt"
                  onChange={(e) => handleTxtSelect(e.target.files?.[0])}
                />
                <p>TXT 파일을 선택하거나 이 영역에 드래그하세요.</p>
              </div>
              <textarea value={promptText} readOnly placeholder="파일 내용을 미리보기 합니다." rows={10} />
            </div>
          ) : (
            <div className="prompt-form-item prompt-full-width">
              <label>프롬프트 직접 입력</label>
              <textarea
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                placeholder="프롬프트 내용을 입력하세요."
                rows={10}
              />
            </div>
          )}

          <div className="prompt-form-item prompt-full-width">
            <label htmlFor="note">노트 (선택)</label>
            <input
              id="note"
              name="note"
              type="text"
              value={formData.note}
              onChange={handleChange}
              placeholder="설명/버전 메모"
            />
          </div>

          <div className="prompt-form-item">
            <label className="prompt-checkbox-label">
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

        <div className="prompt-form-actions">
          <button
            type="button"
            className="common-btn common-btn-secondary"
            onClick={() => navigate('/admin/prompts')}
            disabled={saving}
          >
            취소
          </button>
          <button type="submit" className="common-btn common-btn-primary" disabled={saving}>
            {saving ? '저장 중...' : '저장'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default PromptCreatePage;
