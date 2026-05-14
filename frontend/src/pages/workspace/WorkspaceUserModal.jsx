function WorkspaceUserModal({
  editingUser,
  userFormData,
  onChangeForm,
  onClose,
  onSave,
}) {
  return (
    <div className="workspace-modal-overlay" onClick={onClose}>
      <div className="workspace-modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>{editingUser ? '유저 수정' : '유저 추가'}</h2>
        <div className="workspace-modal-form">
          <div className="workspace-form-group">
            <label>이름 *</label>
            <input
              type="text"
              value={userFormData.name}
              onChange={(e) => onChangeForm({ ...userFormData, name: e.target.value })}
              required
            />
          </div>
          <div className="workspace-form-group">
            <label>이메일 *</label>
            <input
              type="email"
              value={userFormData.e_mail}
              onChange={(e) => onChangeForm({ ...userFormData, e_mail: e.target.value })}
              required
            />
          </div>
          {!editingUser && (
            <>
              <div className="workspace-form-group">
                <label>비밀번호 *</label>
                <input
                  type="password"
                  value={userFormData.password}
                  onChange={(e) => onChangeForm({ ...userFormData, password: e.target.value })}
                  required
                />
              </div>
              <div className="workspace-form-group">
                <label>비밀번호 확인 *</label>
                <input
                  type="password"
                  value={userFormData.passwordConfirm}
                  onChange={(e) => onChangeForm({ ...userFormData, passwordConfirm: e.target.value })}
                  required
                />
                {userFormData.passwordConfirm && (
                  <div
                    className={`workspace-password-match-message ${
                      userFormData.password === userFormData.passwordConfirm ? 'match' : 'no-match'
                    }`}
                  >
                    {userFormData.password === userFormData.passwordConfirm
                      ? '✓ 비밀번호가 일치합니다'
                      : '✗ 비밀번호가 일치하지 않습니다'}
                  </div>
                )}
              </div>
            </>
          )}
          <div className="workspace-form-group">
            <label>역할</label>
            <select
              value={userFormData.role}
              onChange={(e) => onChangeForm({ ...userFormData, role: e.target.value })}
            >
              <option value="user">유저</option>
              <option value="admin">관리자</option>
            </select>
          </div>
          <div className="workspace-form-group">
            <label>부서</label>
            <input
              type="text"
              value={userFormData.department}
              onChange={(e) => onChangeForm({ ...userFormData, department: e.target.value })}
            />
          </div>
          <div className="workspace-form-group">
            <label>연락처</label>
            <input
              type="text"
              value={userFormData.contact}
              onChange={(e) => onChangeForm({ ...userFormData, contact: e.target.value })}
            />
          </div>
          <div className="workspace-modal-actions">
            <button onClick={onClose} className="workspace-cancel-button">
              취소
            </button>
            <button onClick={onSave} className="workspace-save-button">
              저장
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WorkspaceUserModal;
