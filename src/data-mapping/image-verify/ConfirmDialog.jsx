import { KO } from '../../locales/KO';

function ConfirmDialog({
  open,
  message,
  cancelText = KO.dataMapping.imageVerify.actions.cancel,
  confirmText = KO.dataMapping.imageVerify.actions.confirm,
  onCancel,
  onConfirm,
  disabled = false,
}) {
  if (!open) return null;

  return (
    <div className="image-verify-confirm-overlay">
      <div className="image-verify-confirm-dialog">
        <p>{message}</p>
        <div className="image-verify-confirm-actions">
          <button
            type="button"
            className="workspace-cancel-button"
            onClick={onCancel}
            disabled={disabled}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className="workspace-save-button"
            onClick={onConfirm}
            disabled={disabled}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
