import { useState } from 'react';
import { uploadEdiFile } from '../api/data-mapping/uploadApi';
import FileUploadPanel from './upload/FileUploadPanel';

const EDI_SOURCES = [
  { value: 'lotte', label: 'Lotte' },
  { value: 'silla', label: 'Silla' },
];

function formatEdiUploadMessage(result) {
  const message = result?.message || 'EDI 파일 업로드가 완료되었습니다.';
  const rows = result?.rows_upserted != null ? ` (${result.rows_upserted}건 반영)` : '';
  return message + rows;
}

function EdiUploadPanel() {
  const [ediSource, setEdiSource] = useState('lotte');

  return (
    <FileUploadPanel
      title="EDI 업로드"
      hint="면세점을 선택한 뒤 해당 형식의 EDI 엑셀 파일을 업로드하세요."
      accept=".xlsx,.xls"
      emptyFileMessage="업로드할 EDI 파일을 선택해 주세요."
      defaultSuccessMessage="EDI 파일 업로드가 완료되었습니다."
      uploadFailedMessage="EDI 파일 업로드에 실패했습니다."
      uploadFile={(file) => uploadEdiFile(file, ediSource)}
      getSuccessMessage={formatEdiUploadMessage}
      dropzoneSubtext="지원 형식: .xlsx, .xls"
    >
      <div className="upload-control-row">
        <label htmlFor="edi-source">면세점</label>
        <select
          id="edi-source"
          value={ediSource}
          onChange={(event) => setEdiSource(event.target.value)}
          className="upload-control-select"
        >
          {EDI_SOURCES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </FileUploadPanel>
  );
}

export default EdiUploadPanel;
