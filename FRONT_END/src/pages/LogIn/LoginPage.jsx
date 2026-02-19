import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../services/auth';
import LoginForm from './components/LoginForm';
import './LoginPage.css';

function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (formData) => {
    setError('');
    setLoading(true);

    try {
      await login(formData.email, formData.password);
      navigate('/dashboard');
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        '로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-title">구매대행B2C</h1>
          <p className="login-subtitle">로그인하여 서비스를 이용하세요</p>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <LoginForm onSubmit={handleLogin} loading={loading} />

        <div className="login-footer">
          <p>
            계정이 없으신가요?{' '}
            <Link to="/register" className="link">
              회원가입
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
