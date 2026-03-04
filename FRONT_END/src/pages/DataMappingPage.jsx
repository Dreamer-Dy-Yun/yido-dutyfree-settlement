import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getCurrentUser, logout } from '../services/auth';
import { uploadEdiFile, uploadImageZip, getImageOcrProgress } from '../services/tenant';
import Sidebar from '../components/Sidebar';
import SessionHeader from '../components/SessionHeader';
import CommonTabsRow from '../components/CommonTabsRow';
import { DATA_MAPPING_TABS, DEFAULT_DATA_MAPPING_TAB } from '../constants/dataMappingTabs';
import './DataMappingPage.css';

/** 면세점(EDI 출처) 목록 – 프론트 상수. 추후 API/DB로 전환 가능 */
const EDI_SOURCES = [
  { value: 'lotte', label: '롯데' },
  { value: 'silla', label: '신라' },
];

function DataMappingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);
  const [ediSource, setEdiSource] = useState('lotte');
  const [ediFile, setEdiFile] = useState(null);
  const [ediUploading, setEdiUploading] = useState(false);
  const [ediUploadMessage, setEdiUploadMessage] = useState('');
  const [ediUploadError, setEdiUploadError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const [imageFile, setImageFile] = useState(null);
  const [imageUploading, setImageUploading] = useState(false);
  const [imageUploadMessage, setImageUploadMessage] = useState('');
  const [imageUploadError, setImageUploadError] = useState('');
  const [isImageDragging, setIsImageDragging] = useState(false);
  const imageFileInputRef = useRef(null);
  const [ocrProgress, setOcrProgress] = useState(null);
  const [ocrProgressError, setOcrProgressError] = useState('');
  
  // URL 파라미터에서 탭 정보 가져오기
  const searchParams = new URLSearchParams(location.search);
  const tabFromUrl = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(tabFromUrl || DEFAULT_DATA_MAPPING_TAB);
  
  // 관리자 권한 확인
  const isAdmin = currentUser?.role === 'admin';

  useEffect(() => {
    loadCurrentUser();
  }, []);

  useEffect(() => {
    // URL 파라미터 변경 시 탭 업데이트
    const searchParams = new URLSearchParams(location.search);
    const tabFromUrl = searchParams.get('tab') || DEFAULT_DATA_MAPPING_TAB;
    setActiveTab(tabFromUrl);
  }, [location.search]);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    navigate(`/dashboard/data-mapping?tab=${tab}`);
  };

  const handleEdiFileChange = (e) => {
    const file = e.target.files && e.target.files[0] ? e.target.files[0] : null;
    setEdiFile(file);
    setEdiUploadError('');
    setEdiUploadMessage('');
  };

  const handleEdiDropZoneClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleEdiDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleEdiDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleEdiDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setEdiFile(file);
      setEdiUploadError('');
      setEdiUploadMessage('');
    }
  };

  const handleEdiUpload = async () => {
    if (!ediFile) {
      setEdiUploadError('업로드할 엑셀 파일을 선택해주세요.');
      return;
    }

    setEdiUploading(true);
    setEdiUploadError('');
    setEdiUploadMessage('');

    try {
      const result = await uploadEdiFile(ediFile, ediSource);
      const msg = result.message || '파일 업로드가 완료되었습니다.';
      const rows = result.rows_upserted != null ? ` (${result.rows_upserted}건 반영)` : '';
      setEdiUploadMessage(msg + rows);
    } catch (err) {
      setEdiUploadError(err.response?.data?.detail || '파일 업로드에 실패했습니다.');
    } finally {
      setEdiUploading(false);
    }
  };

  const handleImageFileChange = (e) => {
    const file = e.target.files && e.target.files[0] ? e.target.files[0] : null;
    setImageFile(file);
    setImageUploadError('');
    setImageUploadMessage('');
  };

  const handleImageDropZoneClick = () => {
    if (imageFileInputRef.current) {
      imageFileInputRef.current.click();
    }
  };

  const handleImageDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsImageDragging(true);
  };

  const handleImageDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsImageDragging(false);
  };

  const handleImageDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsImageDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setImageFile(file);
      setImageUploadError('');
      setImageUploadMessage('');
    }
  };

  const handleImageUpload = async () => {
    if (!imageFile) {
      setImageUploadError('업로드할 ZIP 파일을 선택해주세요.');
      return;
    }

    setImageUploading(true);
    setImageUploadError('');
    setImageUploadMessage('');

    try {
      const result = await uploadImageZip(imageFile);
      const msg = result.message || 'ZIP 업로드 요청이 전송되었습니다.';
      setImageUploadMessage(msg);
    } catch (err) {
      setImageUploadError(err.response?.data?.detail || 'ZIP 업로드에 실패했습니다.');
    } finally {
      setImageUploading(false);
    }
  };

  useEffect(() => {
    if (activeTab !== 'image-review') {
      return;
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
        setOcrProgressError(err.response?.data?.detail || '진행도 조회에 실패했습니다.');
      }
    };

    poll();
    const timerId = setInterval(poll, 2000);

    return () => {
      mounted = false;
      clearInterval(timerId);
    };
  }, [activeTab]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'edi-upload':
        return (
          <div className="tab-content edi-upload-section">
            <h2>EDI 엑셀 업로드</h2>
            <p className="upload-hint">
              면세점을 선택한 뒤, 해당 형식의 엑셀(.xlsx, .xls) 파일을 업로드하세요.
            </p>
            <div className="edi-source-row">
              <label htmlFor="edi-source">면세점</label>
              <select
                id="edi-source"
                value={ediSource}
                onChange={(e) => setEdiSource(e.target.value)}
                className="edi-source-select"
              >
                {EDI_SOURCES.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div
              className={`edi-dropzone ${isDragging ? 'dragging' : ''}`}
              onDragOver={handleEdiDragOver}
              onDragLeave={handleEdiDragLeave}
              onDrop={handleEdiDrop}
              onClick={handleEdiDropZoneClick}
            >
              <input
                type="file"
                ref={fileInputRef}
                className="file-input-hidden"
                accept=".xlsx,.xls"
                onChange={handleEdiFileChange}
              />
              <p className="dropzone-text">
                이 영역을 클릭하거나 파일을 드래그 앤 드롭하여 업로드할 파일을 선택하세요.
              </p>
              <p className="dropzone-subtext">지원 형식: .xlsx, .xls</p>
            </div>
            {ediFile && (
              <div className="selected-file">
                선택된 파일: <strong>{ediFile.name}</strong>
              </div>
            )}
            <div className="upload-actions">
              <button
                className="upload-button"
                onClick={handleEdiUpload}
                disabled={ediUploading}
              >
                {ediUploading ? '업로드 중...' : '업로드'}
              </button>
            </div>
            {ediUploadError && (
              <div className="upload-error">
                {ediUploadError}
              </div>
            )}
            {ediUploadMessage && !ediUploadError && (
              <div className="upload-success">
                {ediUploadMessage}
              </div>
            )}
          </div>
        );
      case 'image-upload':
        return (
          <div className="tab-content edi-upload-section">
            <h2>이미지 ZIP 업로드</h2>
            <p className="upload-hint">
              상품 이미지 ZIP 파일을 업로드하세요. (내부 구조 및 매핑 규칙은 추후 안내 예정)
            </p>
            <div
              className={`edi-dropzone ${isImageDragging ? 'dragging' : ''}`}
              onDragOver={handleImageDragOver}
              onDragLeave={handleImageDragLeave}
              onDrop={handleImageDrop}
              onClick={handleImageDropZoneClick}
            >
              <input
                type="file"
                ref={imageFileInputRef}
                className="file-input-hidden"
                accept=".zip"
                onChange={handleImageFileChange}
              />
              <p className="dropzone-text">
                이 영역을 클릭하거나 ZIP 파일을 드래그 앤 드롭하여 업로드할 파일을 선택하세요.
              </p>
              <p className="dropzone-subtext">지원 형식: .zip</p>
            </div>
            {imageFile && (
              <div className="selected-file">
                선택된 파일: <strong>{imageFile.name}</strong>
              </div>
            )}
            <div className="upload-actions">
              <button
                className="upload-button"
                onClick={handleImageUpload}
                disabled={imageUploading}
              >
                {imageUploading ? '업로드 중...' : '업로드'}
              </button>
            </div>
            {imageUploadError && (
              <div className="upload-error">
                {imageUploadError}
              </div>
            )}
            {imageUploadMessage && !imageUploadError && (
              <div className="upload-success">
                {imageUploadMessage}
              </div>
            )}
          </div>
        );
      case 'image-review':
        return (
          <div className="tab-content">
            <h2>이미지 확인</h2>
            <p>여권/영수증 AI OCR 결과를 확인하여 확정합니다.</p>
            {ocrProgressError && <div className="upload-error">{ocrProgressError}</div>}
            {ocrProgress && (
              <div className="upload-success">
                전체 {ocrProgress.total}건 / 처리중 {ocrProgress.processing}건 / 완료 {ocrProgress.done}건 / 대기 {ocrProgress.pending}건
                {' '}({ocrProgress.progress_percent}%)
              </div>
            )}
          </div>
        );
      case 'image-mapping':
        return (
          <div className="tab-content">
            <h2>이미지 매핑</h2>
            <p>확인된 이미지를 기준으로 여권정보와 영수증정보를 매핑합니다. 준비 중입니다.</p>
          </div>
        );
      case 'data-check':
        return <div className="tab-content"><p>데이터 확인 기능은 준비 중입니다.</p></div>;
      case 'fee-info':
        return <div className="tab-content"><p>수수료 정보 기능은 준비 중입니다.</p></div>;
      default:
        return <div className="tab-content"><p>페이지를 찾을 수 없습니다.</p></div>;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar isAdmin={isAdmin} />
      <div className="app-main">
        <SessionHeader
          title="데이터 매핑"
          currentUser={currentUser}
          onLogout={async () => {
            await logout();
          }}
          onProfileUpdated={loadCurrentUser}
        />

        <main className="app-content data-mapping-content">
          <CommonTabsRow
            tabs={DATA_MAPPING_TABS.map((tab) => ({ key: tab.id, label: tab.label }))}
            activeKey={activeTab}
            onTabChange={handleTabChange}
          />

          <div className="common-card page-content">
            {renderTabContent()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default DataMappingPage;
