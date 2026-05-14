import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, searchCompany } from '../api/authApi';
import { getPostLoginRedirectPath } from '../api/authTokenStore';
import {
  getCompanyDisplayName,
  readSelectedTenant,
  storeSelectedTenant,
} from '../api/tenantSelectionStore';
import './LoginPage.css';

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [companyQuery, setCompanyQuery] = useState('');
  const [companyResults, setCompanyResults] = useState([]);
  const [companyLoading, setCompanyLoading] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);

  useEffect(() => {
    // 이전에 선택해 둔 회사가 있으면 기본 선택으로 사용
    const tenant = readSelectedTenant();
    if (tenant) {
      setSelectedCompany(tenant);
      setCompanyQuery(getCompanyDisplayName(tenant));
    }
  }, []);

  const handleCompanySearchChange = async (e) => {
    const value = e.target.value;
    setCompanyQuery(value);
    setSelectedCompany(null);
    setError(null);

    if (!value.trim()) {
      setCompanyResults([]);
      return;
    }

    try {
      setCompanyLoading(true);
      const results = await searchCompany(value, null);
      setCompanyResults(results);
    } catch (err) {
      // 400: 회사명 또는 사업자번호 미입력 등은 조용히 처리
      if (err.response?.status !== 400) {
        setError(err.response?.data?.detail || '회사 검색에 실패했습니다');
      }
      setCompanyResults([]);
    } finally {
      setCompanyLoading(false);
    }
  };

  const handleSelectCompany = (company) => {
    const displayName = getCompanyDisplayName(company);
    setSelectedCompany(company);
    setCompanyQuery(displayName);
    setCompanyResults([]);
    storeSelectedTenant(company);
  };

  const resolveCompanyFromQuery = async (query) => {
    const q = (query || '').trim();
    if (!q) return null;

    const results = await searchCompany(q, null);
    if (!Array.isArray(results) || results.length === 0) return null;

    const norm = (s) => (s || '').trim().toLowerCase();
    const qn = norm(q);

    // 1) 입력값과 정확히 일치하는 후보 우선
    const exact = results.find((c) => norm(c.alias) === qn || norm(c.name) === qn);
    if (exact) return exact;

    // 2) 후보가 1개면 그걸로 확정(부분검색 결과라도 유일하면 안전)
    if (results.length === 1) return results[0];

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let company = selectedCompany;
      if (!company && companyQuery.trim()) {
        try {
          company = await resolveCompanyFromQuery(companyQuery);
          if (company) handleSelectCompany(company);
        } catch {
          // 검색 실패는 아래 공통 에러 처리로 넘김
        }
      }

      if (!company) {
        setError('회사를 선택해주세요');
        setLoading(false);
        return;
      }

      await login(email, password, company.id);
      navigate(getPostLoginRedirectPath());
    } catch (err) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* 시스템 어드민용 숨겨진 진입 버튼 (우측 상단 더블클릭) */}
      <div
        className="hidden-admin-trigger"
        onDoubleClick={() => navigate('/admin/login')}
      />
      <div className="login-container">
        <h1>로그인</h1>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="company">회사</label>
            <input
              type="text"
              id="company"
              value={companyQuery}
              onChange={handleCompanySearchChange}
              placeholder="회사명을 입력하세요 (자동완성)"
              autoComplete="off"
            />
            {companyLoading && (
              <div className="company-hint">회사 목록을 불러오는 중...</div>
            )}
            {!companyLoading && companyQuery.trim() && companyResults.length === 0 && (
              <div className="company-hint">등록된 회사가 없습니다.</div>
            )}
            {companyResults.length > 0 && (
              <div className="company-suggestions">
                {companyResults.map((company) => (
                  <div
                    key={company.id}
                    className="company-suggestion-item"
                    onClick={() => handleSelectCompany(company)}
                  >
                    <div className="company-suggestion-name">
                      {company.name}
                      {company.alias && company.alias !== company.name && (
                        <span className="company-alias"> ({company.alias})</span>
                      )}
                    </div>
                    <div className="company-suggestion-meta">
                      {company.business_no && (
                        <span className="company-business-no">
                          사업자번호: {company.business_no}
                        </span>
                      )}
                      <span
                        className={`company-status ${company.is_active ? 'active' : 'inactive'}`}
                      >
                        {company.is_active ? '활성' : '승인 대기'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

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

        <div className="register-section">
          <button
            type="button"
            className="register-button"
            onClick={() => navigate('/company/register')}
          >
            신규 회사 등록
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
