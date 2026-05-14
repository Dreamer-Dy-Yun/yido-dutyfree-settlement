import { useCallback, useState } from 'react';
import ImageViewer from './ImageViewer';
import { verifyReceipt, verifyPassport, deleteReceipt, deletePassport } from '../api/data-mapping/dataMappingApi';
import { KO } from '../locales/KO';
import { normalizeApiError } from '../utils/normalizeApiError';
import { notifyUser } from '../utils/userFeedback';
import ImageVerifyDataCards from './image-verify/ImageVerifyDataCards';
import ImageVerifyDialogs from './image-verify/ImageVerifyDialogs';
import ImageVerifyFields from './image-verify/ImageVerifyFields';
import ImageVerifyFooter from './image-verify/ImageVerifyFooter';
import ImageVerifyHeader from './image-verify/ImageVerifyHeader';
import { buildVerifyRequest, resolveVerifySourceId } from './image-verify/imageVerifyRequestBuilders';
import useImageVerifyDetailState from './image-verify/useImageVerifyDetailState';
import useImageVerifyShortcuts from './image-verify/useImageVerifyShortcuts';
import './ImageViewerLayout.css';
import './ImageVerifyModal.css';

/**
 * 공통 이미지 검수 모달
 * - mode: 'receipt' | 'passport'
 * - items: 현재 필터가 적용된 리스트 (행에 source·id가 있으면 삭제/검수 시 상세 API보다 우선)
 */
function ImageVerifyModal({
  mode,
  items,
  currentIndex,
  onChangeIndex,
  onClose,
  onSaved,
  disableNavigation = false,
}) {
  const text = KO.dataMapping.imageVerify;
  const [saving, setSaving] = useState(false);
  const [savingAction, setSavingAction] = useState(null); // 'save' | 'overwrite' | 'delete' | null
  const [showConfirm, setShowConfirm] = useState(false);
  const [showOverwriteConfirm, setShowOverwriteConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [pendingRequest, setPendingRequest] = useState(null);
  const currentItem = items[currentIndex] || null;

  const resetTransientState = useCallback(() => {
    setShowConfirm(false);
    setShowOverwriteConfirm(false);
    setShowDeleteConfirm(false);
    setPendingRequest(null);
    setSavingAction(null);
  }, []);

  const closeConfirm = useCallback(() => {
    setShowConfirm(false);
  }, []);

  const closeOverwriteConfirm = useCallback(() => {
    setShowOverwriteConfirm(false);
    setPendingRequest(null);
  }, []);

  const closeDeleteConfirm = useCallback(() => {
    setShowDeleteConfirm(false);
  }, []);

  const {
    editTarget,
    setEditTarget,
    form,
    setForm,
    error,
    setError,
    canSendToLLM,
    setCanSendToLLM,
    receiptDetail,
    passportDetail,
    coordinate,
    setCoordinate,
    imageHash,
    initialCoordinate,
  } = useImageVerifyDetailState({
    mode,
    currentItem,
    onResetTransient: resetTransientState,
  });

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    setError('');
    if (editTarget === 'receipt') {
      if (!form.dutyfree_company || !form.receipt_no) {
        setError(text.errors.receiptRequired);
        return;
      }
    } else if (editTarget === 'passport') {
      if (!form.country_code || !form.passport_no) {
        setError(text.errors.passportRequired);
        return;
      }
      if (form.passport_no && form.passport_no.length > 9) {
        setError(text.errors.passportNoLength);
        return;
      }
    }
    setShowConfirm(true);
  };

  const buildCurrentVerifyRequest = () =>
    buildVerifyRequest({
      editTarget,
      mode,
      currentItem,
      receiptDetail,
      passportDetail,
      form,
      coordinate,
    });

  const sendVerifyRequest = async (target, payload, forceMerge = false) => {
    const requestPayload = forceMerge ? { ...payload, force_merge: true } : payload;
    if (target === 'receipt') {
      return verifyReceipt(requestPayload);
    }
    return verifyPassport(requestPayload);
  };

  const handleConfirm = async () => {
    if (!currentItem) return;
    setShowConfirm(false);
    setSaving(true);
    setSavingAction('save');
    setError('');
    try {
      const request = buildCurrentVerifyRequest();
      await sendVerifyRequest(request.target, request.payload, false);
      if (typeof onSaved === 'function') {
        onSaved(currentIndex);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const forceMergeRequired = Boolean(detail && typeof detail === 'object' && detail.force_merge_required);
      if (forceMergeRequired) {
        try {
          setPendingRequest(buildCurrentVerifyRequest());
          setShowOverwriteConfirm(true);
          setError('');
        } catch (buildErr) {
          setError(normalizeApiError(buildErr, text.errors.saveFailed));
        }
      } else {
        setError(normalizeApiError(err, text.errors.saveFailed));
      }
    } finally {
      setSaving(false);
      setSavingAction(null);
    }
  };

  const handleOverwriteConfirm = async () => {
    if (!pendingRequest) return;
    setSaving(true);
    setSavingAction('overwrite');
    setError('');
    try {
      await sendVerifyRequest(pendingRequest.target, pendingRequest.payload, true);
      setShowOverwriteConfirm(false);
      setPendingRequest(null);
      if (typeof onSaved === 'function') {
        onSaved(currentIndex);
      }
      notifyUser(text.messages.overwriteSuccess);
    } catch (err) {
      const reason = normalizeApiError(err, text.errors.unknownReason);
      const message = text.messages.overwriteFailed(reason);
      setError(message);
      notifyUser(message);
    } finally {
      setSaving(false);
      setSavingAction(null);
    }
  };

  const handleDelete = () => {
    setError('');
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    setShowDeleteConfirm(false);
    setSaving(true);
    setSavingAction('delete');
    setError('');
    try {
      if (editTarget === 'receipt') {
        const sid = resolveVerifySourceId({ target: 'receipt', mode, currentItem, receiptDetail, passportDetail });
        if (!sid) throw new Error(text.errors.deleteTargetMissing);
        await deleteReceipt({ source: sid.source, id: sid.id });
      } else if (editTarget === 'passport') {
        const sid = resolveVerifySourceId({ target: 'passport', mode, currentItem, receiptDetail, passportDetail });
        if (!sid) throw new Error(text.errors.deleteTargetMissing);
        await deletePassport({ source: sid.source, id: sid.id });
      } else {
        throw new Error(text.errors.deleteTargetMissing);
      }
      if (typeof onSaved === 'function') {
        onSaved(currentIndex);
      }
      notifyUser(text.messages.deleteSuccess);
    } catch (err) {
      const msg = normalizeApiError(err, text.errors.deleteFailed);
      setError(msg);
      notifyUser(msg);
    } finally {
      setSaving(false);
      setSavingAction(null);
    }
  };

  const handlePrev = () => onChangeIndex('prev');
  const handleNext = () => onChangeIndex('next');

  useImageVerifyShortcuts({
    enabled: Boolean(currentItem),
    showConfirm,
    showOverwriteConfirm,
    showDeleteConfirm,
    disableNavigation,
    onCloseConfirm: closeConfirm,
    onCloseOverwrite: closeOverwriteConfirm,
    onCloseDelete: closeDeleteConfirm,
    onClose,
    onConfirm: handleConfirm,
    onOverwriteConfirm: handleOverwriteConfirm,
    onDeleteConfirm: handleDeleteConfirm,
    onSubmit: handleSubmit,
    onChangeIndex,
  });

  if (!currentItem) return null;

  const verifiedReceipt = receiptDetail && receiptDetail.source === 'verified' ? receiptDetail : null;
  const unverifiedReceipt = receiptDetail && receiptDetail.source === 'ocr' ? receiptDetail : null;
  const verifiedPassport = passportDetail && passportDetail.source === 'verified' ? passportDetail : null;
  const unverifiedPassport = passportDetail && passportDetail.source === 'ocr' ? passportDetail : null;

  return (
    <div className="workspace-modal-overlay" onClick={onClose}>
      <div className="image-verify-modal workspace-modal-content" onClick={(e) => e.stopPropagation()}>
        <ImageVerifyHeader editTarget={editTarget} onClose={onClose} />
        <div className="image-verify-body">
          <div className="image-verify-left image-viewer-pane">
            <div className="image-viewer-frame">
              <ImageViewer
                imageHash={imageHash}
                coordinate={coordinate}
                onChangeCoordinate={(coord) => {
                  setCoordinate(coord);
                  setCanSendToLLM(true);
                }}
                fit="width"
                focusMargin={0.05}
              />
            </div>
          </div>
          <div className="image-verify-right">
            <ImageVerifyFields
              editTarget={editTarget}
              form={form}
              canSendToLLM={canSendToLLM}
              onChangeTarget={setEditTarget}
              onChangeField={handleChange}
              onTryAiOcr={() => notifyUser(text.messages.aiOcrPreparing)}
            />

            {error && <div className="image-verify-error">{error}</div>}

            <ImageVerifyDataCards
              verifiedReceipt={verifiedReceipt}
              verifiedPassport={verifiedPassport}
              unverifiedReceipt={unverifiedReceipt}
              unverifiedPassport={unverifiedPassport}
              onSelectReceipt={(receipt) => {
                setEditTarget('receipt');
                setCoordinate(receipt.coordinate || coordinate || initialCoordinate || null);
              }}
              onSelectPassport={(passport) => {
                setEditTarget('passport');
                setCoordinate(passport.coordinate || coordinate || initialCoordinate || null);
              }}
            />

            <ImageVerifyFooter
              saving={saving}
              savingAction={savingAction}
              onPrev={handlePrev}
              onNext={handleNext}
              onDelete={handleDelete}
              onClose={onClose}
              onSubmit={handleSubmit}
            />
          </div>
        </div>

        <ImageVerifyDialogs
          editTarget={editTarget}
          saving={saving}
          savingAction={savingAction}
          showConfirm={showConfirm}
          showOverwriteConfirm={showOverwriteConfirm}
          showDeleteConfirm={showDeleteConfirm}
          onCloseConfirm={closeConfirm}
          onCloseOverwrite={closeOverwriteConfirm}
          onCloseDelete={closeDeleteConfirm}
          onConfirm={handleConfirm}
          onOverwriteConfirm={handleOverwriteConfirm}
          onDeleteConfirm={handleDeleteConfirm}
        />
      </div>
    </div>
  );
}

export default ImageVerifyModal;

