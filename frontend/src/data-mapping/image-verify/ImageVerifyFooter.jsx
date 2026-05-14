import { KO } from '../../locales/KO';

function ImageVerifyFooter({
  saving,
  savingAction,
  onPrev,
  onNext,
  onDelete,
  onClose,
  onSubmit,
}) {
  const text = KO.dataMapping.imageVerify;

  return (
    <div className="image-verify-footer">
      <div className="image-verify-nav">
        <button type="button" onClick={onPrev} className="image-verify-nav-btn">
          {text.actions.previous}
        </button>
        <button type="button" onClick={onNext} className="image-verify-nav-btn">
          {text.actions.next}
        </button>
      </div>
      <div className="image-verify-footer-actions">
        <button
          type="button"
          className="workspace-delete-confirm-button"
          onClick={onDelete}
          disabled={saving}
        >
          {text.actions.delete}
        </button>
        <button
          type="button"
          className="workspace-cancel-button"
          onClick={onClose}
          disabled={saving}
        >
          {text.actions.cancel}
        </button>
        <button
          type="button"
          className="workspace-save-button"
          onClick={onSubmit}
          disabled={saving}
        >
          {savingAction === 'save' ? text.actions.processing : text.actions.confirm}
        </button>
      </div>
    </div>
  );
}

export default ImageVerifyFooter;
