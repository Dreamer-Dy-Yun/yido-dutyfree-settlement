const USAGE_STATS = [
  { key: 'total_images', label: '이미지' },
  { key: 'total_ocr_passport', label: 'OCR 여권' },
  { key: 'total_ocr_receipt', label: 'OCR 영수증' },
  { key: 'total_verified_passport', label: '검증된 여권' },
  { key: 'total_verified_receipt', label: '검증된 영수증' },
  { key: 'total_matched', label: '매칭된 데이터' },
  { key: 'total_llm_tokens', label: 'LLM 토큰' },
];

function WorkspaceUsageSection({ loading, usage }) {
  return (
    <div className="workspace-usage-section">
      <h2>사용량 조회</h2>
      {loading ? (
        <div className="workspace-loading">로딩 중...</div>
      ) : usage ? (
        <div className="workspace-usage-stats">
          {USAGE_STATS.map((stat) => (
            <div className="workspace-stat-card" key={stat.key}>
              <div className="workspace-stat-label">{stat.label}</div>
              <div className="workspace-stat-value">{usage[stat.key] || 0}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="workspace-no-data">데이터가 없습니다</div>
      )}
    </div>
  );
}

export default WorkspaceUsageSection;
