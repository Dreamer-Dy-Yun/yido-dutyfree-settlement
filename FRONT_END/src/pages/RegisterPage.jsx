import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../services/auth';
import RegisterForm from '../components/RegisterForm';
import './RegisterPage.css';

function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async (formData) => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const result = await register(formData);
      setSuccess(result.message || '회원가입이 완료되었습니다.');
      
      // 2초 후 로그인 페이지로 이동
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        '회원가입에 실패했습니다. 입력 정보를 확인해주세요.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-page">
      <div className="register-container">
        <div className="register-header">
          <h1 className="register-title">구매대행B2C</h1>
          <p className="register-subtitle">새 계정을 만들어 시작하세요</p>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {success && (
          <div className="success-message">
            {success}
          </div>
        )}

        <RegisterForm onSubmit={handleRegister} loading={loading} />

        <div className="register-footer">
          <p>
            이미 계정이 있으신가요?{' '}
            <Link to="/login" className="link">
              로그인
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
