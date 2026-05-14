function TenantDeleteModal({
  deleteReason,
  deleting,
  onChangeReason,
  onClose,
  onDelete,
}) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>테넌트 삭제</h3>
        <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '12px' }}>
          주의: 삭제된 데이터는 복구할 수 없습니다.
        </p>
        <p>삭제 사유를 입력해주세요:</p>
        <textarea
          value={deleteReason}
          onChange={(e) => onChangeReason(e.target.value)}
          placeholder="삭제 사유를 입력하세요..."
          rows="4"
          disabled={deleting}
        />
        <div className="modal-actions">
          <button className="common-btn common-btn-secondary" onClick={onClose} disabled={deleting}>
            취소
          </button>
          <button
            className="common-btn common-btn-danger"
            onClick={onDelete}
            disabled={deleting || !deleteReason.trim()}
          >
            {deleting ? '삭제 중...' : '삭제'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TenantDeleteModal;
