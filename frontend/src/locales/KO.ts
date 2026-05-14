export const KO = {
  dataMapping: {
    imageMapping: {
      title: '이미지 매핑',
      statusLoadError: '매칭 상태를 불러오지 못했습니다.',
      listLoadError: '매칭 결과를 불러오지 못했습니다.',
      noUnmatchedData: '미매핑 데이터가 없습니다.',
      triggerFailed: '매칭 시도 요청에 실패했습니다.',
      detailLoadError: '매핑 상세 정보를 불러오지 못했습니다.',
      filters: {
        all: '전체',
        matched: '매핑됨',
        unmatched: '미매핑',
      },
      table: {
        dutyfreeCompany: '면세점',
        receiptNo: '영수증 번호',
        purchaserName: '이름',
        actions: '동작',
        loading: '로딩 중...',
        empty: '표시할 데이터가 없습니다.',
        viewDetail: '상세 보기',
      },
      pagination: {
        previous: '이전',
        page: '페이지',
        next: '다음',
      },
      status: {
        unmatchedMessage: (count: number) => `확인되었으나 미매핑된 데이터 ${count}건이 있습니다.`,
        runningButton: '매칭 시도 중...',
        idleButton: '매칭 시도',
        runningHelp: '매칭 작업이 진행 중입니다. 완료되면 목록이 자동으로 새로고침됩니다.',
      },
    },
    imageViewer: {
      altText: '원본 이미지',
      help: 'Alt+드래그: 영역 재지정 / 드래그: 화면 이동',
      empty: '이미지 경로가 없습니다.',
    },
  },
} as const;
