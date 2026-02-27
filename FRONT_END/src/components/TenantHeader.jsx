import useSessionTTL from '../hooks/useSessionTTL';
import './TenantHeader.css';

function TenantHeader({ title, currentUser, onLogout }) {
  const { ttl, minutes, seconds } = useSessionTTL();

  return (
    <div className="admin-header">
      <h1>{title}</h1>
      <div className="header-actions">
        {currentUser && (
          <span className="current-user">
            {currentUser.name} ({currentUser.e_mail})
          </span>
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
    </div>
  );
}

export default TenantHeader;

