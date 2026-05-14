import { describe, expect, it } from 'vitest';
import { formatKoDateTime, formatRecordTimestamp } from './dateFormat';

describe('dateFormat', () => {
  it('returns fallback for missing or invalid values', () => {
    expect(formatKoDateTime(null)).toBe('-');
    expect(formatKoDateTime('not-a-date')).toBe('-');
  });

  it('formats valid date values for Korean locale', () => {
    expect(formatKoDateTime('2026-05-14T00:00:00Z')).not.toBe('-');
  });

  it('formats the first available timestamp key from a record', () => {
    expect(
      formatRecordTimestamp({
        created_at: null,
        db_created_at: '2026-05-14T00:00:00Z',
      })
    ).not.toBe('-');
  });
});
