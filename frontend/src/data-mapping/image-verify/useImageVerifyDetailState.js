import { useEffect, useMemo, useState } from 'react';
import { getImageDetailsByHash } from '../../services/tenant';
import { normalizeApiError } from '../../utils/normalizeApiError';

function useImageVerifyDetailState({ mode, currentItem, onResetTransient }) {
  const [editTarget, setEditTarget] = useState(mode);
  const [form, setForm] = useState({});
  const [error, setError] = useState('');
  const [canSendToLLM, setCanSendToLLM] = useState(false);
  const [receiptDetail, setReceiptDetail] = useState(null);
  const [passportDetail, setPassportDetail] = useState(null);
  const [coordinate, setCoordinate] = useState(null);

  const imageHash = useMemo(() => currentItem?.image?.hash_img || '', [currentItem]);
  const initialCoordinate = useMemo(() => currentItem?.image?.coordinate || null, [currentItem]);
  const currentItemSource = currentItem?.source;
  const currentItemId = currentItem?.id;

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
        const detailOpts = {};
        if (mode === 'receipt' && currentItemSource != null && currentItemId != null) {
          detailOpts.receiptSource = currentItemSource;
          detailOpts.receiptId = currentItemId;
        }
        if (mode === 'passport' && currentItemSource != null && currentItemId != null) {
          detailOpts.passportSource = currentItemSource;
          detailOpts.passportId = currentItemId;
        }
        const data = await getImageDetailsByHash(imageHash, detailOpts);
        if (!mounted) return;
        setReceiptDetail(data.receipt || null);
        setPassportDetail(data.passport || null);
        setCoordinate(
          (data[mode]?.coordinate || data.receipt?.coordinate || data.passport?.coordinate || initialCoordinate) ||
            null
        );
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
        onResetTransient();
        setCanSendToLLM(false);
      }
    };
    loadDetails();
    return () => {
      mounted = false;
    };
  }, [currentItemId, currentItemSource, imageHash, initialCoordinate, mode, onResetTransient]);

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
    onResetTransient();
    setCanSendToLLM(false);
  }, [coordinate, editTarget, initialCoordinate, onResetTransient, passportDetail, receiptDetail]);

  return {
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
  };
}

export default useImageVerifyDetailState;
