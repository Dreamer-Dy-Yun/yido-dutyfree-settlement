import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getCurrentUser, logout } from '../services/auth';
import { uploadEdiFile } from '../services/tenant';
import Sidebar from '../components/Sidebar';
import TenantHeader from '../components/TenantHeader';
import './DataMappingPage.css';

function DataMappingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);
  const [ediFile, setEdiFile] = useState(null);
  const [ediUploading, setEdiUploading] = useState(false);
  const [ediUploadMessage, setEdiUploadMessage] = useState('');
  const [ediUploadError, setEdiUploadError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  
  // URL 파라미터에서 탭 정보 가져오기
  const searchParams = new URLSearchParams(location.search);
  const tabFromUrl = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(tabFromUrl || 'edi-upload');
  
  // 관리자 권한 확인
  const isAdmin = currentUser?.role === 'admin';

  useEffect(() => {
    loadCurrentUser();
  }, []);

  useEffect(() => {
    // URL 파라미터 변경 시 탭 업데이트
    const searchParams = new URLSearchParams(location.search);
    const tabFromUrl = searchParams.get('tab') || 'edi-upload';
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
      setEdiUploadError('업로드할 엑셀/CSV 파일을 선택해주세요.');
      return;
    }

    setEdiUploading(true);
    setEdiUploadError('');
    setEdiUploadMessage('');

    try {
      const result = await uploadEdiFile(ediFile);
      setEdiUploadMessage(result.message || '파일 업로드가 완료되었습니다.');
    } catch (err) {
      setEdiUploadError(err.response?.data?.detail || '파일 업로드에 실패했습니다.');
    } finally {
      setEdiUploading(false);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'edi-upload':
        return (
          <div className="tab-content edi-upload-section">
            <h2>EDI 엑셀/CSV 업로드</h2>
            <p className="upload-hint">
              엑셀(.xlsx, .xls) 또는 CSV 파일을 선택해서 업로드할 수 있습니다.
            </p>
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
                accept=".xlsx,.xls,.csv"
                onChange={handleEdiFileChange}
              />
              <p className="dropzone-text">
                이 영역을 클릭하거나 파일을 드래그 앤 드롭하여 업로드할 파일을 선택하세요.
              </p>
              <p className="dropzone-subtext">지원 형식: .xlsx, .xls, .csv</p>
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
        return <div className="tab-content"><p>이미지 업로드 기능은 준비 중입니다.</p></div>;
      case 'data-check':
        return <div className="tab-content"><p>데이터 확인 기능은 준비 중입니다.</p></div>;
      case 'fee-info':
        return <div className="tab-content"><p>수수료 정보 기능은 준비 중입니다.</p></div>;
      default:
        return <div className="tab-content"><p>페이지를 찾을 수 없습니다.</p></div>;
    }
  };

  return (
    <div className="data-mapping-page">
      <Sidebar isAdmin={isAdmin} />
      <TenantHeader
        title="데이터 매핑"
        currentUser={currentUser}
        onLogout={async () => {
          await logout();
        }}
      />

      <div className="admin-tabs">
        <button
          className={activeTab === 'edi-upload' ? 'active' : ''}
          onClick={() => handleTabChange('edi-upload')}
        >
          EDI 데이터 업로드
        </button>
        <button
          className={activeTab === 'image-upload' ? 'active' : ''}
          onClick={() => handleTabChange('image-upload')}
        >
          이미지 업로드
        </button>
        <button
          className={activeTab === 'data-check' ? 'active' : ''}
          onClick={() => handleTabChange('data-check')}
        >
          데이터 확인
        </button>
        <button
          className={activeTab === 'fee-info' ? 'active' : ''}
          onClick={() => handleTabChange('fee-info')}
        >
          수수료 정보
        </button>
      </div>

      <div className="page-content">
        {renderTabContent()}
      </div>
    </div>
  );
}

export default DataMappingPage;
