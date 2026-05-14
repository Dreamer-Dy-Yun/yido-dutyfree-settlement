import { useEffect, useRef, useState } from 'react';
import { getMatchStatus, postMatchAttempt, getMatches, getMatchDetail } from '../api/data-mapping/dataMappingApi';
import { KO } from '../locales/KO';
import { notifyUser } from '../utils/userFeedback';
import ImageMappingStatus from './ImageMappingStatus';
import ImageMappingTable from './ImageMappingTable';
import MappingDetailModal from './MappingDetailModal';
import ImageVerifyModal from './ImageVerifyModal';

/**
 * 이미지 매핑 탭 콘텐츠.
 * 상태 요약, 매핑 시도, 매핑 결과 목록, 상세 모달을 담당한다.
 */
function ImageMappingPanel() {
  const text = KO.dataMapping.imageMapping;

  const [status, setStatus] = useState(null);
  const [statusError, setStatusError] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const pollingRef = useRef(null);

  const [filter, setFilter] = useState('all'); // 'all' | 'matched' | 'unmatched'
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [rows, setRows] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState('');

  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailIndex, setDetailIndex] = useState(0);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  const [verifyModalOpen, setVerifyModalOpen] = useState(false);
  const [verifyMode, setVerifyMode] = useState('receipt'); // 'receipt' | 'passport'
  const [verifyItem, setVerifyItem] = useState(null); // { hash_img, coordinate }

  const loadStatus = async () => {
    try {
      setStatusError('');
      const data = await getMatchStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load match status:', err);
      setStatusError(text.statusLoadError);
    }
  };

  const loadList = async (opts = {}) => {
    const nextFilter = opts.filter ?? filter;
    const nextPage = opts.page ?? page;

    try {
      setListLoading(true);
      setListError('');
      const data = await getMatches({
        status: nextFilter,
        page: nextPage,
        pageSize,
      });

      // API 응답 형태가 전환되는 동안 목록 필드 차이를 흡수한다.
      const items = data.items || data.results || [];
      const total = data.total ?? data.total_count ?? items.length;

      setRows(items);
      setTotalCount(total);
      setPage(nextPage);
      setFilter(nextFilter);
    } catch (err) {
      console.error('Failed to load matches:', err);
      setListError(text.listLoadError);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    loadList({ page: 1 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  const startMatchPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    let attempts = 0;
    const maxAttempts = 15; // 최대 약 30초(2초 * 15)

    pollingRef.current = setInterval(async () => {
      attempts += 1;
      try {
        const data = await getMatchStatus();
        setStatus(data);
        await loadList({ page: 1 });

        const nextUnmatched = data?.unmatched_count ?? 0;
        if (nextUnmatched === 0 || attempts >= maxAttempts) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setIsRunning(false);
        }
      } catch (err) {
        console.error('Failed to poll match status:', err);
        if (attempts >= 3) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setIsRunning(false);
        }
      }
    }, 2000);
  };

  const handleMatchAttempt = async () => {
    if (isRunning) return;
    if (!status || status.unmatched_count === 0) {
      notifyUser(text.noUnmatchedData);
      return;
    }
    try {
      setIsRunning(true);
      await postMatchAttempt({ tryFallback: true });
      startMatchPolling();
    } catch (err) {
      console.error('Failed to trigger match attempt:', err);
      notifyUser(text.triggerFailed);
      setIsRunning(false);
    }
  };

  const handleFilterChange = async (nextFilter) => {
    await loadList({ filter: nextFilter, page: 1 });
  };

  const handlePageChange = async (direction) => {
    const nextPage = page + direction;
    if (nextPage < 1) return;
    const maxPage = Math.max(1, Math.ceil(totalCount / pageSize));
    if (nextPage > maxPage) return;
    await loadList({ page: nextPage });
  };

  const unmatchedCount = status?.unmatched_count ?? 0;

  const handleOpenDetail = async (row, index) => {
    if (!row?.uuid_receipt) return;
    try {
      setDetailModalOpen(true);
      setDetailIndex(index);
      setDetailLoading(true);
      setDetailError('');
      const data = await getMatchDetail(row.uuid_receipt);
      setDetail(data);
    } catch (err) {
      console.error('Failed to load match detail:', err);
      setDetailError(text.detailLoadError);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setDetailModalOpen(false);
    setDetail(null);
    setDetailError('');
  };

  const handleDetailChangeIndex = async (direction) => {
    if (rows.length === 0) return;

    const nextIndex =
      direction === 'prev'
        ? (detailIndex === 0 ? rows.length - 1 : detailIndex - 1)
        : (detailIndex === rows.length - 1 ? 0 : detailIndex + 1);

    const nextRow = rows[nextIndex];
    if (!nextRow?.uuid_receipt) return;

    try {
      setDetailIndex(nextIndex);
      setDetailLoading(true);
      setDetailError('');
      const data = await getMatchDetail(nextRow.uuid_receipt);
      setDetail(data);
    } catch (err) {
      console.error('Failed to load match detail:', err);
      setDetailError(text.detailLoadError);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleEditReceipt = (receipt) => {
    if (!receipt?.hash_img) return;
    setVerifyMode('receipt');
    setVerifyItem({
      hash_img: receipt.hash_img,
      coordinate: receipt.coordinate_verified || null,
    });
    setVerifyModalOpen(true);
  };

  const handleEditPassport = (passport) => {
    if (!passport?.hash_img) return;
    setVerifyMode('passport');
    setVerifyItem({
      hash_img: passport.hash_img,
      coordinate: passport.coordinate || null,
    });
    setVerifyModalOpen(true);
  };

  return (
    <div className="tab-content">
      <h2>{text.title}</h2>

      <ImageMappingStatus
        status={status}
        statusError={statusError}
        unmatchedCount={unmatchedCount}
        isRunning={isRunning}
        onMatchAttempt={handleMatchAttempt}
      />

      <ImageMappingTable
        filter={filter}
        onFilterChange={handleFilterChange}
        listError={listError}
        listLoading={listLoading}
        rows={rows}
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
        onOpenDetail={handleOpenDetail}
        onPageChange={handlePageChange}
      />

      {detailModalOpen && (
        <MappingDetailModal
          loading={detailLoading}
          error={detailError}
          detail={detail}
          onClose={handleCloseDetail}
          onPrev={() => handleDetailChangeIndex('prev')}
          onNext={() => handleDetailChangeIndex('next')}
          onEditReceipt={handleEditReceipt}
          onEditPassport={handleEditPassport}
        />
      )}

      {verifyModalOpen && verifyItem && (
        <ImageVerifyModal
          mode={verifyMode}
          items={[
            {
              image: {
                hash_img: verifyItem.hash_img,
                coordinate: verifyItem.coordinate || null,
              },
              source: 'verified',
            },
          ]}
          currentIndex={0}
          onChangeIndex={() => {}}
          onClose={() => setVerifyModalOpen(false)}
          onSaved={() => {
            setVerifyModalOpen(false);
            setDetailModalOpen(false);
            setDetail(null);
            setDetailError('');
            void loadList({ filter, page: 1 });
            void loadStatus();
          }}
          disableNavigation
        />
      )}
    </div>
  );
}

export default ImageMappingPanel;
