import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../services/auth';
import './LoginPage.css';

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedTenantName, setSelectedTenantName] = useState('');

  useEffect(() => {
    // 선택한 회사 정보 확인
    const tenantId = localStorage.getItem('selected_tenant_id');
    const tenantName = localStorage.getItem('selected_tenant_name');
    
    if (!tenantId) {
      // 회사 선택을 하지 않았으면 회사 선택 페이지로 이동
      navigate('/');
    } else {
      setSelectedTenantName(tenantName || '');
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const tenantId = parseInt(localStorage.getItem('selected_tenant_id'));
      await login(email, password, tenantId);
      
      // 로그인 성공 시 대시보드로 이동
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    localStorage.removeItem('selected_tenant_id');
    localStorage.removeItem('selected_tenant_name');
    navigate('/');
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>로그인</h1>
        {selectedTenantName && (
          <div className="selected-company">
            선택한 회사: <strong>{selectedTenantName}</strong>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">이메일</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="이메일을 입력하세요"
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

export default LoginPage;
