import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Sidebar.css';
import { DATA_MAPPING_TABS, getDataMappingTabPath } from '../constants/dataMappingTabs';
import { FEE_TABS, getFeeTabPath } from '../constants/feeTabs';

function Sidebar({ isAdmin, variant = 'tenant' }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState(
    variant === 'system-admin'
      ? ['admin-tenant', 'admin-service-account', 'admin-api-key', 'admin-prompt']
      : ['tenant', 'data-mapping']
  );

  const tenantMenuItems = [
    {
      id: 'tenant',
      label: '테넌트 관리',
      icon: '🏢',
      visible: isAdmin,
      children: [
        {
          id: 'users',
          label: '유저 관리',
          path: '/dashboard',
          icon: '👥',
        },
        {
          id: 'usage',
          label: '사용량 조회',
          path: '/dashboard?tab=usage',
          icon: '📊',
        },
      ],
    },
    {
      id: 'data-mapping',
      label: '데이터 매핑',
      icon: '📋',
      visible: true,
      children: DATA_MAPPING_TABS.map((tab) => ({
        id: tab.id,
        label: tab.label,
        path: getDataMappingTabPath(tab.id),
        icon: tab.icon,
      })),
    },
    {
      id: 'fee',
      label: '수수료',
      icon: '💰',
      visible: true,
      children: FEE_TABS.map((tab) => ({
        id: tab.id,
        label: tab.label,
        path: getFeeTabPath(tab.id),
        icon: tab.icon,
      })),
    },
  ];
  const systemAdminMenuItems = [
    {
      id: 'admin-dashboard',
      label: '대시보드',
      icon: '🏠',
      visible: true,
      path: '/admin',
    },
    {
      id: 'admin-tenant',
      label: '테넌트 관리',
      icon: '🏢',
      visible: true,
      children: [
        {
          id: 'admin-tenant-all',
          label: '전체',
          path: '/admin/tenants',
          icon: '📋',
        },
        {
          id: 'admin-tenant-active',
          label: '활성',
          path: '/admin/tenants?is_active=true',
          icon: '✅',
        },
        {
          id: 'admin-tenant-pending',
          label: '승인 대기',
          path: '/admin/tenants/pending',
          icon: '⏳',
        },
        {
          id: 'admin-tenant-inactive',
          label: '비활성',
          path: '/admin/tenants?is_active=false',
          icon: '⛔',
        },
      ],
    },
    {
      id: 'admin-service-account',
      label: '서비스 어카운트 관리',
      icon: '👤',
      visible: true,
      children: [
        {
          id: 'admin-service-account-all',
          label: '전체',
          path: '/admin/service-accounts',
          icon: '📋',
        },
        {
          id: 'admin-service-account-active',
          label: '활성',
          path: '/admin/service-accounts?is_active=true',
          icon: '✅',
        },
        {
          id: 'admin-service-account-inactive',
          label: '비활성',
          path: '/admin/service-accounts?is_active=false',
          icon: '⛔',
        },
      ],
    },
    {
      id: 'admin-api-key',
      label: 'API KEY 관리',
      icon: '🔐',
      visible: true,
      children: [
        {
          id: 'admin-api-key-all',
          label: '전체',
          path: '/admin/llm-api-keys',
          icon: '📋',
        },
        {
          id: 'admin-api-key-active',
          label: '활성',
          path: '/admin/llm-api-keys?is_active=true',
          icon: '✅',
        },
        {
          id: 'admin-api-key-inactive',
          label: '비활성',
          path: '/admin/llm-api-keys?is_active=false',
          icon: '⛔',
        },
      ],
    },
    {
      id: 'admin-prompt',
      label: '프롬프트 관리',
      icon: '🧠',
      visible: true,
      children: [
        {
          id: 'admin-prompt-all',
          label: '전체',
          path: '/admin/prompts',
          icon: '📋',
        },
        {
          id: 'admin-prompt-active',
          label: '활성',
          path: '/admin/prompts?is_active=true',
          icon: '✅',
        },
        {
          id: 'admin-prompt-inactive',
          label: '비활성',
          path: '/admin/prompts?is_active=false',
          icon: '⛔',
        },
      ],
    },
  ];
  const menuItems = variant === 'system-admin' ? systemAdminMenuItems : tenantMenuItems;

  const handleMenuClick = (item) => {
    if (item.children) {
      // 하위 메뉴가 있는 경우 펼치기/접기
      setExpandedMenus((prev) =>
        prev.includes(item.id)
          ? prev.filter((id) => id !== item.id)
          : [...prev, item.id]
      );
    } else if (item.path) {
      // 하위 메뉴가 없는 경우 페이지 이동
      if (item.path.includes('?tab=')) {
        const [path, tab] = item.path.split('?tab=');
        navigate(`${path}?tab=${tab}`);
      } else {
        navigate(item.path);
      }
    }
  };

  const handleSubMenuClick = (e, childItem) => {
    e.stopPropagation();
    if (childItem.path.includes('?tab=')) {
      const [path, tab] = childItem.path.split('?tab=');
      navigate(`${path}?tab=${tab}`);
    } else {
      navigate(childItem.path);
    }
  };

  const isActive = (item) => {
    if (!item.path) return false;
    if (item.path.includes('?')) {
      const [path, queryString] = item.path.split('?');
      if (location.pathname !== path) return false;

      const currentParams = new URLSearchParams(location.search);
      const targetParams = new URLSearchParams(queryString);

      for (const [key, value] of targetParams.entries()) {
        if (currentParams.get(key) !== value) {
          return false;
        }
      }
      return true;
    }
    if (item.path === '/admin') {
      return location.pathname === '/admin' && location.search === '';
    }
    if (item.path.startsWith('/admin/')) {
      return location.pathname === item.path && location.search === '';
    }
    if (item.path === '/dashboard') {
      return location.pathname === '/dashboard' && !location.search.includes('tab=usage');
    }
    return location.pathname === item.path;
  };

  const isChildActive = (childItem) => {
    return isActive(childItem);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <button
        className="sidebar-toggle"
        onClick={() => setIsCollapsed(!isCollapsed)}
        aria-label={isCollapsed ? '메뉴 펼치기' : '메뉴 접기'}
      >
        {isCollapsed ? '▶' : '◀'}
      </button>
      <nav className="sidebar-nav">
        {menuItems
          .filter((item) => item.visible)
          .map((item) => (
            <div key={item.id} className="sidebar-menu-group">
              <button
                className={`sidebar-item ${item.children ? 'has-children' : ''} ${
                  item.children && expandedMenus.includes(item.id) ? 'expanded' : ''
                } ${!item.children && isActive(item) ? 'active' : ''}`}
                onClick={() => handleMenuClick(item)}
                disabled={!item.visible}
              >
                <span className="sidebar-icon">{item.icon}</span>
                {!isCollapsed && (
                  <>
                    <span className="sidebar-label">{item.label}</span>
                    {item.children && (
                      <span className="sidebar-arrow">
                        {expandedMenus.includes(item.id) ? '▼' : '▶'}
                      </span>
                    )}
                  </>
                )}
              </button>
              {item.children && !isCollapsed && expandedMenus.includes(item.id) && (
                <div className="sidebar-submenu">
                  {item.children.map((child) => (
                    <button
                      key={child.id}
                      className={`sidebar-submenu-item ${isChildActive(child) ? 'active' : ''}`}
                      onClick={(e) => handleSubMenuClick(e, child)}
                    >
                      <span className="sidebar-icon">{child.icon}</span>
                      <span className="sidebar-label">{child.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
      </nav>
    </div>
  );
}

export default Sidebar;