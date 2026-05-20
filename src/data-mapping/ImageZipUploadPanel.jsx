import { uploadImageZip } from '../api/data-mapping/uploadApi';
import FileUploadPanel from './upload/FileUploadPanel';

function ImageZipUploadPanel() {
  return (
    <FileUploadPanel
      title="이미지 ZIP 업로드"
      hint="여권/영수증 이미지 ZIP 파일을 업로드하세요."
      accept=".zip"
      emptyFileMessage="업로드할 ZIP 파일을 선택해 주세요."
      defaultSuccessMessage="ZIP 업로드 요청이 전송되었습니다."
      uploadFailedMessage="ZIP 업로드에 실패했습니다."
      uploadFile={uploadImageZip}
      dropzoneText="이 영역을 클릭하거나 ZIP 파일을 드래그해서 업로드할 파일을 선택하세요."
      dropzoneSubtext="지원 형식: .zip"
    />
  );
}

export default ImageZipUploadPanel;
