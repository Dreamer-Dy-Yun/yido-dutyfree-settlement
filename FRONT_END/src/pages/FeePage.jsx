import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import SessionHeader from '../components/SessionHeader';
import CommonTabsRow from '../components/CommonTabsRow';
import { getCurrentUser, logout } from '../services/auth';
import { DEFAULT_FEE_TAB, FEE_TABS } from '../constants/feeTabs';
import './FeePage.css';

function FeePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null);

  const searchParams = new URLSearchParams(location.search);
  const tabFromUrl = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(tabFromUrl || DEFAULT_FEE_TAB);

  const isAdmin = currentUser?.role === 'admin';

  useEffect(() => {
    loadCurrentUser();
  }, []);

  useEffect(() => {
    const nextParams = new URLSearchParams(location.search);
    const nextTab = nextParams.get('tab') || DEFAULT_FEE_TAB;
    setActiveTab(nextTab);
  }, [location.search]);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to load current user:', err);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'settings':
        return (
          <div className="tab-content">
            <h2>수수료 설정</h2>
            <p>수수료 관련 기본 설정 화면(준비 중)</p>
          </div>
        );
      case 'rates':
        return (
          <div className="tab-content">
            <h2>수수료율</h2>
            <p>수수료율 관리 화면(준비 중)</p>
          </div>
        );
      case 'settlements':
        return (
          <div className="tab-content">
            <h2>정산</h2>
            <p>정산 내역/처리 화면(준비 중)</p>
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
    <div className="app-layout">
      <Sidebar isAdmin={isAdmin} />
      <div className="app-main">
        <SessionHeader
          title="수수료"
          currentUser={currentUser}
          onLogout={async () => {
            await logout();
          }}
          onProfileUpdated={loadCurrentUser}
        />

        <main className="app-content fee-content">
          <CommonTabsRow
            tabs={FEE_TABS.map((tab) => ({ key: tab.id, label: tab.label }))}
            activeKey={activeTab}
            onTabChange={(tab) => {
              setActiveTab(tab);
              navigate(`/dashboard/fee?tab=${tab}`);
            }}
          />

          <div className="common-card page-content">{renderTabContent()}</div>
        </main>
      </div>
    </div>
  );
}

export default FeePage;

