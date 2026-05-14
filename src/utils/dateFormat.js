export function formatKoDateTime(value, fallback = '-') {
  if (!value) return fallback;

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? fallback : date.toLocaleString('ko-KR');
}

export function formatRecordTimestamp(record, keys = ['created_at', 'db_created_at'], fallback = '-') {
  const raw = keys.map((key) => record?.[key]).find(Boolean);
  return formatKoDateTime(raw, fallback);
}
