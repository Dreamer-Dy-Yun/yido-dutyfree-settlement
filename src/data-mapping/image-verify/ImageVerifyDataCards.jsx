import { KO } from '../../locales/KO';

function ImageVerifyDataCards({
  verifiedReceipt,
  verifiedPassport,
  unverifiedReceipt,
  unverifiedPassport,
  onSelectReceipt,
  onSelectPassport,
}) {
  const text = KO.dataMapping.imageVerify;

  return (
    <div className="image-verify-list-section">
      {(verifiedReceipt || verifiedPassport) && (
        <>
          <div className="image-verify-list-title">{text.cards.verifiedData}</div>
          <div className="image-verify-list">
            {verifiedReceipt && (
              <ImageVerifyCard
                variant="verified"
                label={text.target.receipt}
                value={verifiedReceipt.receipt_no || '-'}
                onClick={() => onSelectReceipt(verifiedReceipt)}
              />
            )}
            {verifiedPassport && (
              <ImageVerifyCard
                variant="verified"
                label={text.target.passport}
                value={verifiedPassport.passport_no || '-'}
                onClick={() => onSelectPassport(verifiedPassport)}
              />
            )}
          </div>
        </>
      )}

      {(unverifiedReceipt || unverifiedPassport) && (
        <>
          <div className="image-verify-list-title">{text.cards.unverifiedData}</div>
          <div className="image-verify-list">
            {unverifiedReceipt && (
              <ImageVerifyCard
                variant="unverified"
                label={text.target.receipt}
                value={unverifiedReceipt.receipt_no || '-'}
                onClick={() => onSelectReceipt(unverifiedReceipt)}
              />
            )}
            {unverifiedPassport && (
              <ImageVerifyCard
                variant="unverified"
                label={text.target.passport}
                value={unverifiedPassport.passport_no || '-'}
                onClick={() => onSelectPassport(unverifiedPassport)}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}

function ImageVerifyCard({ variant, label, value, onClick }) {
  return (
    <div
      className={`image-verify-card image-verify-card-${variant}`}
      onClick={onClick}
    >
      <div className="image-verify-card-icon">{variant === 'verified' ? '✓' : '…'}</div>
      <div className="image-verify-card-main">
        <span className="image-verify-card-label">{label}</span>
        <span className="image-verify-card-meta">{value}</span>
      </div>
    </div>
  );
}

export default ImageVerifyDataCards;
