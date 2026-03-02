import { useState } from 'react';
import useSessionTTL from '../hooks/useSessionTTL';
import { verifyPassword, updateMyProfile, changePassword } from '../services/auth';
import ProfileModal from './ProfileModal';
import './TenantHeader.css';

function TenantHeader({ title, currentUser, onLogout, onProfileUpdated }) {
  const { ttl, minutes, seconds } = useSessionTTL();
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  return (
    <div className="admin-header">
      <h1>{title}</h1>
      <div className="header-actions">
        {currentUser && (
          <>
            <button
              type="button"
              className="tenant-header-user-icon"
              onClick={() => setProfileModalOpen(true)}
              title="내 정보"
              aria-label="내 정보"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" fill="none" />
                <path d="M5 21c0-4 3-7 7-7s7 3 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" />
              </svg>
            </button>
            <span className="current-user">
              {currentUser.name} ({currentUser.e_mail})
            </span>
          </>
        )}
        {ttl !== null && (
          <span className="session-timer">
            세션 남은 시간:{' '}
            <strong>
              {minutes}분 {String(seconds).padStart(2, '0')}초
            </strong>
          </span>
        )}
        <button onClick={onLogout} className="logout-button">
          로그아웃
        </button>
      </div>

      <ProfileModal
        open={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        user={currentUser}
        variant="tenant"
        onVerifyPassword={verifyPassword}
        onUpdateProfile={updateMyProfile}
        onChangePassword={changePassword}
        onSaved={onProfileUpdated}
      />
    </div>
  );
}

export default TenantHeader;

