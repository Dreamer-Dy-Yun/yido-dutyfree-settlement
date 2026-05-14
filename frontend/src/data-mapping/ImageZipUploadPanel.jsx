import { useRef, useState } from 'react';
import { uploadImageZip } from '../api/tenantApi';

function ImageZipUploadPanel() {
  const [imageFile, setImageFile] = useState(null);
  const [imageUploading, setImageUploading] = useState(false);
  const [imageUploadMessage, setImageUploadMessage] = useState('');
  const [imageUploadError, setImageUploadError] = useState('');
  const [isImageDragging, setIsImageDragging] = useState(false);
  const imageFileInputRef = useRef(null);

  const resetUploadMessage = () => {
    setImageUploadError('');
    setImageUploadMessage('');
  };

  const selectFile = (file) => {
    setImageFile(file);
    resetUploadMessage();
  };

  const handleImageUpload = async () => {
    if (!imageFile) {
      setImageUploadError('업로드할 ZIP 파일을 선택해 주세요.');
      return;
    }

    setImageUploading(true);
    resetUploadMessage();

    try {
      const result = await uploadImageZip(imageFile);
      setImageUploadMessage(result.message || 'ZIP 업로드 요청이 전송되었습니다.');
    } catch (err) {
      setImageUploadError(err.response?.data?.detail || 'ZIP 업로드에 실패했습니다.');
    } finally {
      setImageUploading(false);
    }
  };

  return (
    <div className="tab-content edi-upload-section">
      <h2>이미지 ZIP 업로드</h2>
      <p className="upload-hint">
        여권/영수증 이미지 ZIP 파일을 업로드하세요.
      </p>
      <div
        className={`edi-dropzone ${isImageDragging ? 'dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsImageDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsImageDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsImageDragging(false);
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            selectFile(e.dataTransfer.files[0]);
          }
        }}
        onClick={() => imageFileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={imageFileInputRef}
          className="file-input-hidden"
          accept=".zip"
          onChange={(e) => selectFile(e.target.files?.[0] || null)}
        />
        <p className="dropzone-text">
          이 영역을 클릭하거나 ZIP 파일을 드래그해서 업로드할 파일을 선택하세요.
        </p>
        <p className="dropzone-subtext">지원 형식: .zip</p>
      </div>
      {imageFile && (
        <div className="selected-file">
          선택한 파일: <strong>{imageFile.name}</strong>
        </div>
      )}
      <div className="upload-actions">
        <button
          className="upload-button"
          type="button"
          onClick={handleImageUpload}
          disabled={imageUploading}
        >
          {imageUploading ? '업로드 중...' : '업로드'}
        </button>
      </div>
      {imageUploadError && <div className="upload-error">{imageUploadError}</div>}
      {imageUploadMessage && !imageUploadError && (
        <div className="upload-success">{imageUploadMessage}</div>
      )}
    </div>
  );
}

export default ImageZipUploadPanel;
