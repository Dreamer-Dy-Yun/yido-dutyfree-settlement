import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { isAuthenticated, isSuperuser } from '../../api/auth/authApi';
import ProtectedRoute from './ProtectedRoute';

vi.mock('../../api/auth/authApi', () => ({
  isAuthenticated: vi.fn(),
  isSuperuser: vi.fn(),
}));

function renderProtectedRoute({ requireSuperuser = false, initialPath = '/private' } = {}) {
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          path="/private"
          element={
            <ProtectedRoute requireSuperuser={requireSuperuser}>
              <div>private content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>tenant login</div>} />
        <Route path="/admin/login" element={<div>admin login</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it('renders tenant route when tenant session exists', () => {
    isAuthenticated.mockReturnValue(true);

    renderProtectedRoute();

    expect(screen.getByText('private content')).toBeTruthy();
  });

  it('redirects tenant route to tenant login without session', () => {
    isAuthenticated.mockReturnValue(false);

    renderProtectedRoute();

    expect(screen.getByText('tenant login')).toBeTruthy();
  });

  it('renders admin route when superuser session exists', () => {
    isSuperuser.mockReturnValue(true);

    renderProtectedRoute({ requireSuperuser: true });

    expect(screen.getByText('private content')).toBeTruthy();
  });

  it('redirects admin route to admin login without superuser session', () => {
    isSuperuser.mockReturnValue(false);

    renderProtectedRoute({ requireSuperuser: true });

    expect(screen.getByText('admin login')).toBeTruthy();
  });
});
