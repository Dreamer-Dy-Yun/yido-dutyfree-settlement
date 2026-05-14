import { useEffect } from 'react';

function useImageVerifyShortcuts({
  enabled,
  showConfirm,
  showOverwriteConfirm,
  showDeleteConfirm,
  disableNavigation,
  onCloseConfirm,
  onCloseOverwrite,
  onCloseDelete,
  onClose,
  onConfirm,
  onOverwriteConfirm,
  onDeleteConfirm,
  onSubmit,
  onChangeIndex,
}) {
  useEffect(() => {
    if (!enabled) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        if (showOverwriteConfirm) {
          onCloseOverwrite();
        } else if (showDeleteConfirm) {
          onCloseDelete();
        } else if (showConfirm) {
          onCloseConfirm();
        } else {
          onClose();
        }
      } else if (event.key === 'Enter') {
        event.preventDefault();
        if (showOverwriteConfirm) {
          onOverwriteConfirm();
        } else if (showDeleteConfirm) {
          onDeleteConfirm();
        } else if (showConfirm) {
          onConfirm();
        } else {
          onSubmit();
        }
      } else if (event.key === 'ArrowLeft') {
        if (disableNavigation) return;
        event.preventDefault();
        onChangeIndex('prev');
      } else if (event.key === 'ArrowRight') {
        if (disableNavigation) return;
        event.preventDefault();
        onChangeIndex('next');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    disableNavigation,
    enabled,
    onChangeIndex,
    onClose,
    onCloseConfirm,
    onCloseDelete,
    onCloseOverwrite,
    onConfirm,
    onDeleteConfirm,
    onOverwriteConfirm,
    onSubmit,
    showConfirm,
    showDeleteConfirm,
    showOverwriteConfirm,
  ]);
}

export default useImageVerifyShortcuts;
