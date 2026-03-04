function CommonTabsRow({ tabs, activeKey, onTabChange, rightAction = null, className = '' }) {
  const rowClassName = ['common-tabs-row', className].filter(Boolean).join(' ');

  return (
    <div className={rowClassName}>
      <div className="common-tabs tab">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={activeKey === tab.key ? 'active' : ''}
            onClick={() => onTabChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {rightAction && <div className="common-tabs btn">{rightAction}</div>}
    </div>
  );
}

export default CommonTabsRow;
