import ConfirmDialog from './ConfirmDialog';
import { KO } from '../../locales/KO';

function ImageVerifyDialogs({
  editTarget,
  saving,
  savingAction,
  showConfirm,
  showOverwriteConfirm,
  showDeleteConfirm,
  onCloseConfirm,
  onCloseOverwrite,
  onCloseDelete,
  onConfirm,
  onOverwriteConfirm,
  onDeleteConfirm,
}) {
  const text = KO.dataMapping.imageVerify;

  return (
    <>
      <ConfirmDialog
        open={showConfirm}
        message={text.messages.confirmSave}
        cancelText={text.actions.cancel}
        confirmText={text.actions.confirm}
        onCancel={onCloseConfirm}
        onConfirm={onConfirm}
        disabled={saving}
      />

      <ConfirmDialog
        open={showOverwriteConfirm}
        message={text.messages.confirmOverwrite}
        cancelText={text.actions.cancel}
        confirmText={savingAction === 'overwrite' ? text.actions.proceeding : text.actions.proceed}
        onCancel={onCloseOverwrite}
        onConfirm={onOverwriteConfirm}
        disabled={saving}
      />

      <ConfirmDialog
        open={showDeleteConfirm}
        message={editTarget === 'receipt' ? text.messages.confirmDeleteReceipt : text.messages.confirmDeletePassport}
        cancelText={text.actions.cancel}
        confirmText={savingAction === 'delete' ? text.actions.deleting : text.actions.delete}
        onCancel={onCloseDelete}
        onConfirm={onDeleteConfirm}
        disabled={saving}
      />
    </>
  );
}

export default ImageVerifyDialogs;
