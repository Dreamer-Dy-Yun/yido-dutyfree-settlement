 # 데이터 매핑 - 이미지 확인 탭 설계서

> 목적: `데이터 매핑 > 이미지 확인` 탭에서 **영수증/여권 OCR 결과를 검수·수정**하는 화면과 대응 백엔드를 설계한다.

---

## 1. 요구사항 정리

### 1.1 탭 내 역할

- 위치: 테넌트 대시보드 → `데이터 매핑` 메뉴 → `이미지 확인(image-review)` 탭
- 역할: AI OCR 결과(영수증/여권)를 리스트로 보여주고, **이미지와 함께 필드를 검수/수정**하여 확정 저장

### 1.2 공통 제약

- 데이터는 테넌트 전용 스키마 사용 (기존 `router_tenant` 패턴 준수)
- 미확인 데이터: `OcrReceipt`, `OcrPassport`
  - `is_processed = False` 인 경우만 “작업 대상”으로 조회
  - 수정/확인 시 `is_processed = True` 로 변경
- 확정 데이터: `VerifiedReceipt`, `VerifiedPassport`
  - `is_verified = True` 인 경우 “작업 완료”로 간주
  - 최초 OCR 결과와 수정 값 비교 후 `is_corrected` 플래그 세팅
  - 수정/확인 시 `db_updated_by` 에 현재 유저 id 기록 (이미 BaseModel 컬럼 존재 가정)

---

## 2. 백엔드 API 설계 (FastAPI / `router_tenant.py`)

### 2.1 공통 유틸

- 인증: `get_current_tenant_admin` 사용
- 스키마: `schemas = [tenant_schema, "public"]` (기존 `_get_current_tenant_schemas` 재사용)
- 응답 JSON은 프론트 요구 필드 + 이미지/좌표 정보만 포함

### 2.2 영수증 리스트 API

#### 2.2.1 엔드포인트

```http
GET /api/tenant/data-mapping/receipts
```

#### 2.2.2 쿼리 파라미터

- `is_completed: bool = false`
  - `false` → `OcrReceipt` 기준, `is_processed = False`
  - `true` → `VerifiedReceipt` 기준, `is_verified = True`
- `skip: int = 0`, `limit: int = 50` (기본 페이지네이션)

#### 2.2.3 응답 스키마 (리스트용)

```jsonc
[
  {
    "id": 123,                 // 소스 테이블 PK
    "source": "ocr",           // "ocr" | "verified"
    "dutyfree_company": "롯데",
    "group_no": "G-001",
    "receipt_no": "R-12345",
    "country_code": "KOR",
    "passport_no": "M1234567*",
    "purchaser": "HONG*GILDONG", // 이름
    "is_completed": false,
    "image": {
      "hash_img": "....",
      "path": "/tenant-a/img/abcd1234.jpg",
      "coordinate": { "top": 10, "bottom": 200, "left": 50, "right": 400 }
    }
  }
]
```

- **리스트 표시 필드**
  - 면세점: `dutyfree_company`
  - 그룹: `group_no`
  - 영수증 번호: `receipt_no`
  - 작업 완료 여부: `is_completed` (배지 색상으로 표현)
- **수정 모달용 데이터**
  - `country_code`, `passport_no`, `purchaser` 등도 함께 포함 → 별도 상세 API 불필요

### 2.3 여권 리스트 API

#### 2.3.1 엔드포인트

```http
GET /api/tenant/data-mapping/passports
```

#### 2.3.2 쿼리 파라미터

- `is_completed: bool = false`
  - `false` → `OcrPassport.is_processed = False`
  - `true` → `VerifiedPassport.is_verified = True`

#### 2.3.3 응답 스키마

> 요구사항: “필요 정보 외에는 좌표만 프론트로 전달”

```jsonc
[
  {
    "id": 55,
    "source": "ocr",
    "country_code": "KOR",
    "passport_no": "M1234567",
    "name": "HONG GILDONG",
    "is_completed": false,
    "image": {
      "hash_img": "....",
      "path": "/tenant-a/img/abcd1234.jpg",
      "coordinate": { "top": 20, "bottom": 180, "left": 40, "right": 380 }
    }
  }
]
```

- **리스트 표시 필드**
  - 국적: `country_code`
  - 여권 번호: `passport_no`
  - 이름: `name`

### 2.4 영수증 수정/확인 API

#### 2.4.1 엔드포인트

```http
POST /api/tenant/data-mapping/receipts/verify
```

#### 2.4.2 요청 바디

```jsonc
{
  "source": "ocr",              // "ocr" | "verified"
  "id": 123,                    // source 기준 PK
  "dutyfree_company": "롯데",    // 드롭다운에서 선택된 값
  "group_no": "G-001",
  "receipt_no": "R-12345",
  "country_code": "KOR",
  "passport_no": "M1234567*",   // 9자리 이하, * 허용
  "purchaser": "HONG*GILDONG"   // 이름, * 허용
}
```

#### 2.4.3 처리 로직 개략

1. `source` 값에 따라 원본 로우 조회
   - `"ocr"` → `OcrReceipt` 에서 `id` 로 조회, OCR 원본 값 기준 비교
   - `"verified"` → `VerifiedReceipt` 에서 `id` 로 조회 (단순 구현, 최초 OCR 기준 비교는 추후 리팩토링 여지)
2. `VerifiedReceipt` upsert
   - composite key (예: `dutyfree_company`, `receipt_no` 등) 기준 upsert
   - `is_verified = True`
   - 기존 값과 비교하여 `is_corrected` 계산
   - `db_updated_by` 에 현재 유저 id 기록
3. `OcrReceipt.is_processed = True` 업데이트 (최초 처리 시에만)

### 2.5 여권 수정/확인 API

#### 2.5.1 엔드포인트

```http
POST /api/tenant/data-mapping/passports/verify
```

#### 2.5.2 요청 바디

```jsonc
{
  "source": "ocr",             // "ocr" | "verified"
  "id": 55,
  "country_code": "KOR",
  "passport_no": "M1234567",   // 9자리 이하
  "name": "HONG GILDONG"
}
```

#### 2.5.3 처리 로직 개략

- 2.4와 동일한 패턴으로 `OcrPassport` / `VerifiedPassport` 에 대해 처리
  - `OcrPassport.is_processed = True`
  - `VerifiedPassport.is_verified = True`, `is_corrected` 비교, `db_updated_by` 설정

---

## 3. 프론트엔드 설계 (React / `FRONT_END/src`)

### 3.1 탭 내 전체 구성

- 기존 `DataMappingPage.jsx` 의 `image-review` 탭을 다음 구조로 교체:
  1. 상단: “영수증 / 여권” 토글 (탭 또는 버튼 그룹)
  2. 중단: 선택된 타입(영수증/여권)에 따른 리스트 + “작업 완료 여부” 필터
  3. 오버레이: 공통 수정 모달 (`ImageVerifyModal`)

### 3.2 파일 구조 (제안)

```text
FRONT_END/src/data-mapping/
  ImageReviewPanel.jsx      // image-review 탭 전체 컨테이너
  ReceiptList.jsx           // 영수증 리스트 + 필터
  PassportList.jsx          // 여권 리스트 + 필터
  ImageVerifyModal.jsx      // 공통 수정 모달
  ImageViewer.jsx           // 이미지 + 좌표 하이라이트 + 줌/팬
  useImageViewer.js         // (선택) 이미지 뷰어용 커스텀 훅
```

- `DataMappingPage.jsx`
  - `image-review` case에서 `ImageReviewPanel` 을 렌더링

### 3.3 서비스 계층 (`services/tenant.js`)

- 기존 `uploadEdiFile`, `uploadImageZip`, `getImageOcrProgress` 패턴을 따른다.

```ts
// pseudo type
getReceiptList(params: { isCompleted?: boolean; skip?: number; limit?: number });
getPassportList(params: { isCompleted?: boolean; skip?: number; limit?: number });
verifyReceipt(payload: ReceiptVerifyPayload);
verifyPassport(payload: PassportVerifyPayload);
```

---

## 4. 수정 모달 설계 (`ImageVerifyModal`)

### 4.1 공통 레이아웃

- 좌측: `ImageViewer` 컴포넌트
  - 이미지 표시
  - 전달받은 좌표에 밝은 붉은색 테두리 표시
  - 이미지의 나머지 영역은 채도/밝기 낮추기 (약한 모아레 느낌)
  - 이미지 확대/축소, 드래그 이동 가능
- 우측: 폼 영역
  - 모드: `'receipt' | 'passport'`
  - 영수증 / 여권에 따라 입력 필드 다르게 렌더링
- 하단: 네비게이션 / 액션 버튼
  - `◀ 이전`, `▶ 다음`, `취소`, `수정`

### 4.2 입력 필드

#### 4.2.1 영수증 모드

- 면세점 종류 (드롭다운, 현재는 상수로 구현)
  - 값: `lotte`, `silla` (레이블은 한글)
  - 추후 테이블 기반으로 교체할 수 있게 상수 정의 분리
- 영수증 번호 (`receipt_no`)
- 국적 (`country_code`) – 읽기/수정 정책은 API 계약에 맞춤
- 여권 번호 (`passport_no`)
  - 표시: API 값 그대로
  - 수정 시: 최대 9자리, `*` 허용
- 이름 (`purchaser`)
  - 표시: API 값 그대로
  - 수정 시: `*` 허용

#### 4.2.2 여권 모드

- 국적 (`country_code`)
- 여권 번호 (`passport_no`) – 최대 9자리
- 이름 (`name`)

### 4.3 키보드 인터랙션

- 모달 활성화 시:
  - `Enter` → “수정” 버튼 클릭과 동일 동작
  - `Esc` → “취소” 버튼 클릭과 동일 동작
  - `←` → `◀` 버튼 클릭 (이전 항목)
  - `→` → `▶` 버튼 클릭 (다음 항목)
- “수정” 클릭 시:
  - 확인 다이얼로그(간단한 confirm 모달) 표시
    - `Enter` → 확인 (실제 API 호출)
    - `Esc` → 취소 (다이얼로그 닫기)

### 4.4 리스트 네비게이션 규칙

- 현재 필터(예: `is_completed = false`)를 적용한 리스트 배열을 상위 컨테이너가 보유
- 모달로 전달: `items`, `currentIndex`, `onChangeIndex`
- 버튼/키 입력 시:
  - 이전(`◀`): `index === 0` 이면 마지막 인덱스로 이동 (순환)
  - 다음(`▶`): 마지막 인덱스에서 다시 ▶ 누르면 `index = 0`
- 수정 성공 후:
  - 기본 동작: 현재 항목을 클라이언트 리스트에서 제거 (`setItems`), 동일 필터에 더 이상 나타나지 않게 함
  - 제거 후 자동으로 다음 항목으로 포커스 이동 (리스트 비면 모달 닫기)

---

## 5. 이미지 뷰어 설계 (`ImageViewer`)

### 5.1 입력 값

- `imageUrl: string` (백엔드에서 준 `path` 를 기반으로 구성)
- `coordinate: { top: number; bottom: number; left: number; right: number }` (원본 픽셀 기준)

### 5.2 렌더링 방법

- 컨테이너: `position: relative; overflow: hidden;`
- 실제 이미지:
  - CSS `transform: translate(x, y) scale(s)` 로 줌/팬
  - 최대/최소 배율 제한
- ROI(관심 영역) 표시:
  - `position: absolute` 박스 하나 생성
  - 이미지 실제 렌더 크기 대비 비율로 좌표 스케일링 후 위치/크기 계산
  - 스타일: `border: 2px solid rgba(255, 80, 80, 0.9); box-shadow` 등
- 주변 영역 채도/밝기 낮추기:
  - 전체 이미지 위에 반투명 어두운 마스크를 덮고,
  - ROI 영역만 투명하게 뚫린 형태로 구현 (CSS clip-path 또는 4개의 마스크 div)

### 5.3 인터랙션

- 마우스 휠: 줌 인/아웃 (center 기준 또는 마우스 포인터 근처 기준)
- 드래그: 마우스 왼쪽 버튼 드래그로 이미지 이동 (translateX/translateY 조정)
- 필요 시 모바일 터치 제스처는 후순위 (1차 구현 범위에서 제외 가능)

---

## 6. 단계별 구현 계획

### 6.1 1단계 – 백엔드 리스트 API

1. `router_tenant.py` 내 “데이터 매핑 / EDI 업로드” 섹션 아래에 다음 엔드포인트 추가
   - `GET /api/tenant/data-mapping/receipts`
   - `GET /api/tenant/data-mapping/passports`
2. 쿼리 파라미터(`is_completed`, `skip`, `limit`) 처리
3. 각 모델(`OcrReceipt`, `VerifiedReceipt`, `OcrPassport`, `VerifiedPassport`)에서 필요한 컬럼만 선택
4. `Image` 테이블과 조합해 `hash_img`, `path`, `coordinate` 포함

### 6.2 2단계 – 프론트 리스트 화면

1. `FRONT_END/src/data-mapping/ImageReviewPanel.jsx` 생성
   - 영수증/여권 토글
   - 현재 타입/필터 상태 관리
2. `ReceiptList.jsx`, `PassportList.jsx` 생성
   - 테이블/리스트 UI
   - “작업 완료 여부” 필터 (기본: 미완료)
   - 항목 클릭 시 `onSelect(item, index, list)` 호출

### 6.3 3단계 – 공통 수정 모달 + 이미지 뷰어

1. `ImageViewer.jsx` 구현
   - 이미지 표시 + 좌표 하이라이트 + 줌/팬
2. `ImageVerifyModal.jsx` 구현
   - 폼 + 버튼 + 키보드/네비게이션 + 확인 다이얼로그
   - `mode: 'receipt' | 'passport'` 에 따라 폼 분기

### 6.4 4단계 – 백엔드 수정/확인 API

1. `router_tenant.py` 에 다음 엔드포인트 추가
   - `POST /api/tenant/data-mapping/receipts/verify`
   - `POST /api/tenant/data-mapping/passports/verify`
2. OCR/Verified 테이블과의 upsert 로직 구현
3. `is_processed`, `is_verified`, `is_corrected`, `db_updated_by` 처리

### 6.5 5단계 – 프론트 수정 연동 및 UX 다듬기

1. 모달에서 수정 요청 → 백엔드 verify API 호출
2. 성공 시:
   - 현재 항목을 리스트에서 제거
   - 다음 항목으로 자동 이동 (없으면 모달 닫기)
3. 에러 메시지 / 로딩 상태 / 버튼 비활성화 등 UX 정리

---

## 7. 노트

- 면세점 종류 드롭다운은 현재 상수(`lotte`, `silla`)로 구현하고, 추후 별도 테이블/엔드포인트로 리팩토링 예정
- OCR 원본과 Verified 값 비교 방식은 1차 구현 시 단순 비교로 두고, 나중에 “최초 OCR 스냅샷” 저장 구조가 정해지면 개선 예정
- 전체 구현은 이 문서를 기준으로 단계별로 진행하며, 각 단계 이후 리팩토링 포인트를 다시 검토한다.

