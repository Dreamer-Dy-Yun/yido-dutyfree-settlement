export function resolveVerifySourceId({
  target,
  mode,
  currentItem,
  receiptDetail,
  passportDetail,
}) {
  if (target === mode && currentItem?.source != null && currentItem?.id != null) {
    return { source: currentItem.source, id: currentItem.id };
  }
  if (target === 'receipt' && receiptDetail) {
    return { source: receiptDetail.source, id: receiptDetail.id };
  }
  if (target === 'passport' && passportDetail) {
    return { source: passportDetail.source, id: passportDetail.id };
  }
  return null;
}

export function buildVerifyRequest({
  editTarget,
  mode,
  currentItem,
  receiptDetail,
  passportDetail,
  form,
  coordinate,
}) {
  if (editTarget === 'receipt' && receiptDetail) {
    const sid = resolveVerifySourceId({ target: 'receipt', mode, currentItem, receiptDetail, passportDetail });
    if (!sid) throw new Error('수정할 대상 데이터가 없습니다.');
    return {
      target: 'receipt',
      payload: {
        source: sid.source,
        id: sid.id,
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
    const sid = resolveVerifySourceId({ target: 'passport', mode, currentItem, receiptDetail, passportDetail });
    if (!sid) throw new Error('수정할 대상 데이터가 없습니다.');
    return {
      target: 'passport',
      payload: {
        source: sid.source,
        id: sid.id,
        country_code: form.country_code || '',
        passport_no: form.passport_no || '',
        name: form.name || null,
        coordinate: coordinate || null,
      },
    };
  }
  throw new Error('수정할 대상 데이터가 없습니다.');
}
