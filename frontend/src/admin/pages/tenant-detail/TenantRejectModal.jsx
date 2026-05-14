function TenantRejectModal({ rejectReason, onChangeReason, onClose, onReject }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>테넌트 거부</h3>
        <p>거부 사유를 입력해주세요:</p>
        <textarea
          value={rejectReason}
          onChange={(e) => onChangeReason(e.target.value)}
          placeholder="거부 사유를 입력하세요..."
          rows="4"
        />
        <div className="modal-actions">
          <button className="common-btn common-btn-secondary" onClick={onClose}>
            취소
          </button>
          <button
            className="common-btn common-btn-danger"
            onClick={onReject}
            disabled={!rejectReason.trim()}
          >
            거부
          </button>
        </div>
      </div>
    </div>
  );
}

export default TenantRejectModal;
