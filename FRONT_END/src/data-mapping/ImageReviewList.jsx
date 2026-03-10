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
}) {
  return (
    <div className="image-review-section">
      <div className="image-review-header-row">
        <div className="image-review-title">{title}</div>
        <div className="image-review-filters">
          <label className="image-review-toggle">
            <input
              type="checkbox"
              checked={isCompleted}
              onChange={(e) => onToggleCompleted(e.target.checked)}
            />
            <span>{isCompleted ? '작업 완료 보기' : '작업 미완료 보기'}</span>
          </label>
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
                {columns.map((col) => (
                  <th key={col.key}>{col.header}</th>
                ))}
                <th>작업 상태</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr
                  key={item.id}
                  className="image-review-row"
                  onClick={() => onRowClick(index)}
                >
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
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ImageReviewList;

