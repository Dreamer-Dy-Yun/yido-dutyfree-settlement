import './CommonDataTable.css';

function CommonDataTable({
  tableClassName = 'common-table',
  columns = [],
  rows = [],
  emptyMessage = '데이터가 없습니다.',
  emptyCellClassName = 'empty-cell',
  getRowKey,
  getRowClassName,
  getRowTitle,
  onRowDoubleClick,
}) {
  const mergedTableClassName = ['common-table', 'common-data-table', tableClassName]
    .filter(Boolean)
    .join(' ')
    .trim();

  return (
    <div className="common-table-wrap">
      <table className={mergedTableClassName}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key || column.label} className={column.className || ''}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={emptyCellClassName}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr
                key={getRowKey ? getRowKey(row, index) : row?.id ?? index}
                className={getRowClassName ? getRowClassName(row, index) : ''}
                title={getRowTitle ? getRowTitle(row, index) : undefined}
                onDoubleClick={onRowDoubleClick ? () => onRowDoubleClick(row, index) : undefined}
              >
                {columns.map((column) => (
                  <td key={column.key || column.label} className={column.tdClassName || ''}>
                    {column.isAction ? (
                      <div className="action-buttons">
                        {column.render ? column.render(row, index) : (row?.[column.key] ?? '-')}
                      </div>
                    ) : (
                      column.render ? column.render(row, index) : (row?.[column.key] ?? '-')
                    )}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default CommonDataTable;
