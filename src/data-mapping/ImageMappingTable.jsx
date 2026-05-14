import { KO } from '../locales/KO';

function ImageMappingTable({
  filter,
  onFilterChange,
  listError,
  listLoading,
  rows,
  page,
  pageSize,
  totalCount,
  onOpenDetail,
  onPageChange,
}) {
  const text = KO.dataMapping.imageMapping;
  const maxPage = Math.max(1, Math.ceil(totalCount / pageSize));

  return (
    <div className="mapping-list-card">
      <div className="mapping-list-header">
        <div className="mapping-filters">
          <button
            className={filter === 'all' ? 'filter-button active' : 'filter-button'}
            type="button"
            onClick={() => onFilterChange('all')}
          >
            {text.filters.all}
          </button>
          <button
            className={filter === 'matched' ? 'filter-button active' : 'filter-button'}
            type="button"
            onClick={() => onFilterChange('matched')}
          >
            {text.filters.matched}
          </button>
          <button
            className={filter === 'unmatched' ? 'filter-button active' : 'filter-button'}
            type="button"
            onClick={() => onFilterChange('unmatched')}
          >
            {text.filters.unmatched}
          </button>
        </div>
      </div>

      {listError && <div className="upload-error">{listError}</div>}

      <table className="common-table">
        <thead>
          <tr>
            <th>{text.table.dutyfreeCompany}</th>
            <th>{text.table.receiptNo}</th>
            <th>{text.table.purchaserName}</th>
            <th>{text.table.actions}</th>
          </tr>
        </thead>
        <tbody>
          {listLoading && (
            <tr>
              <td colSpan={4} style={{ textAlign: 'center' }}>
                {text.table.loading}
              </td>
            </tr>
          )}
          {!listLoading && rows.length === 0 && (
            <tr>
              <td colSpan={4} style={{ textAlign: 'center' }}>
                {text.table.empty}
              </td>
            </tr>
          )}
          {!listLoading &&
            rows.map((row, idx) => {
              const dutyfreeCompany = row.dutyfree_company ?? '-';
              const receiptNo = row.receipt_no ?? '-';
              const purchaserName = row.name ?? '-';

              return (
                <tr key={row.uuid_receipt || `${dutyfreeCompany}-${receiptNo}-${purchaserName}`}>
                  <td>{dutyfreeCompany}</td>
                  <td>{receiptNo}</td>
                  <td>{purchaserName}</td>
                  <td>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => onOpenDetail(row, idx)}
                    >
                      {text.table.viewDetail}
                    </button>
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>

      <div className="pagination-controls">
        <button
          className="secondary-button"
          type="button"
          onClick={() => onPageChange(-1)}
          disabled={page <= 1}
        >
          {text.pagination.previous}
        </button>
        <span className="page-info">
          {text.pagination.page} {page} / {maxPage}
        </span>
        <button
          className="secondary-button"
          type="button"
          onClick={() => onPageChange(1)}
          disabled={page >= maxPage}
        >
          {text.pagination.next}
        </button>
      </div>
    </div>
  );
}

export default ImageMappingTable;
