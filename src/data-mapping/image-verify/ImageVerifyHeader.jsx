import { KO } from '../../locales/KO';

function ImageVerifyHeader({ editTarget, onClose }) {
  const text = KO.dataMapping.imageVerify;

  return (
    <div className="image-verify-header">
      <h2>{editTarget === 'receipt' ? text.title.receipt : text.title.passport}</h2>
      <button type="button" className="image-verify-close" onClick={onClose} aria-label={text.actions.close}>
        ×
      </button>
    </div>
  );
}

export default ImageVerifyHeader;
