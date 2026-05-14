function WorkspaceDeleteConfirmModal({
  deletingUser,
  deleteConfirmText,
  isDeletingUser,
  onChangeConfirmText,
  onClose,
  onConfirm,
}) {
  return (
    <div className="workspace-modal-overlay" onClick={onClose}>
      <div className="workspace-modal-content workspace-delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
        <h2>유저 삭제 확인</h2>
        <p className="workspace-delete-confirm-text">
          <strong>{deletingUser.name || deletingUser.e_mail}</strong> 유저를 삭제합니다.
          삭제 후 복구할 수 없습니다.
        </p>
        <p className="workspace-delete-confirm-text">
          삭제를 진행하려면 아래에 <strong>지금 삭제</strong>를 입력하세요.
        </p>
        <input
          type="text"
          value={deleteConfirmText}
          onChange={(e) => onChangeConfirmText(e.target.value)}
          placeholder="지금 삭제"
          className="workspace-delete-confirm-input"
          disabled={isDeletingUser}
        />
        <div className="workspace-modal-actions">
          <button onClick={onClose} className="workspace-cancel-button" disabled={isDeletingUser}>
            취소
          </button>
          <button
            onClick={onConfirm}
            className="workspace-delete-confirm-button"
            disabled={isDeletingUser || deleteConfirmText.trim() !== '지금 삭제'}
          >
            {isDeletingUser ? '삭제 중...' : '삭제 확인'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default WorkspaceDeleteConfirmModal;
