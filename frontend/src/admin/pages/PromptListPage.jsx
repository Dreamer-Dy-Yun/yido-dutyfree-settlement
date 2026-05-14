import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  getPrompts,
  updatePrompt,
  deletePrompt,
} from '../services/systemAdminApi';
import CommonTabsRow from '../../components/CommonTabsRow';
import CommonDataTable from '../components/CommonDataTable';

function PromptListPage() {
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

  const formatCreatedAt = (row) => {
    const raw = row?.created_at || row?.db_created_at;
    if (!raw) return '-';
    const dt = new Date(raw);
    return Number.isNaN(dt.getTime()) ? '-' : dt.toLocaleString('ko-KR');
  };

  const loadRows = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getPrompts({
        is_active: filter === 'all' ? undefined : filter === 'active',
      });
      setRows(data.prompts || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prompt 목록 조회에 실패했습니다.');
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
    navigate(query ? `/admin/prompts?${query}` : '/admin/prompts');
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`삭제하시겠습니까?\npurpose=${row.purpose}\ntype=${row.type || '-'}`)) {
      return;
    }
    try {
      await deletePrompt(row.id);
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'Prompt 삭제에 실패했습니다.');
    }
  };

  const handleToggleActive = async (row, nextActive) => {
    try {
      await updatePrompt(row.id, { is_active: nextActive });
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'Prompt 상태 변경에 실패했습니다.');
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
          <button className="common-btn common-btn-primary" onClick={() => navigate('/admin/prompts/new')}>
            새 Prompt 추가
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
              { key: 'type', label: 'Type', render: (row) => row.type || '-' },
              { key: 'note', label: 'Note', render: (row) => row.note || '-' },
              { key: 'created_at', label: '등록일', render: (row) => formatCreatedAt(row) },
              { key: 'active', label: 'Active', render: (row) => (row.is_active ? 'Y' : 'N') },
              {
                key: 'actions',
                label: '작업',
                isAction: true,
                render: (row) => (
                  <>
                    <button className="common-btn common-btn-primary" onClick={() => navigate(`/admin/prompts/${row.id}`)}>
                      상세보기
                    </button>
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
                        <button
                          className="common-btn common-btn-danger"
                          onClick={() => handleDelete(row)}
                        >
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
          />
        </div>
      )}
    </div>
  );
}

export default PromptListPage;
