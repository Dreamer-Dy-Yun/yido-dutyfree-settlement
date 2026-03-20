import { useEffect, useState, useMemo } from 'react';
import ImageViewer from './ImageViewer';
import {
  verifyReceipt,
  verifyPassport,
  deleteVerifiedReceipt,
  deleteVerifiedPassport,
  getImageDetailsByHash,
} from '../services/tenant';
import './ImageViewerLayout.css';
import './ImageVerifyModal.css';

function normalizeApiError(err, fallbackMessage) {
  const detail = err?.response?.data?.detail;

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const joined = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          if (typeof item.msg === 'string') return item.msg;
          if (typeof item.message === 'string') return item.message;
        }
        return '';
      })
      .filter(Boolean)
      .join(', ');
    return joined || fallbackMessage;
  }

  if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string' && detail.message.trim()) {
      return detail.message;
    }
    if (typeof detail.code === 'string' && detail.code.trim()) {
      return `${fallbackMessage} (${detail.code})`;
    }
    return fallbackMessage;
  }

  const message = err?.message;
  if (typeof message === 'string' && message.trim()) {
    return message;
  }

  return fallbackMessage;
}

function ConfirmDialog({
  open,
  message,
  cancelText = '취소',
  confirmText = '확인',
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

/**
 * 공통 이미지 검수 모달
 * - mode: 'receipt' | 'passport'
 * - items: 현재 필터가 적용된 리스트
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
  const [editTarget, setEditTarget] = useState(mode); // 'receipt' | 'passport'
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [savingAction, setSavingAction] = useState(null); // 'save' | 'overwrite' | 'delete' | null
  const [error, setError] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [showOverwriteConfirm, setShowOverwriteConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [pendingRequest, setPendingRequest] = useState(null);
  const [canSendToLLM, setCanSendToLLM] = useState(false);

  const [receiptDetail, setReceiptDetail] = useState(null);
  const [passportDetail, setPassportDetail] = useState(null);
  const [coordinate, setCoordinate] = useState(null);

  const currentItem = items[currentIndex] || null;

  const imageHash = useMemo(() => currentItem?.image?.hash_img || '', [currentItem]);
  const initialCoordinate = useMemo(() => currentItem?.image?.coordinate || null, [currentItem]);

  // 이미지 기준 영수증/여권 상세 로드
  useEffect(() => {
    let mounted = true;
    const loadDetails = async () => {
      if (!imageHash) {
        setReceiptDetail(null);
        setPassportDetail(null);
        setCoordinate(initialCoordinate);
        return;
      }
      try {
        const data = await getImageDetailsByHash(imageHash);
        if (!mounted) return;
        setReceiptDetail(data.receipt || null);
        setPassportDetail(data.passport || null);
        // 기본 좌표: verified/ocr 중 서버가 내려준 값 또는 리스트에서 받은 값
        setCoordinate(
          (data[mode]?.coordinate || data.receipt?.coordinate || data.passport?.coordinate || initialCoordinate) ||
            null
        );
        // 편집 대상 기본값 설정
        if (mode === 'receipt' && data.receipt) {
          setEditTarget('receipt');
        } else if (mode === 'passport' && data.passport) {
          setEditTarget('passport');
        } else if (data.receipt) {
          setEditTarget('receipt');
        } else if (data.passport) {
          setEditTarget('passport');
        }
      } catch (err) {
        if (!mounted) return;
        setError(normalizeApiError(err, '상세 정보를 불러오지 못했습니다.'));
      } finally {
        setShowConfirm(false);
        setCanSendToLLM(false);
      }
    };
    loadDetails();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [imageHash]);

  // 편집 대상이 바뀔 때 폼 초기화
  useEffect(() => {
    let base = null;
    if (editTarget === 'receipt' && receiptDetail) {
      base = receiptDetail;
      setForm({
        dutyfree_company: (base.dutyfree_company || '').toLowerCase(),
        group_no: base.group_no || '',
        receipt_no: base.receipt_no || '',
        country_code: base.country_code || '',
        passport_no: base.passport_no || '',
        purchaser: base.purchaser || '',
      });
      setCoordinate(base.coordinate || coordinate || initialCoordinate || null);
    } else if (editTarget === 'passport' && passportDetail) {
      base = passportDetail;
      setForm({
        country_code: base.country_code || '',
        passport_no: base.passport_no || '',
        name: base.name || '',
      });
      setCoordinate(base.coordinate || coordinate || initialCoordinate || null);
    }
    setError('');
    setShowConfirm(false);
    setShowOverwriteConfirm(false);
    setShowDeleteConfirm(false);
    setPendingRequest(null);
    setSavingAction(null);
    setCanSendToLLM(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editTarget, receiptDetail, passportDetail]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!currentItem) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        if (showOverwriteConfirm) {
          setShowOverwriteConfirm(false);
          setPendingRequest(null);
        } else if (showDeleteConfirm) {
          setShowDeleteConfirm(false);
        } else if (showConfirm) {
          setShowConfirm(false);
        } else {
          onClose();
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (showOverwriteConfirm) {
          handleOverwriteConfirm();
        } else if (showDeleteConfirm) {
          handleDeleteConfirm();
        } else if (showConfirm) {
          handleConfirm();
        } else {
          handleSubmit();
        }
      } else if (e.key === 'ArrowLeft') {
        if (disableNavigation) return;
        e.preventDefault();
        onChangeIndex('prev');
      } else if (e.key === 'ArrowRight') {
        if (disableNavigation) return;
        e.preventDefault();
        onChangeIndex('next');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentItem, showConfirm, showOverwriteConfirm, showDeleteConfirm, form, mode, onChangeIndex, onClose]);

  if (!currentItem) return null;

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    setError('');
    if (editTarget === 'receipt') {
      if (!form.dutyfree_company || !form.receipt_no) {
        setError('면세점과 영수증 번호는 필수입니다.');
        return;
      }
    } else if (editTarget === 'passport') {
      if (!form.country_code || !form.passport_no) {
        setError('국적과 여권 번호는 필수입니다.');
        return;
      }
      if (form.passport_no && form.passport_no.length > 9) {
        setError('여권 번호는 9자리 이하여야 합니다.');
        return;
      }
    }
    setShowConfirm(true);
  };

  const buildVerifyRequest = () => {
    if (editTarget === 'receipt' && receiptDetail) {
      return {
        target: 'receipt',
        payload: {
          source: receiptDetail.source,
          id: receiptDetail.id,
          dutyfree_company: (form.dutyfree_company || '').toUpperCase(),
          group_no: form.group_no || null,
          receipt_no: form.receipt_no || '',
          country_code: form.country_code || null,
          passport_no: form.passport_no || null,
          purchaser: form.purchaser || null,
          coordinate: coordinate || null,
        },
      };
    }
    if (editTarget === 'passport' && passportDetail) {
      return {
        target: 'passport',
        payload: {
          source: passportDetail.source,
          id: passportDetail.id,
          country_code: form.country_code || '',
          passport_no: form.passport_no || '',
          name: form.name || null,
          coordinate: coordinate || null,
        },
      };
    }
    throw new Error('수정할 대상 데이터가 없습니다.');
  };

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
      const request = buildVerifyRequest();
      await sendVerifyRequest(request.target, request.payload, false);
      if (typeof onSaved === 'function') {
        onSaved(currentIndex);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const forceMergeRequired = Boolean(detail && typeof detail === 'object' && detail.force_merge_required);
      if (forceMergeRequired) {
        try {
          setPendingRequest(buildVerifyRequest());
          setShowOverwriteConfirm(true);
          setError('');
        } catch (buildErr) {
          setError(normalizeApiError(buildErr, '저장에 실패했습니다.'));
        }
      } else {
        setError(normalizeApiError(err, '저장에 실패했습니다.'));
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
      alert('덮어쓰기가 성공하였습니다.');
    } catch (err) {
      const reason = normalizeApiError(err, '사유를 확인할 수 없습니다.');
      setError(`덮어쓰기가 실패하였습니다. ${reason}`);
      alert(`덮어쓰기가 실패하였습니다. ${reason}`);
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
      if (editTarget === 'receipt' && receiptDetail) {
        await deleteVerifiedReceipt({
          source: receiptDetail.source,
          id: receiptDetail.id,
        });
      } else if (editTarget === 'passport' && passportDetail) {
        await deleteVerifiedPassport({
          source: passportDetail.source,
          id: passportDetail.id,
        });
      } else {
        throw new Error('삭제할 대상 데이터가 없습니다.');
      }
      if (typeof onSaved === 'function') {
        onSaved(currentIndex);
      }
      alert('삭제가 완료되었습니다.');
    } catch (err) {
      const msg = normalizeApiError(err, '삭제에 실패했습니다.');
      setError(msg);
      alert(msg);
    } finally {
      setSaving(false);
      setSavingAction(null);
    }
  };

  const handlePrev = () => onChangeIndex('prev');
  const handleNext = () => onChangeIndex('next');

  const verifiedReceipt = receiptDetail && receiptDetail.source === 'verified' ? receiptDetail : null;
  const unverifiedReceipt = receiptDetail && receiptDetail.source === 'ocr' ? receiptDetail : null;
  const verifiedPassport = passportDetail && passportDetail.source === 'verified' ? passportDetail : null;
  const unverifiedPassport = passportDetail && passportDetail.source === 'ocr' ? passportDetail : null;

  return (
    <div className="workspace-modal-overlay" onClick={onClose}>
      <div className="image-verify-modal workspace-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="image-verify-header">
          <h2>{editTarget === 'receipt' ? '영수증/여권 검수 - 영수증' : '영수증/여권 검수 - 여권'}</h2>
          <button type="button" className="image-verify-close" onClick={onClose} aria-label="닫기">
            ×
          </button>
        </div>
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
            <div className="image-verify-type-toggle">
              <button
                type="button"
                className={
                  editTarget === 'receipt'
                    ? 'image-verify-type-btn image-verify-type-btn-active'
                    : 'image-verify-type-btn'
                }
                onClick={() => setEditTarget('receipt')}
              >
                영수증
              </button>
              <button
                type="button"
                className={
                  editTarget === 'passport'
                    ? 'image-verify-type-btn image-verify-type-btn-active'
                    : 'image-verify-type-btn'
                }
                onClick={() => setEditTarget('passport')}
              >
                여권
              </button>
              <button
                type="button"
                className="image-verify-region-btn"
                disabled={!canSendToLLM}
                onClick={() => {
                  alert('현재 준비중인 기능입니다.');
                }}
              >
                AI OCR
              </button>
            </div>

            {editTarget === 'receipt' ? (
              <>
                <div className="image-verify-field">
                  <label>면세점 종류</label>
                  <select
                    value={form.dutyfree_company}
                    onChange={(e) => handleChange('dutyfree_company', e.target.value)}
                  >
                    <option value="">선택</option>
                    <option value="lotte">롯데</option>
                    <option value="shilla">신라</option>
                  </select>
                </div>
                <div className="image-verify-field">
                  <label>그룹 번호</label>
                  <input
                    type="text"
                    value={form.group_no}
                    onChange={(e) => handleChange('group_no', e.target.value)}
                  />
                </div>
                <div className="image-verify-field">
                  <label>영수증 번호</label>
                  <input
                    type="text"
                    value={form.receipt_no}
                    onChange={(e) => handleChange('receipt_no', e.target.value)}
                  />
                </div>
                <div className="image-verify-field">
                  <label>국적</label>
                  <input
                    type="text"
                    value={form.country_code}
                    onChange={(e) => handleChange('country_code', e.target.value)}
                  />
                </div>
                <div className="image-verify-field">
                  <label>여권 번호 (9자리 이하, * 허용)</label>
                  <input
                    type="text"
                    value={form.passport_no}
                    maxLength={9}
                    onChange={(e) => handleChange('passport_no', e.target.value)}
                  />
                </div>
                <div className="image-verify-field">
                  <label>이름 (* 허용)</label>
                  <input
                    type="text"
                    value={form.purchaser}
                    onChange={(e) => handleChange('purchaser', e.target.value)}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="image-verify-field">
                  <label>국적</label>
                  <input
                    type="text"
                    value={form.country_code}
                    onChange={(e) => handleChange('country_code', e.target.value)}
                  />
                </div>
                <div className="image-verify-field">
                  <label>여권 번호 (9자리 이하)</label>
                  <input
                    type="text"
                    value={form.passport_no}
                    maxLength={9}
                    onChange={(e) => handleChange('passport_no', e.target.value)}
                  />
                </div>
                <div className="image-verify-field">
                  <label>이름</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                  />
                </div>
              </>
            )}

            {error && <div className="image-verify-error">{error}</div>}

            <div className="image-verify-list-section">
              {verifiedReceipt || verifiedPassport ? (
                <>
                  <div className="image-verify-list-title">확인된 데이터</div>
                  <div className="image-verify-list">
                    {verifiedReceipt && (
                      <div
                        className="image-verify-card image-verify-card-verified"
                        onClick={() => {
                          setEditTarget('receipt');
                          setCoordinate(verifiedReceipt.coordinate || coordinate || initialCoordinate || null);
                        }}
                      >
                        <div className="image-verify-card-icon">✓</div>
                        <div className="image-verify-card-main">
                          <span className="image-verify-card-label">영수증</span>
                          <span className="image-verify-card-meta">{verifiedReceipt.receipt_no || '-'}</span>
                        </div>
                      </div>
                    )}
                    {verifiedPassport && (
                      <div
                        className="image-verify-card image-verify-card-verified"
                        onClick={() => {
                          setEditTarget('passport');
                          setCoordinate(verifiedPassport.coordinate || coordinate || initialCoordinate || null);
                        }}
                      >
                        <div className="image-verify-card-icon">✓</div>
                        <div className="image-verify-card-main">
                          <span className="image-verify-card-label">여권</span>
                          <span className="image-verify-card-meta">{verifiedPassport.passport_no || '-'}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : null}

              {unverifiedReceipt || unverifiedPassport ? (
                <>
                  <div className="image-verify-list-title">미확인 데이터</div>
                  <div className="image-verify-list">
                    {unverifiedReceipt && (
                      <div
                        className="image-verify-card image-verify-card-unverified"
                        onClick={() => {
                          setEditTarget('receipt');
                          setCoordinate(unverifiedReceipt.coordinate || coordinate || initialCoordinate || null);
                        }}
                      >
                        <div className="image-verify-card-icon">…</div>
                        <div className="image-verify-card-main">
                          <span className="image-verify-card-label">영수증</span>
                          <span className="image-verify-card-meta">{unverifiedReceipt.receipt_no || '-'}</span>
                        </div>
                      </div>
                    )}
                    {unverifiedPassport && (
                      <div
                        className="image-verify-card image-verify-card-unverified"
                        onClick={() => {
                          setEditTarget('passport');
                          setCoordinate(unverifiedPassport.coordinate || coordinate || initialCoordinate || null);
                        }}
                      >
                        <div className="image-verify-card-icon">…</div>
                        <div className="image-verify-card-main">
                          <span className="image-verify-card-label">여권</span>
                          <span className="image-verify-card-meta">{unverifiedPassport.passport_no || '-'}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : null}
            </div>

            <div className="image-verify-footer">
              <div className="image-verify-nav">
                <button type="button" onClick={handlePrev} className="image-verify-nav-btn">
                  ◀ 이전
                </button>
                <button type="button" onClick={handleNext} className="image-verify-nav-btn">
                  다음 ▶
                </button>
              </div>
              <div className="image-verify-footer-actions">
                <button
                  type="button"
                  className="workspace-delete-confirm-button"
                  onClick={handleDelete}
                  disabled={saving}
                >
                  삭제
                </button>
                <button
                  type="button"
                  className="workspace-cancel-button"
                  onClick={onClose}
                  disabled={saving}
                >
                  취소
                </button>
                <button
                  type="button"
                  className="workspace-save-button"
                  onClick={handleSubmit}
                  disabled={saving}
                >
                  {savingAction === 'save' ? '처리 중…' : '확인'}
                </button>
              </div>
            </div>
          </div>
        </div>

        <ConfirmDialog
          open={showConfirm}
          message="수정 내용을 저장하시겠습니까?"
          cancelText="취소"
          confirmText="확인"
          onCancel={() => setShowConfirm(false)}
          onConfirm={handleConfirm}
          disabled={saving}
        />

        <ConfirmDialog
          open={showOverwriteConfirm}
          message="동일 데이터가 이미 존재합니다. 덮어쓰기를 진행하시겠습니까?"
          cancelText="취소"
          confirmText={savingAction === 'overwrite' ? '진행 중...' : '진행'}
          onCancel={() => {
            setShowOverwriteConfirm(false);
            setPendingRequest(null);
          }}
          onConfirm={handleOverwriteConfirm}
          disabled={saving}
        />

        <ConfirmDialog
          open={showDeleteConfirm}
          message={editTarget === 'receipt' ? '검증 영수증을 삭제하시겠습니까?' : '검증 여권을 삭제하시겠습니까?'}
          cancelText="취소"
          confirmText={savingAction === 'delete' ? '삭제 중...' : '삭제'}
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={handleDeleteConfirm}
          disabled={saving}
        />
      </div>
    </div>
  );
}

export default ImageVerifyModal;

