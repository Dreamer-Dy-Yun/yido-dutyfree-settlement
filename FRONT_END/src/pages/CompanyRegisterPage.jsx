import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerCompany } from '../services/auth';
import './CompanyRegisterPage.css';

function CompanyRegisterPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    alias: '',
    business_no: '',
    country_code: '',
    contact: '',
    email: '',
    address: '',
    admin_email: '',
    admin_name: '',
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await registerCompany(formData);
      setSuccess(true);
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || '회사 등록에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  if (success) {
    return (
      <div className="company-register-page">
        <div className="company-register-container">
          <div className="success-message">
            <h2>회사 등록이 완료되었습니다</h2>
            <p>관리자 승인 후 활성화됩니다.</p>
            <p>회사 선택 화면으로 이동합니다...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="company-register-page">
      <div className="company-register-container">
        <h1>신규 회사 등록</h1>
        
        <form onSubmit={handleSubmit} className="register-form">
          <div className="form-section">
            <h2>회사 정보</h2>
            
            <div className="form-group">
              <label htmlFor="name">회사명 <span className="required">*</span></label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="회사명을 입력하세요"
              />
            </div>

            <div className="form-group">
              <label htmlFor="alias">회사 별칭</label>
              <input
                type="text"
                id="alias"
                name="alias"
                value={formData.alias}
                onChange={handleChange}
                placeholder="회사 별칭을 입력하세요"
              />
            </div>

            <div className="form-group">
              <label htmlFor="business_no">사업자 번호</label>
              <input
                type="text"
                id="business_no"
                name="business_no"
                value={formData.business_no}
                onChange={handleChange}
                placeholder="사업자 번호를 입력하세요"
              />
            </div>

            <div className="form-group">
              <label htmlFor="country_code">국가 코드</label>
              <input
                type="number"
                id="country_code"
                name="country_code"
                value={formData.country_code}
                onChange={handleChange}
                placeholder="국가 코드를 입력하세요"
              />
            </div>

            <div className="form-group">
              <label htmlFor="contact">대표 번호</label>
              <input
                type="text"
                id="contact"
                name="contact"
                value={formData.contact}
                onChange={handleChange}
                placeholder="대표 번호를 입력하세요"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">대표 이메일</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="대표 이메일을 입력하세요"
              />
            </div>

            <div className="form-group">
              <label htmlFor="address">소재지</label>
              <textarea
                id="address"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="소재지를 입력하세요"
                rows="3"
              />
            </div>
          </div>

          <div className="form-section">
            <h2>관리자 정보</h2>
            
            <div className="form-group">
              <label htmlFor="admin_name">관리자 이름 <span className="required">*</span></label>
              <input
                type="text"
                id="admin_name"
                name="admin_name"
                value={formData.admin_name}
                onChange={handleChange}
                required
                placeholder="관리자 이름을 입력하세요"
              />
            </div>

            <div className="form-group">
              <label htmlFor="admin_email">관리자 이메일 <span className="required">*</span></label>
              <input
                type="email"
                id="admin_email"
                name="admin_email"
                value={formData.admin_email}
                onChange={handleChange}
                required
                placeholder="관리자 이메일을 입력하세요"
              />
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="form-actions">
            <button type="button" onClick={handleBack} className="back-button">
              취소
            </button>
            <button type="submit" disabled={loading} className="submit-button">
              {loading ? '등록 중...' : '등록'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CompanyRegisterPage;
