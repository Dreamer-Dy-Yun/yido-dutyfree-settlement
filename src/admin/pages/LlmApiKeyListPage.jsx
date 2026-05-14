import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  getLlmApiKeys,
  updateLlmApiKey,
  deleteLlmApiKey,
} from '../../api/admin/systemAdminApi';
import CommonTabsRow from '../../components/CommonTabsRow';
import { formatRecordTimestamp } from '../../utils/dateFormat';
import { confirmUserAction, notifyUser } from '../../utils/userFeedback';
import CommonDataTable from '../components/CommonDataTable';

function LlmApiKeyListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const filterFromLocation = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    const isActive = searchParams.get('is_active');
    if (isActive === 'true') return 'active';
    if (isActive === 'false') return 'inactive';
    return 'all';
  }, [location.search]);
  const [filter, setFilter] = useState(filterFromLocation);
  const loadRows = useCallback(async () => {
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
  }, [filter]);

  useEffect(() => {
    setFilter(filterFromLocation);
  }, [filterFromLocation]);

  useEffect(() => {
    loadRows();
  }, [loadRows]);

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

  const handleToggleActive = async (row, nextActive) => {
    try {
      await updateLlmApiKey(row.id, {
        is_active: nextActive,
      });
      await loadRows();
    } catch (err) {
      notifyUser(err.response?.data?.detail || '상태 변경에 실패했습니다.');
    }
  };

  const handleDelete = async (row) => {
    if (!confirmUserAction(`삭제하시겠습니까?\nprovider=${row.llm_provider}, model=${row.llm_model}`)) {
      return;
    }
    if (!confirmUserAction('정말 삭제하시겠습니까? 삭제 후 복구할 수 없습니다.')) {
      return;
    }
    try {
      await deleteLlmApiKey(row.id);
      await loadRows();
    } catch (err) {
      notifyUser(err.response?.data?.detail || 'LLM API KEY 삭제에 실패했습니다.');
    }
  };

  return (
    <div className="common-page">
      <CommonTabsRow
        tabs={[
          { key: 'all', label: '전체' },
          { key: 'active', label: '활성' },
          { key: 'inactive', label: '비활성' },
        ]}
        activeKey={filter}
        onTabChange={navigateWithFilter}
        rightAction={
          <button className="common-btn common-btn-primary" onClick={() => navigate('/admin/llm-api-keys/new')}>
            새 API KEY 추가
          </button>
        }
      />

      {loading && <div className="common-card common-state">로딩 중...</div>}
      {error && <div className="common-card common-state error">에러: {error}</div>}

      {!loading && !error && (
        <div className="common-card">
          <CommonDataTable
            columns={[
              { key: 'id', label: 'ID' },
              { key: 'purpose', label: 'Purpose' },
              { key: 'llm_provider', label: 'Provider' },
              { key: 'llm_model', label: 'Model' },
              { key: 'api_key', label: 'API KEY', render: (row) => row.api_key },
              { key: 'created_at', label: '등록일', render: (row) => formatRecordTimestamp(row) },
              { key: 'active', label: 'Active', render: (row) => (row.is_active ? 'Y' : 'N') },
              {
                key: 'actions',
                label: '작업',
                isAction: true,
                render: (row) => (
                  <>
                    {row.is_active ? (
                      <button
                        className="common-btn common-btn-secondary"
                        onClick={() => handleToggleActive(row, false)}
                      >
                        비활성화
                      </button>
                    ) : (
                      <>
                        <button
                          className="common-btn common-btn-success"
                          onClick={() => handleToggleActive(row, true)}
                        >
                          활성화
                        </button>
                        <button className="common-btn common-btn-danger" onClick={() => handleDelete(row)}>
                          삭제
                        </button>
                      </>
                    )}
                  </>
                ),
              },
            ]}
            rows={rows}
            emptyMessage="데이터가 없습니다."
            getRowClassName={() => 'clickable-row'}
            getRowTitle={() => '더블클릭하여 수정'}
            onRowDoubleClick={(row) => navigate(`/admin/llm-api-keys/${row.id}/edit`)}
          />
        </div>
      )}
    </div>
  );
}

export default LlmApiKeyListPage;
