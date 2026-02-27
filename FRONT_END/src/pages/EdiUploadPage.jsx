import { useState, useEffect } from 'react';
import { getCurrentUser } from '../services/auth';
import Sidebar from '../components/Sidebar';
import './EdiUploadPage.css';

function EdiUploadPage() {
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    loadCurrentUser();
  }, []);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  };

  const isAdmin = currentUser?.role === 'admin';

  return (
    <div className="edi-upload-page">
      <Sidebar isAdmin={isAdmin} />
      <div className="page-header">
        <h1>EDI 데이터 업로드</h1>
      </div>
      <div className="page-content">
        <p>EDI 데이터 업로드 기능은 준비 중입니다.</p>
      </div>
    </div>
  );
}

export default EdiUploadPage;
