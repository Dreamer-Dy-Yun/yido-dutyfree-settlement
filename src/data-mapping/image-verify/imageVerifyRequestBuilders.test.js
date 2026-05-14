import { describe, expect, it } from 'vitest';
import { buildVerifyRequest, resolveVerifySourceId } from './imageVerifyRequestBuilders';

const receiptDetail = { source: 'verified_receipt', id: 11 };
const passportDetail = { source: 'verified_passport', id: 22 };
const coordinate = { x: 1, y: 2, width: 3, height: 4 };

describe('imageVerifyRequestBuilders', () => {
  it('resolves source id from current item when it matches edit target', () => {
    expect(
      resolveVerifySourceId({
        target: 'receipt',
        mode: 'receipt',
        currentItem: { source: 'current_receipt', id: 10 },
        receiptDetail,
        passportDetail,
      })
    ).toEqual({ source: 'current_receipt', id: 10 });
  });

  it('falls back to receipt detail when current item does not match target', () => {
    expect(
      resolveVerifySourceId({
        target: 'receipt',
        mode: 'passport',
        currentItem: { source: 'current_passport', id: 20 },
        receiptDetail,
        passportDetail,
      })
    ).toEqual(receiptDetail);
  });

  it('builds receipt verify payload without inventing missing optional values', () => {
    const result = buildVerifyRequest({
      editTarget: 'receipt',
      mode: 'receipt',
      currentItem: { source: 'current_receipt', id: 10 },
      receiptDetail,
      passportDetail,
      coordinate,
      form: {
        dutyfree_company: 'lotte',
        group_no: '',
        receipt_no: 'R-1',
        country_code: '',
        passport_no: '',
        purchaser: '',
      },
    });

    expect(result).toEqual({
      target: 'receipt',
      payload: {
        source: 'current_receipt',
        id: 10,
        dutyfree_company: 'LOTTE',
        group_no: null,
        receipt_no: 'R-1',
        country_code: null,
        passport_no: null,
        purchaser: null,
        coordinate,
      },
    });
  });

  it('builds passport verify payload', () => {
    const result = buildVerifyRequest({
      editTarget: 'passport',
      mode: 'receipt',
      currentItem: { source: 'current_receipt', id: 10 },
      receiptDetail,
      passportDetail,
      coordinate,
      form: {
        country_code: 'KR',
        passport_no: 'M123',
        name: 'KIM',
      },
    });

    expect(result).toEqual({
      target: 'passport',
      payload: {
        source: 'verified_passport',
        id: 22,
        country_code: 'KR',
        passport_no: 'M123',
        name: 'KIM',
        coordinate,
      },
    });
  });

  it('throws when target detail is missing', () => {
    expect(() =>
      buildVerifyRequest({
        editTarget: 'receipt',
        mode: 'receipt',
        currentItem: null,
        receiptDetail: null,
        passportDetail: null,
        coordinate: null,
        form: {},
      })
    ).toThrow('수정할 대상 데이터가 없습니다.');
  });
});
