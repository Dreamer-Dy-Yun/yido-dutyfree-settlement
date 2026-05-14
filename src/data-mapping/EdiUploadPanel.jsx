import { useRef, useState } from 'react';
import { uploadEdiFile } from '../api/data-mapping/dataMappingApi';

const EDI_SOURCES = [
  { value: 'lotte', label: 'Lotte' },
  { value: 'silla', label: 'Silla' },
];

function EdiUploadPanel() {
  const [ediSource, setEdiSource] = useState('lotte');
  const [ediFile, setEdiFile] = useState(null);
  const [ediUploading, setEdiUploading] = useState(false);
  const [ediUploadMessage, setEdiUploadMessage] = useState('');
  const [ediUploadError, setEdiUploadError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const resetUploadMessage = () => {
    setEdiUploadError('');
    setEdiUploadMessage('');
  };

  const selectFile = (file) => {
    setEdiFile(file);
    resetUploadMessage();
  };

  const handleEdiUpload = async () => {
    if (!ediFile) {
      setEdiUploadError('업로드할 EDI 파일을 선택해 주세요.');
      return;
    }

    setEdiUploading(true);
    resetUploadMessage();

    try {
      const result = await uploadEdiFile(ediFile, ediSource);
      const msg = result.message || 'EDI 파일 업로드가 완료되었습니다.';
      const rows = result.rows_upserted != null ? ` (${result.rows_upserted}건 반영)` : '';
      setEdiUploadMessage(msg + rows);
    } catch (err) {
      setEdiUploadError(err.response?.data?.detail || 'EDI 파일 업로드에 실패했습니다.');
    } finally {
      setEdiUploading(false);
    }
  };

  return (
    <div className="tab-content edi-upload-section">
      <h2>EDI 업로드</h2>
      <p className="upload-hint">
        면세점을 선택한 뒤 해당 형식의 EDI 엑셀 파일을 업로드하세요.
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
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsDragging(false);
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            selectFile(e.dataTransfer.files[0]);
          }
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="file-input-hidden"
          accept=".xlsx,.xls"
          onChange={(e) => selectFile(e.target.files?.[0] || null)}
        />
        <p className="dropzone-text">
          이 영역을 클릭하거나 파일을 드래그해서 업로드할 파일을 선택하세요.
        </p>
        <p className="dropzone-subtext">지원 형식: .xlsx, .xls</p>
      </div>
      {ediFile && (
        <div className="selected-file">
          선택한 파일: <strong>{ediFile.name}</strong>
        </div>
      )}
      <div className="upload-actions">
        <button
          className="upload-button"
          type="button"
          onClick={handleEdiUpload}
          disabled={ediUploading}
        >
          {ediUploading ? '업로드 중...' : '업로드'}
        </button>
      </div>
      {ediUploadError && <div className="upload-error">{ediUploadError}</div>}
      {ediUploadMessage && !ediUploadError && (
        <div className="upload-success">{ediUploadMessage}</div>
      )}
    </div>
  );
}

export default EdiUploadPanel;
