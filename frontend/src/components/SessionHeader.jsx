import { useState } from 'react';
import useSessionTTL from '../hooks/useSessionTTL';
import { verifyPassword, updateMyProfile, changePassword } from '../services/auth';
import ProfileModal from './ProfileModal';
import AppHeader from './AppHeader';

function SessionHeader({ title, currentUser, onLogout, onProfileUpdated, sticky = true }) {
  const { ttl, minutes, seconds } = useSessionTTL();
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  return (
    <>
      <AppHeader
        title={title}
        sticky={sticky}
        showHomeButton={false}
        onOpenProfile={() => setProfileModalOpen(true)}
        displayName={currentUser?.name || '사용자'}
        email={currentUser?.e_mail}
        minutes={ttl !== null ? minutes : undefined}
        seconds={ttl !== null ? seconds : undefined}
        onLogout={onLogout}
      />
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
    </>
  );
}

export default SessionHeader;
