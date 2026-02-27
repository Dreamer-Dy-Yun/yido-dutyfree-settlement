import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Sidebar.css';

function Sidebar({ isAdmin }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState(['tenant', 'data-mapping']); // 기본적으로 테넌트 관리와 데이터 매핑 펼침

  const menuItems = [
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
      children: [
        {
          id: 'edi-upload',
          label: 'EDI 데이터 업로드',
          path: '/dashboard/data-mapping?tab=edi-upload',
          icon: '📤',
        },
        {
          id: 'image-upload',
          label: '이미지 업로드',
          path: '/dashboard/data-mapping?tab=image-upload',
          icon: '🖼️',
        },
        {
          id: 'data-check',
          label: '데이터 확인',
          path: '/dashboard/data-mapping?tab=data-check',
          icon: '🔍',
        },
        {
          id: 'fee-info',
          label: '수수료 정보',
          path: '/dashboard/data-mapping?tab=fee-info',
          icon: '💰',
        },
      ],
    },
  ];

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
    if (item.path === '/dashboard') {
      return location.pathname === '/dashboard' && !location.search.includes('tab=usage');
    }
    if (item.path.includes('?tab=')) {
      const [path, tab] = item.path.split('?tab=');
      if (path === '/dashboard') {
        return location.pathname === '/dashboard' && location.search.includes(`tab=${tab}`);
      }
      if (path === '/dashboard/data-mapping') {
        return location.pathname === '/dashboard/data-mapping' && location.search.includes(`tab=${tab}`);
      }
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