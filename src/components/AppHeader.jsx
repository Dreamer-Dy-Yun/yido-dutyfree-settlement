import './AppHeader.css';

function AppHeader({
  title,
  sticky = false,
  showHomeButton = false,
  isHomeCurrent = false,
  onHomeClick,
  homeTitle,
  onOpenProfile,
  displayName,
  department,
  email,
  minutes,
  seconds,
  onLogout,
}) {
  return (
    <header className={`app-header ${sticky ? 'app-header--sticky' : ''}`}>
      <div className="app-header-left">
        {showHomeButton && (
          <button
            className={`app-header-home-btn ${isHomeCurrent ? 'app-header-home-btn--current' : ''}`}
            onClick={isHomeCurrent ? undefined : onHomeClick}
            title={homeTitle}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle
                cx="10"
                cy="10"
                r="8"
                stroke="currentColor"
                strokeWidth="1.5"
                fill={isHomeCurrent ? 'currentColor' : 'none'}
              />
            </svg>
          </button>
        )}
        <h1 className="app-header-title">{title}</h1>
      </div>

      <div className="app-header-right">
        {(displayName || email) && (
          <div className="app-header-user-info">
            <button
              type="button"
              className="app-header-user-btn"
              onClick={onOpenProfile}
              title="내 정보"
              aria-label="내 정보"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.5" />
                <path d="M5 20c0-3.5 3.5-6 7-6s7 2.5 7 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
            <div className="app-header-user-details">
              {displayName && <span className="app-header-user-name">{displayName}</span>}
              {department && <span className="app-header-user-department">{department}</span>}
              {email && <span className="app-header-user-email">{email}</span>}
              {minutes !== undefined && seconds !== undefined && (
                <span className="app-header-session-timer">
                  세션 남은 시간: <strong>{minutes}분 {String(seconds).padStart(2, '0')}초</strong>
                </span>
              )}
            </div>
            <button className="app-header-logout-btn" onClick={onLogout}>
              로그아웃
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default AppHeader;
