import { useLocation, useNavigate } from 'react-router-dom';
import CommonTabsRow from '../components/CommonTabsRow';
import DashboardShell from '../components/DashboardShell';
import { DEFAULT_FEE_TAB, FEE_TABS } from '../constants/feeTabs';
import './FeePage.css';

function FeePage() {
  const navigate = useNavigate();
  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);
  const tabFromUrl = searchParams.get('tab');
  const activeTab = tabFromUrl || DEFAULT_FEE_TAB;

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
    <DashboardShell title="수수료" contentClassName="fee-content">
      <CommonTabsRow
        tabs={FEE_TABS.map((tab) => ({ key: tab.id, label: tab.label }))}
        activeKey={activeTab}
        onTabChange={(tab) => {
          navigate(`/dashboard/fee?tab=${tab}`);
        }}
      />

      <div className="common-card page-content">{renderTabContent()}</div>
    </DashboardShell>
  );
}

export default FeePage;

