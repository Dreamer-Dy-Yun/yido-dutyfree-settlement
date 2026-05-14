import { afterEach, describe, expect, it, vi } from 'vitest';
import { confirmUserAction, notifyUser } from './userFeedback';

describe('userFeedback', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sends notices through the browser alert boundary', () => {
    const alertSpy = vi.fn();
    vi.stubGlobal('alert', alertSpy);

    notifyUser('saved');

    expect(alertSpy).toHaveBeenCalledWith('saved');
  });

  it('returns the browser confirmation result', () => {
    const confirmSpy = vi.fn().mockReturnValue(true);
    vi.stubGlobal('confirm', confirmSpy);

    expect(confirmUserAction('delete?')).toBe(true);
    expect(confirmSpy).toHaveBeenCalledWith('delete?');
  });
});
