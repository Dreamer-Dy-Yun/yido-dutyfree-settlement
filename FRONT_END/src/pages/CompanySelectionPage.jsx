import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchCompany } from '../services/auth';
import './CompanySelectionPage.css';

function CompanySelectionPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState(null);

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      setError('회사명 또는 사업자번호를 입력해주세요');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      // 회사명으로 검색 (사업자번호는 나중에 추가)
      const results = await searchCompany(searchTerm, null);
      setCompanies(results);
      if (results.length === 0) {
        setError('검색 결과가 없습니다');
      }
    } catch (err) {
      setError(err.response?.data?.detail || '회사 검색에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCompany = (company) => {
    setSelectedCompany(company);
  };

  const handleConfirm = () => {
    if (selectedCompany) {
      // 선택한 회사 정보를 localStorage에 저장하고 로그인 페이지로 이동
      localStorage.setItem('selected_tenant_id', selectedCompany.id);
      localStorage.setItem('selected_tenant_name', selectedCompany.name);
      navigate('/login');
    }
  };

  const handleRegisterNew = () => {
    navigate('/company/register');
  };

  return (
    <div className="company-selection-page">
      <div className="company-selection-container">
        <h1>회사 선택</h1>
        
        <div className="search-section">
          <div className="search-input-group">
            <input
              type="text"
              placeholder="회사명 또는 사업자번호를 입력하세요"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="search-input"
            />
            <button onClick={handleSearch} disabled={loading} className="search-button">
              {loading ? '검색 중...' : '검색'}
            </button>
          </div>
          
          {error && <div className="error-message">{error}</div>}
        </div>

        {companies.length > 0 && (
          <div className="companies-list">
            <h2>검색 결과</h2>
            {companies.map((company) => (
              <div
                key={company.id}
                className={`company-item ${selectedCompany?.id === company.id ? 'selected' : ''}`}
                onClick={() => handleSelectCompany(company)}
              >
                <div className="company-name">{company.name}</div>
                {company.alias && <div className="company-alias">{company.alias}</div>}
                {company.business_no && (
                  <div className="company-business-no">사업자번호: {company.business_no}</div>
                )}
                <div className={`company-status ${company.is_active ? 'active' : 'inactive'}`}>
                  {company.is_active ? '활성' : '승인 대기'}
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedCompany && (
          <div className="action-section">
            <button onClick={handleConfirm} className="confirm-button">
              확인
            </button>
          </div>
        )}

        <div className="register-section">
          <button onClick={handleRegisterNew} className="register-button">
            신규 회사 등록
          </button>
        </div>
      </div>
    </div>
  );
}

export default CompanySelectionPage;
