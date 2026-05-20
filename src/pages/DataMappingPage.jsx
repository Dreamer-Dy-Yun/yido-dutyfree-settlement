import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getImageOcrProgress } from '../api/data-mapping/reviewApi';
import DashboardShell from '../components/DashboardShell';
import CommonTabsRow from '../components/CommonTabsRow';
import { DATA_MAPPING_TABS, DEFAULT_DATA_MAPPING_TAB } from '../constants/dataMappingTabs';
import EdiUploadPanel from '../data-mapping/EdiUploadPanel';
import ImageReviewPanel from '../data-mapping/ImageReviewPanel';
import ImageZipUploadPanel from '../data-mapping/ImageZipUploadPanel';
import ImageMappingPanel from '../data-mapping/ImageMappingPanel';
import EdiUnifiedCheckPanel from '../data-mapping/EdiUnifiedCheckPanel';
import { normalizeApiError } from '../utils/normalizeApiError';
import '../data-mapping/DataMappingFeedback.css';
import './DataMappingPage.css';

function DataMappingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [ocrProgress, setOcrProgress] = useState(null);
  const [ocrProgressError, setOcrProgressError] = useState('');
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);

  const searchParams = new URLSearchParams(location.search);
  const activeTab = searchParams.get('tab') || DEFAULT_DATA_MAPPING_TAB;

  useEffect(() => {
    if (activeTab !== 'image-review' || isVerifyModalOpen) {
      return undefined;
    }

    let mounted = true;
    const poll = async () => {
      try {
        const result = await getImageOcrProgress();
        if (!mounted) return;
        setOcrProgress(result);
        setOcrProgressError('');
      } catch (err) {
        if (!mounted) return;
        setOcrProgressError(normalizeApiError(err, '진행률 조회에 실패했습니다.'));
      }
    };

    void poll();
    const timerId = setInterval(poll, 2000);

    return () => {
      mounted = false;
      clearInterval(timerId);
    };
  }, [activeTab, isVerifyModalOpen]);

  const handleTabChange = (tab) => {
    navigate(`/dashboard/data-mapping?tab=${tab}`);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'edi-upload':
        return <EdiUploadPanel />;
      case 'image-upload':
        return <ImageZipUploadPanel />;
      case 'image-review':
        return (
          <div className="tab-content">
            <h2>이미지 확인</h2>
            <p>여권/영수증 AI OCR 결과를 확인하고 확정합니다.</p>
            {ocrProgressError && <div className="upload-error">{ocrProgressError}</div>}
            {ocrProgress && (
              <div className="upload-success">
                전체 {ocrProgress.total}건 / 처리중 {ocrProgress.processing}건 / 완료{' '}
                {ocrProgress.done}건 / 대기 {ocrProgress.pending}건 ({ocrProgress.progress_percent}%)
              </div>
            )}
            <ImageReviewPanel onVerifyModalOpenChange={setIsVerifyModalOpen} />
          </div>
        );
      case 'image-mapping':
        return <ImageMappingPanel />;
      case 'data-check':
        return (
          <div className="tab-content">
            <h2>데이터 확인</h2>
            <p>EDI 매핑 실행 및 최종 결과 확인/엑셀 다운로드를 제공합니다.</p>
            <EdiUnifiedCheckPanel />
          </div>
        );
      default:
        return (
          <div className="tab-content">
            <p>페이지를 찾을 수 없습니다.</p>
          </div>
        );
    }
  };

  return (
    <DashboardShell title="데이터 매핑" contentClassName="data-mapping-content">
      <CommonTabsRow
        tabs={DATA_MAPPING_TABS.map((tab) => ({ key: tab.id, label: tab.label }))}
        activeKey={activeTab}
        onTabChange={handleTabChange}
      />

      <div className="common-card page-content">{renderTabContent()}</div>
    </DashboardShell>
  );
}

export default DataMappingPage;
