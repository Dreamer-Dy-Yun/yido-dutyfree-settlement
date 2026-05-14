import './ImageReviewList.css';

function ImageReviewList({
  title,
  items,
  isCompleted,
  loading,
  error,
  columns,
  onToggleCompleted,
  onRowClick,
  bulkMode = false,
  selectedIds = [],
  onToggleSelect,
  onToggleSelectAll,
  onBulkConfirm,
}) {
  const hasItems = !loading && !error && items.length > 0;
  const selectedCount = selectedIds?.length || 0;

  return (
    <div className="image-review-section">
      <div className="image-review-header-row">
        <div className="image-review-title">{title}</div>
        <div className="image-review-filters">
          <label className="image-review-switch">
            <input
              type="checkbox"
              className="image-review-switch-input"
              checked={isCompleted}
              onChange={(e) => onToggleCompleted(e.target.checked)}
            />
            <span className="image-review-switch-track" aria-hidden>
              <span className="image-review-switch-thumb" />
            </span>
            <span className="image-review-switch-label">
              {isCompleted ? '작업 완료 보기' : '작업 미완료 보기'}
            </span>
          </label>

          {!isCompleted && hasItems && (
            <div className="image-review-bulk-actions">
              <button
                type="button"
                className="primary-button"
                disabled={selectedCount === 0}
                onClick={onBulkConfirm}
              >
                선택 {selectedCount}건 일괄 확인
              </button>
            </div>
          )}
        </div>
      </div>

      {loading && <div className="image-review-status">불러오는 중...</div>}
      {error && <div className="image-review-status image-review-status-error">{error}</div>}

      {!loading && !error && items.length === 0 && (
        <div className="image-review-status">표시할 데이터가 없습니다.</div>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="image-review-table-wrapper">
          <table className="image-review-table">
            <thead>
              <tr>
                {bulkMode && (
                  <th>
                    <input
                      type="checkbox"
                      onChange={(e) => onToggleSelectAll(e.target.checked)}
                      checked={
                        selectedCount > 0 && selectedCount === items.length
                      }
                    />
                  </th>
                )}
                {columns.map((col) => (
                  <th key={col.key}>{col.header}</th>
                ))}
                <th>작업 상태</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => {
                const key = item.uuid_record || item.id;
                const selected = selectedIds?.includes(key);
                return (
                  <tr
                    key={key}
                    className="image-review-row"
                    onClick={() => onRowClick(index)}
                  >
                    {bulkMode && (
                      <td onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => onToggleSelect(key)}
                        />
                      </td>
                    )}
                    {columns.map((col) => (
                      <td key={col.key}>{col.render(item)}</td>
                    ))}
                    <td>
                      <span
                        className={
                          item.is_completed
                            ? 'image-review-badge image-review-badge-completed'
                            : 'image-review-badge image-review-badge-pending'
                        }
                      >
                        {item.is_completed ? '완료' : '미완료'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ImageReviewList;

