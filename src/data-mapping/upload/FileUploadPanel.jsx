import { useRef, useState } from 'react';
import { normalizeApiError } from '../../utils/normalizeApiError';
import '../DataMappingFeedback.css';
import './FileUploadPanel.css';

function FileUploadPanel({
  title,
  hint,
  accept,
  emptyFileMessage,
  defaultSuccessMessage,
  uploadFailedMessage,
  uploadFile,
  getSuccessMessage,
  dropzoneText = '이 영역을 클릭하거나 파일을 드래그해서 업로드할 파일을 선택하세요.',
  dropzoneSubtext,
  children,
}) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const resetUploadMessage = () => {
    setError('');
    setMessage('');
  };

  const selectFile = (nextFile) => {
    setFile(nextFile);
    resetUploadMessage();
  };

  const handleUpload = async () => {
    if (!file) {
      setError(emptyFileMessage);
      return;
    }

    setUploading(true);
    resetUploadMessage();

    try {
      const result = await uploadFile(file);
      setMessage(getSuccessMessage?.(result) || result?.message || defaultSuccessMessage);
    } catch (err) {
      setError(normalizeApiError(err, uploadFailedMessage));
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    selectFile(event.dataTransfer.files?.[0] || null);
  };

  return (
    <div className="tab-content upload-panel">
      <h2>{title}</h2>
      <p className="upload-hint">{hint}</p>
      {children}

      <div
        className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="file-input-hidden"
          accept={accept}
          onChange={(event) => selectFile(event.target.files?.[0] || null)}
        />
        <p className="dropzone-text">{dropzoneText}</p>
        {dropzoneSubtext && <p className="dropzone-subtext">{dropzoneSubtext}</p>}
      </div>

      {file && (
        <div className="selected-file">
          선택한 파일: <strong>{file.name}</strong>
        </div>
      )}

      <div className="upload-actions">
        <button className="upload-button" type="button" onClick={handleUpload} disabled={uploading}>
          {uploading ? '업로드 중...' : '업로드'}
        </button>
      </div>

      {error && <div className="upload-error">{error}</div>}
      {message && !error && <div className="upload-success">{message}</div>}
    </div>
  );
}

export default FileUploadPanel;
