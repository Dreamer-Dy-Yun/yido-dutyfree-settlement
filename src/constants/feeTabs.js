export const DEFAULT_FEE_TAB = 'settings';

export const FEE_TABS = [
  { id: 'settings', label: '수수료 설정', icon: '⚙️' },
  { id: 'rates', label: '수수료율', icon: '📈' },
  { id: 'settlements', label: '정산', icon: '🧾' },
];

export const getFeeTabPath = (tabId) => `/dashboard/fee?tab=${tabId}`;

