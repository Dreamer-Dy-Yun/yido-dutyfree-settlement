import { KO } from '../locales/KO';

function ImageMappingStatus({
  status,
  statusError,
  unmatchedCount,
  isRunning,
  onMatchAttempt,
}) {
  const text = KO.dataMapping.imageMapping.status;

  return (
    <div className="mapping-status-card">
      {statusError && <div className="upload-error">{statusError}</div>}
      {status && !statusError && (
        <div className="upload-success">
          {text.unmatchedMessage(unmatchedCount)}
        </div>
      )}

      <div className="mapping-actions">
        <button
          className="primary-button"
          type="button"
          onClick={onMatchAttempt}
          disabled={isRunning || unmatchedCount === 0}
        >
          {isRunning ? text.runningButton : text.idleButton}
        </button>
      </div>
      {isRunning && (
        <div style={{ marginTop: 8, fontSize: '0.85rem', color: '#4b5563' }}>
          {text.runningHelp}
        </div>
      )}
    </div>
  );
}

export default ImageMappingStatus;
