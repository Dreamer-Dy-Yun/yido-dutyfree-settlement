import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { systemAdminLogin } from '../services/auth';
import './SystemAdminLoginPage.css';

function SystemAdminLoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await systemAdminLogin(email, password);
      
      // 로그인 성공 시 시스템 어드민 대시보드로 이동
      navigate('/admin');
    } catch (err) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  return (
    <div className="system-admin-login-page">
      <div className="login-container">
        <h1>시스템 관리자 로그인</h1>
        <p className="login-description">서비스 제공사 관리자 전용 로그인</p>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">이메일</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="시스템 관리자 이메일을 입력하세요"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="비밀번호를 입력하세요"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="submit-button">
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <button onClick={handleBack} className="back-button">
          회사 선택으로 돌아가기
        </button>
      </div>
    </div>
  );
}

export default SystemAdminLoginPage;
