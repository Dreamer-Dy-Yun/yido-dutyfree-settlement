import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  getPromptPaths,
  createPromptPath,
  updatePromptPath,
  deletePromptPath,
} from '../services/systemAdminApi';
import CommonTabsRow from '../../components/CommonTabsRow';
import './CrudListPage.css';

function PromptPathListPage() {
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
      const data = await getPromptPaths({
        is_active: filter === 'all' ? undefined : filter === 'active',
      });
      setRows(data.prompt_paths || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prompt Path 목록 조회에 실패했습니다.');
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
    navigate(query ? `/admin/prompt-paths?${query}` : '/admin/prompt-paths');
  };

  const handleCreate = async () => {
    const purpose = prompt('프롬프트 목적 입력 (예: image_ocr)');
    if (!purpose) return;
    const path = prompt('프롬프트 파일 경로 입력');
    if (!path) return;
    const isActive = confirm('활성 상태로 저장할까요? (취소 시 비활성)');

    try {
      await createPromptPath({
        purpose,
        path,
        is_active: isActive,
      });
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'Prompt Path 등록에 실패했습니다.');
    }
  };

  const handleEdit = async (row) => {
    const purpose = prompt('프롬프트 목적 수정', row.purpose);
    if (!purpose) return;
    const path = prompt('프롬프트 파일 경로 수정', row.path);
    if (!path) return;
    const isActive = confirm('활성 상태로 저장할까요? (취소 시 비활성)');

    try {
      await updatePromptPath(row.id, {
        purpose,
        path,
        is_active: isActive,
      });
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'Prompt Path 수정에 실패했습니다.');
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`삭제하시겠습니까?\npurpose=${row.purpose}`)) {
      return;
    }
    try {
      await deletePromptPath(row.id);
      await loadRows();
    } catch (err) {
      alert(err.response?.data?.detail || 'Prompt Path 삭제에 실패했습니다.');
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
            새 Prompt Path 추가
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
                <th>Purpose</th>
                <th>Path</th>
                <th>Active</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan="5" className="empty-cell">데이터가 없습니다.</td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.purpose}</td>
                    <td>{row.path}</td>
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

export default PromptPathListPage;
