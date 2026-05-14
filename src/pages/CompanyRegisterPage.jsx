import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerCompany } from '../api/authApi';
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
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showDuplicateConfirm, setShowDuplicateConfirm] = useState(false);
  const [countdown, setCountdown] = useState(10);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const submitCompany = async (useExistingIfPending = false) => {
    setError(null);
    setLoading(true);

    try {
      // 백엔드 스키마(CompanyRegisterRequest)에 맞게 값 정리
      const payload = {
        ...formData,
        // 선택 입력인데 타입이 int/EmailStr인 필드는 빈 문자열을 null로 변환
        country_code: formData.country_code === '' ? null : Number(formData.country_code),
        email: formData.email.trim() === '' ? null : formData.email.trim(),
        use_existing_if_pending: useExistingIfPending,
      };

      await registerCompany(payload);
      setShowDuplicateConfirm(false);
      setSuccess(true);
      setCountdown(10);
    } catch (err) {
      const detail = err.response?.data?.detail;

      // 이미 등록된 사업자번호인 경우 → 확인 팝업 노출 (HTTP 상태코드는 사용자에게 직접 노출하지 않음)
      if (typeof detail === 'string' && detail.includes('이미 등록된 사업자번호')) {
        // 첫 시도에서만 팝업을 띄우고, 확인 후에는 다시 호출 시 useExistingIfPending=true 로 진행
        if (!useExistingIfPending) {
          setShowDuplicateConfirm(true);
          return;
        }
      }

      setError(detail || '회사 등록에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await submitCompany(false);
  };

  const handleConfirmDuplicate = async () => {
    await submitCompany(true);
  };

  const handleCancelDuplicate = () => {
    setShowDuplicateConfirm(false);
  };

  const handleBack = () => {
    navigate('/');
  };

  // 카운트다운 및 자동 이동
  useEffect(() => {
    if (success && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (success && countdown === 0) {
      navigate('/');
    }
  }, [success, countdown, navigate]);

  if (success) {
    return (
      <div className="company-register-page">
        <div className="company-register-container">
          <div className="success-message">
            <h2>회사 등록이 완료되었습니다</h2>
            <p>관리자 승인 후 활성화됩니다.</p>
            <p className="countdown-text">
              {countdown}초 후 회사 선택 화면으로 이동합니다...
            </p>
            <button 
              type="button" 
              className="back-button success-back-button"
              onClick={handleBack}
            >
              바로 돌아가기
            </button>
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
              <label htmlFor="email">
                대표 이메일
                <span className="email-alert">
                  {' '}이 메일로 승인 결과 및 초기 로그인 계정이 발송됩니다.
                </span>
              </label>
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

          {error && <div className="error-message">{error}</div>}

          {showDuplicateConfirm && (
            <div className="modal-backdrop" onClick={handleCancelDuplicate}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>이미 등록된 사업자번호입니다</h3>
                <p>이미 등록된 사업자 번호입니다. 계속 진행할까요?</p>
                <div className="modal-actions">
                  <button
                    type="button"
                    className="modal-button cancel"
                    onClick={handleCancelDuplicate}
                  >
                    아니오
                  </button>
                  <button
                    type="button"
                    className="modal-button confirm"
                    onClick={handleConfirmDuplicate}
                  >
                    예, 계속 진행
                  </button>
                </div>
              </div>
            </div>
          )}

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
