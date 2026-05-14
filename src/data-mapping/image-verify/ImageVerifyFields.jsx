import { KO } from '../../locales/KO';

function ImageVerifyFields({
  editTarget,
  form,
  canSendToLLM,
  onChangeTarget,
  onChangeField,
  onTryAiOcr,
}) {
  const text = KO.dataMapping.imageVerify;

  return (
    <>
      <div className="image-verify-type-toggle">
        <button
          type="button"
          className={
            editTarget === 'receipt'
              ? 'image-verify-type-btn image-verify-type-btn-active'
              : 'image-verify-type-btn'
          }
          onClick={() => onChangeTarget('receipt')}
        >
          {text.target.receipt}
        </button>
        <button
          type="button"
          className={
            editTarget === 'passport'
              ? 'image-verify-type-btn image-verify-type-btn-active'
              : 'image-verify-type-btn'
          }
          onClick={() => onChangeTarget('passport')}
        >
          {text.target.passport}
        </button>
        <button
          type="button"
          className="image-verify-region-btn"
          disabled={!canSendToLLM}
          onClick={onTryAiOcr}
        >
          AI OCR
        </button>
      </div>

      {editTarget === 'receipt' ? (
        <ReceiptFields form={form} onChangeField={onChangeField} />
      ) : (
        <PassportFields form={form} onChangeField={onChangeField} />
      )}
    </>
  );
}

function ReceiptFields({ form, onChangeField }) {
  const text = KO.dataMapping.imageVerify;

  return (
    <>
      <div className="image-verify-field">
        <label>{text.fields.dutyfreeCompanyType}</label>
        <select
          value={form.dutyfree_company}
          onChange={(e) => onChangeField('dutyfree_company', e.target.value)}
        >
          <option value="">{text.fields.select}</option>
          <option value="lotte">{text.fields.lotte}</option>
          <option value="shilla">{text.fields.shilla}</option>
        </select>
      </div>
      <div className="image-verify-field">
        <label>{text.fields.groupNo}</label>
        <input type="text" value={form.group_no} onChange={(e) => onChangeField('group_no', e.target.value)} />
      </div>
      <div className="image-verify-field">
        <label>{text.fields.receiptNo}</label>
        <input type="text" value={form.receipt_no} onChange={(e) => onChangeField('receipt_no', e.target.value)} />
      </div>
      <div className="image-verify-field">
        <label>{text.fields.countryCode}</label>
        <input type="text" value={form.country_code} onChange={(e) => onChangeField('country_code', e.target.value)} />
      </div>
      <div className="image-verify-field">
        <label>{text.fields.passportNoOptional}</label>
        <input
          type="text"
          value={form.passport_no}
          maxLength={9}
          onChange={(e) => onChangeField('passport_no', e.target.value)}
        />
      </div>
      <div className="image-verify-field">
        <label>{text.fields.purchaserOptional}</label>
        <input type="text" value={form.purchaser} onChange={(e) => onChangeField('purchaser', e.target.value)} />
      </div>
    </>
  );
}

function PassportFields({ form, onChangeField }) {
  const text = KO.dataMapping.imageVerify;

  return (
    <>
      <div className="image-verify-field">
        <label>{text.fields.countryCode}</label>
        <input type="text" value={form.country_code} onChange={(e) => onChangeField('country_code', e.target.value)} />
      </div>
      <div className="image-verify-field">
        <label>{text.fields.passportNo}</label>
        <input
          type="text"
          value={form.passport_no}
          maxLength={9}
          onChange={(e) => onChangeField('passport_no', e.target.value)}
        />
      </div>
      <div className="image-verify-field">
        <label>{text.fields.name}</label>
        <input type="text" value={form.name} onChange={(e) => onChangeField('name', e.target.value)} />
      </div>
    </>
  );
}

export default ImageVerifyFields;
