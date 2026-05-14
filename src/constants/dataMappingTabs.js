export const DEFAULT_DATA_MAPPING_TAB = 'edi-upload';

export const DATA_MAPPING_TABS = [
  { id: 'edi-upload', label: 'EDI 데이터 업로드', icon: '📤' },
  { id: 'image-upload', label: '이미지 업로드', icon: '🖼️' },
  { id: 'image-review', label: '이미지 확인', icon: '🧾' },
  { id: 'image-mapping', label: '이미지 매핑', icon: '🔗' },
  { id: 'data-check', label: '데이터 확인', icon: '🔍' },
];

export const getDataMappingTabPath = (tabId) => `/dashboard/data-mapping?tab=${tabId}`;
