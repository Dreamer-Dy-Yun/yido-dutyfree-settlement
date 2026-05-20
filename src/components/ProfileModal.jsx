import { useState } from 'react';
import { normalizeApiError } from '../utils/normalizeApiError';
import { notifyUser } from '../utils/userFeedback';
import './ProfileModal.css';

const MODAL_VIEW = 'view';
const MODAL_PASSWORD = 'password';
const MODAL_EDIT = 'edit';

/**
 * 내 정보 조회/수정 모달 (시스템 어드민·테넌트 공용)
 * @param {boolean} open - 모달 열림 여부
 * @param {function} onClose - 닫기 콜백
 * @param {object} user - 현재 사용자 { name, alias?, e_mail, role?, department, contact }
 * @param {'system_admin'|'tenant'} variant - 시스템 어드민이면 alias 표시/수정, 테넌트면 역할 표시
 * @param {function} onVerifyPassword - (password) => Promise
 * @param {function} onUpdateProfile - (password, profile) => Promise, profile은 variant에 따라 { name, alias?, department, contact }
 * @param {function} [onChangePassword] - (currentPassword, newPassword) => Promise, 비밀번호 변경 시 호출
 * @param {function} [onSaved] - 저장 성공 후 콜백 (부모에서 사용자 재조회용)
 */
function ProfileModal({
  open,
  onClose,
  user,
  variant,
  onVerifyPassword,
  onUpdateProfile,
  onChangePassword,
  onSaved,
}) {
  const isSystemAdmin = variant === 'system_admin';
  const [modalMode, setModalMode] = useState(MODAL_VIEW);
  const [passwordInput, setPasswordInput] = useState('');
  const [passwordForEdit, setPasswordForEdit] = useState('');
  const [editForm, setEditForm] = useState({
    name: '',
    alias: '',
    department: '',
    contact: '',
    newPassword: '',
    newPasswordConfirm: '',
  });
  const [modalError, setModalError] = useState('');
  const [saving, setSaving] = useState(false);

  const closeModal = () => {
    setModalMode(MODAL_VIEW);
    setPasswordInput('');
    setPasswordForEdit('');
    setModalError('');
    onClose();
  };

  const handleClickEditProfile = () => {
    setModalMode(MODAL_PASSWORD);
    setModalError('');
    setPasswordInput('');
  };

  const handlePasswordConfirm = async () => {
    if (!passwordInput.trim()) {
      setModalError('비밀번호를 입력해주세요.');
      return;
    }
    setModalError('');
    try {
      await onVerifyPassword(passwordInput);
      setPasswordForEdit(passwordInput);
      setEditForm({
        name: user?.name ?? '',
        alias: user?.alias ?? '',
        department: user?.department ?? '',
        contact: user?.contact ?? '',
        newPassword: '',
        newPasswordConfirm: '',
      });
      setModalMode(MODAL_EDIT);
      setPasswordInput('');
    } catch (err) {
      setModalError(normalizeApiError(err, '비밀번호가 일치하지 않습니다.'));
    }
  };

  const handleCancelEdit = () => {
    setModalMode(MODAL_VIEW);
    setPasswordForEdit('');
    setModalError('');
  };

  const handleSaveProfile = async () => {
    setModalError('');
    const newPw = (editForm.newPassword || '').trim();
    const newPwConfirm = (editForm.newPasswordConfirm || '').trim();
    if (newPw) {
      if (newPw !== newPwConfirm) {
        setModalError('비밀번호 확인이 일치하지 않습니다.');
        return;
      }
      if (newPw.length < 4) {
        setModalError('새 비밀번호는 4자 이상 입력해주세요.');
        return;
      }
    }
    setSaving(true);
    try {
      const profile = {
        name: editForm.name || null,
        department: editForm.department || null,
        contact: editForm.contact || null,
      };
      if (isSystemAdmin) profile.alias = editForm.alias || null;
      await onUpdateProfile(passwordForEdit, profile);
      if (newPw && typeof onChangePassword === 'function') {
        await onChangePassword(passwordForEdit, newPw);
      }
      if (typeof onSaved === 'function') onSaved();
      setModalMode(MODAL_VIEW);
      setPasswordForEdit('');
      closeModal();
      notifyUser('정보가 수정되었습니다.');
    } catch (err) {
      const message = normalizeApiError(err, '수정에 실패했습니다.');
      setModalError(message);
      notifyUser(message);
    } finally {
      setSaving(false);
    }
  };

  if (!open || !user) return null;

  return (
    <div className="profile-modal-overlay">
      <div className="profile-modal">
        <div className="profile-modal-header">
          <h2>내 정보</h2>
          <button type="button" className="profile-modal-close" onClick={closeModal} aria-label="닫기">
            ×
          </button>
        </div>
        <div className="profile-modal-body">
          {modalMode === MODAL_VIEW && (
            <>
              <dl className="profile-modal-dl">
                <dt>이름</dt>
                <dd>{user.name || '-'}</dd>
                {isSystemAdmin && (
                  <>
                    <dt>별칭</dt>
                    <dd>{user.alias || '-'}</dd>
                  </>
                )}
                <dt>이메일</dt>
                <dd>{user.e_mail}</dd>
                {!isSystemAdmin && user.role != null && (
                  <>
                    <dt>역할</dt>
                    <dd>{user.role === 'admin' ? '관리자' : '사용자'}</dd>
                  </>
                )}
                <dt>부서</dt>
                <dd>{user.department || '-'}</dd>
                <dt>연락처</dt>
                <dd>{user.contact || '-'}</dd>
              </dl>
              <button type="button" className="profile-modal-btn-edit" onClick={handleClickEditProfile}>
                정보 수정
              </button>
            </>
          )}
          {modalMode === MODAL_PASSWORD && (
            <>
              <p className="profile-modal-password-hint">정보 수정을 위해 비밀번호를 입력해주세요.</p>
              <input
                type="password"
                className="profile-modal-password-input"
                placeholder="비밀번호"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handlePasswordConfirm();
                  }
                }}
                autoFocus
              />
              {modalError && <p className="profile-modal-error">{modalError}</p>}
              <div className="profile-modal-actions">
                <button type="button" className="profile-modal-btn-secondary" onClick={handleCancelEdit}>
                  취소
                </button>
                <button type="button" className="profile-modal-btn-primary" onClick={handlePasswordConfirm}>
                  확인
                </button>
              </div>
            </>
          )}
          {modalMode === MODAL_EDIT && (
            <>
              <div className="profile-modal-edit-form">
                <label>
                  이름
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                    placeholder="이름"
                  />
                </label>
                {isSystemAdmin && (
                  <label>
                    별칭
                    <input
                      type="text"
                      value={editForm.alias}
                      onChange={(e) => setEditForm((f) => ({ ...f, alias: e.target.value }))}
                      placeholder="별칭"
                    />
                  </label>
                )}
                <label>
                  이메일 <span className="profile-modal-muted">(수정 불가)</span>
                  <input type="text" value={user.e_mail} disabled className="profile-modal-input-disabled" />
                </label>
                <label>
                  부서
                  <input
                    type="text"
                    value={editForm.department}
                    onChange={(e) => setEditForm((f) => ({ ...f, department: e.target.value }))}
                    placeholder="부서"
                  />
                </label>
                <label>
                  연락처
                  <input
                    type="text"
                    value={editForm.contact}
                    onChange={(e) => setEditForm((f) => ({ ...f, contact: e.target.value }))}
                    placeholder="연락처"
                  />
                </label>
                <label>
                  새 비밀번호 <span className="profile-modal-muted">(변경 시에만 입력)</span>
                  <input
                    type="password"
                    value={editForm.newPassword}
                    onChange={(e) => setEditForm((f) => ({ ...f, newPassword: e.target.value }))}
                    placeholder="새 비밀번호"
                    autoComplete="new-password"
                  />
                </label>
                <label>
                  비밀번호 확인
                  <input
                    type="password"
                    value={editForm.newPasswordConfirm}
                    onChange={(e) => setEditForm((f) => ({ ...f, newPasswordConfirm: e.target.value }))}
                    placeholder="비밀번호 확인"
                    autoComplete="new-password"
                  />
                  {editForm.newPassword.length > 0 && editForm.newPasswordConfirm.length > 0 && (
                    <span className={editForm.newPassword === editForm.newPasswordConfirm ? 'profile-modal-pw-match' : 'profile-modal-pw-mismatch'}>
                      {editForm.newPassword === editForm.newPasswordConfirm ? '비밀번호가 일치합니다.' : '비밀번호가 일치하지 않습니다.'}
                    </span>
                  )}
                </label>
              </div>
              {modalError && <p className="profile-modal-error">{modalError}</p>}
              <div className="profile-modal-actions">
                <button type="button" className="profile-modal-btn-secondary" onClick={handleCancelEdit} disabled={saving}>
                  취소
                </button>
                <button type="button" className="profile-modal-btn-primary" onClick={handleSaveProfile} disabled={saving}>
                  {saving ? '저장 중…' : '수정 완료'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfileModal;
