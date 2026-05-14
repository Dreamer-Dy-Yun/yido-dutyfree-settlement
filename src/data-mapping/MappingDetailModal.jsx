import { useMemo, useState } from 'react';
import ImageViewer from './ImageViewer';
import './ImageViewerLayout.css';
import './MappingDetailModal.css';

function MappingDetailModal({
  loading,
  error,
  detail,
  onClose,
  onPrev,
  onNext,
  onEditReceipt,
  onEditPassport,
}) {
  const [manualSelection, setManualSelection] = useState({ key: null, index: null });

  const receipt = detail?.receipt || null;
  const candidates = useMemo(() => detail?.candidates || [], [detail]);
  const detailKey = receipt?.uuid_record || receipt?.id || detail?.current_match?.uuid_record || null;
  const defaultSelectedIndex = useMemo(() => {
    if (!detail) return null;
    if (detail.current_match) {
      const idx = candidates.findIndex(
        (c) => c.uuid_record === detail.current_match.uuid_record,
      );
      return idx >= 0 ? idx : (candidates.length > 0 ? 0 : null);
    }
    return candidates.length > 0 ? 0 : null;
  }, [candidates, detail]);
  const selectedIndex =
    manualSelection.key === detailKey ? manualSelection.index : defaultSelectedIndex;

  const selectedPassport =
    (candidates && selectedIndex != null && candidates[selectedIndex]) ||
    detail?.current_match ||
    null;

  const receiptHash = receipt?.hash_img || '';
  const receiptCoord = receipt?.coordinate_verified || null;
  const passportHash = selectedPassport?.hash_img || '';
  const passportCoord = selectedPassport?.coordinate || null;

  return (
    <div className="workspace-modal-overlay" onClick={onClose}>
      <div
        className="mapping-detail-modal workspace-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mapping-detail-header">
          <h2>영수증-여권 매핑 상세</h2>
          <button
            type="button"
            className="image-verify-close"
            onClick={onClose}
            aria-label="닫기"
          >
            ×
          </button>
        </div>

        <div className="mapping-detail-body">
          {loading && (
            <div className="mapping-detail-loading">로딩 중...</div>
          )}
          {error && !loading && (
            <div className="mapping-detail-error">{error}</div>
          )}

          {!loading && !error && detail && (
            <>
              <div className="mapping-detail-section image-viewer-pane">
                <h3>영수증</h3>
                  <div className="image-viewer-frame">
                    {receiptHash ? (
                      <ImageViewer
                        imageHash={receiptHash}
                        coordinate={receiptCoord}
                        onChangeCoordinate={undefined}
                        editable={false}
                        showHelp={false}
                        fit="width"
                        focusMargin={0.05}
                      />
                    ) : (
                      <div className="no-image">이미지 없음</div>
                    )}
                  </div>
                <div className="mapping-detail-info-row">
                  <div className="image-viewer-info mapping-detail-info">
                    <div>면세점: {receipt?.dutyfree_company ?? '-'}</div>
                    <div>그룹: {receipt?.group_no ?? '-'}</div>
                    <div>영수증 번호: {receipt?.receipt_no ?? '-'}</div>
                    <div>국가코드: {receipt?.country_code ?? '-'}</div>
                    <div>여권번호: {receipt?.passport_no ?? '-'}</div>
                    <div>이름: {receipt?.name ?? '-'}</div>
                  </div>
                  <div className="mapping-detail-info-actions">
                    <button
                      type="button"
                      className="workspace-save-button"
                      onClick={() => onEditReceipt && onEditReceipt(receipt)}
                      disabled={!receipt}
                    >
                      수정
                    </button>
                  </div>
                </div>
              </div>

              <div className="mapping-detail-section image-viewer-pane">
                <h3>선택된 여권</h3>
                {selectedPassport ? (
                  <>
                    <div className="image-viewer-frame">
                      {passportHash ? (
                        <ImageViewer
                          imageHash={passportHash}
                          coordinate={passportCoord}
                          onChangeCoordinate={undefined}
                          editable={false}
                          showHelp={false}
                          fit="width"
                          focusMargin={0.05}
                        />
                      ) : (
                        <div className="no-image">이미지 없음</div>
                      )}
                    </div>
                    <div className="mapping-detail-info-row">
                      <div className="image-viewer-info mapping-detail-info">
                        <div>국적: {selectedPassport.country_code ?? '-'}</div>
                        <div>여권 번호: {selectedPassport.passport_no ?? '-'}</div>
                        <div>이름: {selectedPassport.name ?? '-'}</div>
                        <div>순위: {selectedPassport.rank ?? '-'}</div>
                      </div>
                      <div className="mapping-detail-info-actions">
                        <button
                          type="button"
                          className="workspace-save-button"
                          onClick={() => onEditPassport && onEditPassport(selectedPassport)}
                          disabled={!selectedPassport}
                        >
                          수정
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="mapping-detail-no-passport">
                    매핑 가능한 여권 정보가 없습니다.
                  </div>
                )}
              </div>

              <div className="mapping-detail-section mapping-detail-candidates-section">
                <h3>후보 여권</h3>
                <div className="mapping-detail-candidate-list">
                  {candidates && candidates.length > 0 ? (
                    candidates.map((c, idx) => (
                      <button
                        key={c.uuid_record}
                        type="button"
                        className={
                          idx === selectedIndex
                            ? 'mapping-candidate-card mapping-candidate-card-active'
                            : 'mapping-candidate-card'
                        }
                        onClick={() => setManualSelection({ key: detailKey, index: idx })}
                      >
                        <div className="mapping-candidate-rank">
                          #{c.rank ?? '-'}
                        </div>
                        <div className="mapping-candidate-main">
                          <div>{c.country_code ?? '-'}</div>
                          <div>{c.passport_no ?? '-'}</div>
                          <div>{c.name ?? '-'}</div>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="mapping-detail-no-candidates">
                      매핑 가능한 여권 정보가 없습니다.
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="mapping-detail-footer">
          <button
            type="button"
            className="workspace-cancel-button"
            onClick={onPrev}
          >
            ◀ 이전
          </button>
          <button
            type="button"
            className="workspace-save-button"
            onClick={onNext}
          >
            다음 ▶
          </button>
        </div>
      </div>
    </div>
  );
}

export default MappingDetailModal;
