import { useEffect, useState, useCallback } from 'react';
import {
  getReceiptList,
  getPassportList,
  bulkVerifyReceipts,
  bulkVerifyPassports,
} from '../api/data-mapping/reviewApi';
import { normalizeApiError } from '../utils/normalizeApiError';
import { confirmUserAction, notifyUser } from '../utils/userFeedback';
import ImageReviewList from './ImageReviewList';
import ImageVerifyModal from './ImageVerifyModal';
import './ImageReviewPanel.css';

function ImageReviewPanel({ onVerifyModalOpenChange }) {
  const [mode, setMode] = useState('receipt'); // 'receipt' | 'passport'
  const [isCompleted, setIsCompleted] = useState(false);

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  const [selectedIds, setSelectedIds] = useState([]);
  const bulkMode = !isCompleted;

  useEffect(() => {
    if (typeof onVerifyModalOpenChange === 'function') {
      onVerifyModalOpenChange(modalOpen);
    }
  }, [modalOpen, onVerifyModalOpenChange]);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data =
        mode === 'receipt'
          ? await getReceiptList({ isCompleted })
          : await getPassportList({ isCompleted });
      setItems(Array.isArray(data) ? data : []);
      setSelectedIds([]);
    } catch (err) {
      setError(normalizeApiError(err, '목록을 불러오지 못했습니다.'));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [mode, isCompleted]);

  useEffect(() => {
    loadList();
  }, [loadList]);

  const handleToggleCompleted = (value) => {
    setIsCompleted(value);
    setSelectedIds([]);
  };

  const handleSelectItem = (index) => {
    setCurrentIndex(index);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const handleChangeIndex = (direction) => {
    if (items.length === 0) return;
    setCurrentIndex((prev) => {
      if (direction === 'prev') {
        return prev === 0 ? items.length - 1 : prev - 1;
      }
      // next
      return prev === items.length - 1 ? 0 : prev + 1;
    });
  };

  const handleSaved = (savedIndex) => {
    // 저장 성공 시 현재 항목을 목록에서 제거하고, 남은 항목이 없으면 모달을 닫는다.
    setItems((prev) => {
      const next = prev.slice();
      if (savedIndex >= 0 && savedIndex < next.length) {
        next.splice(savedIndex, 1);
      }
      if (next.length === 0) {
        setModalOpen(false);
      } else {
        setCurrentIndex((idx) => {
          if (idx >= next.length) return next.length - 1;
          return idx;
        });
      }
      return next;
    });
  };

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const handleToggleSelectAll = (checked) => {
    if (!checked) {
      setSelectedIds([]);
      return;
    }
    setSelectedIds(
      items
        .map((item) => item.uuid_record || item.id)
        .filter((v) => v !== undefined && v !== null),
    );
  };

  const handleBulkConfirm = async () => {
    if (selectedIds.length === 0) return;
    const ok = confirmUserAction(
      '일괄 확인 처리 시, 실제 이미지와 다른 데이터가 잘못 연결된 상태로 확정될 수 있습니다. 계속 진행하시겠습니까?\n잘못 연결된 데이터는 매칭 화면에서 수정이 가능합니다.',
    );
    if (!ok) return;

    try {
      if (mode === 'receipt') {
        await bulkVerifyReceipts(selectedIds);
      } else {
        await bulkVerifyPassports(selectedIds);
      }
      notifyUser(`선택된 ${selectedIds.length}건이 일괄 확인 처리되었습니다.`);
      setSelectedIds([]);
      await loadList();
    } catch (err) {
      notifyUser(normalizeApiError(err, '일괄 확인 처리 중 오류가 발생했습니다.'));
    }
  };

  return (
    <div className="image-review-root">
      <div className="image-review-mode-toggle">
        <button
          type="button"
          className={
            mode === 'receipt'
              ? 'image-review-mode-btn image-review-mode-btn-active'
              : 'image-review-mode-btn'
          }
          onClick={() => setMode('receipt')}
        >
          영수증
        </button>
        <button
          type="button"
          className={
            mode === 'passport'
              ? 'image-review-mode-btn image-review-mode-btn-active'
              : 'image-review-mode-btn'
          }
          onClick={() => setMode('passport')}
        >
          여권
        </button>
      </div>

      {mode === 'receipt' ? (
        <ImageReviewList
          title="영수증 목록"
          items={items}
          isCompleted={isCompleted}
          loading={loading}
          error={error}
          onToggleCompleted={handleToggleCompleted}
          onRowClick={handleSelectItem}
          bulkMode={bulkMode}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onToggleSelectAll={handleToggleSelectAll}
          onBulkConfirm={handleBulkConfirm}
          columns={[
            {
              key: 'dutyfree_company',
              header: '면세점',
              render: (item) => item.dutyfree_company || '-',
            },
            {
              key: 'group_no',
              header: '그룹',
              render: (item) => item.group_no || '-',
            },
            {
              key: 'receipt_no',
              header: '영수증 번호',
              render: (item) => item.receipt_no || '-',
            },
          ]}
        />
      ) : (
        <ImageReviewList
          title="여권 목록"
          items={items}
          isCompleted={isCompleted}
          loading={loading}
          error={error}
          onToggleCompleted={handleToggleCompleted}
          onRowClick={handleSelectItem}
          bulkMode={bulkMode}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onToggleSelectAll={handleToggleSelectAll}
          onBulkConfirm={handleBulkConfirm}
          columns={[
            {
              key: 'country_code',
              header: '국적',
              render: (item) => item.country_code || '-',
            },
            {
              key: 'passport_no',
              header: '여권 번호',
              render: (item) => item.passport_no || '-',
            },
            {
              key: 'name',
              header: '이름',
              render: (item) => item.name || '-',
            },
          ]}
        />
      )}

      {modalOpen && items.length > 0 && (
        <ImageVerifyModal
          mode={mode}
          items={items}
          currentIndex={currentIndex}
          onChangeIndex={handleChangeIndex}
          onClose={handleCloseModal}
          onSaved={handleSaved}
        />
      )}
    </div>
  );
}

export default ImageReviewPanel;

