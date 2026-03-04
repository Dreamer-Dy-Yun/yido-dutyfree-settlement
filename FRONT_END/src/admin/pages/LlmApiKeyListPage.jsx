import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  getLlmApiKeys,
  createLlmApiKey,
  updateLlmApiKey,
  deleteLlmApiKey,
} from '../services/systemAdminApi';
import CommonTabsRow from '../../components/CommonTabsRow';
import './CrudListPage.css';

function LlmApiKeyListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const getFilterFromLocation = () => {
    const searchParams = new URLSearchParams(location.search);
    const isActive = searchParams.get('is_active');
    if (isActive === 'true') return 'active';
    if (isActive === 'false') return 'inactive';
    return 'all';
  };
  const [filter, setFilter] = useState(getFilterFromLocation);

  const loadRows = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getLlmApiKeys({
        is_active: filter === 'all' ? undefined : filter === 'active',
      });
      setRows(data.llm_api_keys || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'LLM API KEY 목록 조회에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setFilter(getFilterFromLocation());
  }, [location.pathname, location.search]);

  useEffect(() => {
    loadRows();
  }, [filter]);

  const navigateWithFilter = (nextFilter) => {
    const params = new URLSearchParams();
    if (nextFilter === 'active') {
      params.set('is_active', 'true');
    } else if (nextFilter === 'inactive') {
      params.set('is_active', 'false');
    }
    const query = params.toString();
    navigate(query ? `/admin/llm-api-keys?${query}` : '/admin/llm-api-keys');
  };

  const handleCreate = async () => {
    const llmProvider = prompt('LLM 제공사 입력 (예: openai)');
    if (!llmProvider) return;
    const llmModel = prompt('LLM 모델 입력 (예: gpt-4o)');
    if (!llmModel) return;
    const apiKey = prompt('API KEY 입력');
    if (!apiKey) return;

    try {
      await createLlmApiKey({
        llm_provider: llmProvider,
        llm_model: llmModel,
        api_key: apiKey,
        is_active: false,
      });
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'LLM API KEY 등록에 실패했습니다.');
    }
  };

  const handleEdit = async (row) => {
    const llmProvider = prompt('LLM 제공사 수정', row.llm_provider);
    if (!llmProvider) return;
    const llmModel = prompt('LLM 모델 수정', row.llm_model);
    if (!llmModel) return;
    const apiKey = prompt('API KEY 수정', row.api_key);
    if (!apiKey) return;
    const isActive = confirm('활성 상태로 저장할까요? (취소 시 비활성)');

    try {
      await updateLlmApiKey(row.id, {
        llm_provider: llmProvider,
        llm_model: llmModel,
        api_key: apiKey,
        is_active: isActive,
      });
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'LLM API KEY 수정에 실패했습니다.');
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`삭제하시겠습니까?\nprovider=${row.llm_provider}, model=${row.llm_model}`)) {
      return;
    }
    try {
      await deleteLlmApiKey(row.id);
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'LLM API KEY 삭제에 실패했습니다.');
    }
  };

  return (
    <div className="common-page crud-list-page">
      <CommonTabsRow
        tabs={[
          { key: 'all', label: '전체' },
          { key: 'active', label: '활성' },
          { key: 'inactive', label: '비활성' },
        ]}
        activeKey={filter}
        onTabChange={navigateWithFilter}
        rightAction={
          <button className="common-btn common-btn-primary" onClick={handleCreate}>
            새 API KEY 추가
          </button>
        }
      />

      {loading && <div className="common-card common-state">로딩 중...</div>}
      {error && <div className="common-card common-state error">에러: {error}</div>}

      {!loading && !error && (
        <div className="common-card common-table-wrap">
          <table className="common-table simple-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Provider</th>
                <th>Model</th>
                <th>API KEY</th>
                <th>Active</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-cell">데이터가 없습니다.</td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.llm_provider}</td>
                    <td>{row.llm_model}</td>
                    <td>{row.api_key}</td>
                    <td>{row.is_active ? 'Y' : 'N'}</td>
                    <td className="action-buttons">
                      <button className="common-btn common-btn-primary" onClick={() => handleEdit(row)}>수정</button>
                      <button className="common-btn common-btn-secondary" onClick={() => handleDelete(row)}>삭제</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default LlmApiKeyListPage;
