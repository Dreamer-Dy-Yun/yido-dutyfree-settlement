# 이미지 검수 모달 – 확인/미확인 리스트 카드 UI

> 이미지 해시 기준으로 불러온 **확인된 리스트**와 **미확인 리스트**를 카드로 표시할 때의 아이콘·스타일 규칙.

---

## 1. 적용 위치

- **컴포넌트**: `ImageVerifyModal` 우측 패널
- **위치**: 입력 폼(영수증/여권 필드) **아래**
- **역할**: 해당 이미지(`hash_img`)에 연결된 영수증·여권 항목을 카드 리스트로 표시. 카드 클릭 시 해당 항목 수정 폼으로 전환.

---

## 2. 리스트 구분

| 구분 | 데이터 소스 | 설명 |
|------|-------------|------|
| **확인된 리스트** | `VerifiedReceipt` / `VerifiedPassport` | 이미 검수 완료된 항목 (`is_verified = True` 등) |
| **미확인 리스트** | `OcrReceipt` / `OcrPassport` | 아직 검수하지 않은 OCR 결과 (`is_processed = False` 등) |

- 조회: 동일 이미지 해시(`hash_img`)로 두 소스 모두 조회 후, 확인/미확인으로 구분해 표시.

---

## 3. 카드별 아이콘·배경

### 3.1 확인된 리스트 (Verified)

- **배경색**: 초록색  
  - 예: `#22c55e`, `#16a34a` 등 (프로젝트 팔레트에 맞게 선택)
- **아이콘**: 하얀색 체크(✓)  
  - 배경 위에 흰색 체크 아이콘 표시
- **의미**: 검수 완료된 항목임을 한눈에 구분

**구현 예시 (클래스/스타일)**

- 카드 루트: `image-verify-card image-verify-card-verified`
- 배경: `background: #22c55e` (또는 `--color-verified-bg`)
- 아이콘: SVG 또는 아이콘 폰트로 `color: #fff` 체크 마크, 카드 좌측 또는 레이블 옆에 배치

---

### 3.2 미확인 리스트 (Unverified / OCR)

- **배경색**: **주황색 계열**  
  - 예: `#fb923c`(기본), 상황에 따라 `#f97316` 등
- **아이콘**: 확인됨과 구분되는 아이콘  
  - 후보 1: **시계/대기** 아이콘 (미확인·대기 중)
  - 후보 2: **빈 원(○)** 또는 **원형 테두리** (미완료)
  - 후보 3: **연필/편집** 아이콘 (수정 대기)
- **색**: 배경과 대비되게 짙은 주황/갈색 계열  
  - 예: `#7c2d12`, `#9a3412`

**권장**

- 배경: 주황색 `#fb923c`
- 아이콘: 시계(clock) 또는 원형 대기 아이콘, 색상 `#7c2d12`
- **클래스**: `image-verify-card image-verify-card-unverified`

---

## 4. 카드 공통 사양 (요약)

- **형태**: 가로로 긴 카드 (한 줄에 레이블·아이콘·주요 식별자)
- **영수증 카드**: 영수증 번호(`receipt_no`)를 주로 표시
- **여권 카드**: 여권 번호(`passport_no`)를 주로 표시
- **레이아웃**: [아이콘] [타입(영수증/여권)] [번호 등] 한 줄 정렬
- **스크롤**: 카드 영역이 세로로 길어지면 해당 영역만 스크롤 (`overflow-y: auto`)

---

## 5. 구현 시 참고 (클래스·구조)

```html
<!-- 확인된 항목 카드 -->
<div class="image-verify-card image-verify-card-verified">
  <span class="image-verify-card-icon" aria-hidden="true"><!-- 흰색 체크 SVG --></span>
  <span class="image-verify-card-type">영수증</span>
  <span class="image-verify-card-id">R-12345</span>
</div>

<!-- 미확인 항목 카드 -->
<div class="image-verify-card image-verify-card-unverified">
  <span class="image-verify-card-icon" aria-hidden="true"><!-- 시계 또는 원형 아이콘 --></span>
  <span class="image-verify-card-type">여권</span>
  <span class="image-verify-card-id">M12345678</span>
</div>
```

- **CSS**
  - `.image-verify-card-verified`: 초록 배경 + 흰색 체크
  - `.image-verify-card-unverified`: 연한 회색(또는 앰버) 배경 + 회색/앰버 계열 대기 아이콘

---

## 6. 정리

| 리스트 | 배경 | 아이콘 |
|--------|------|--------|
| **확인됨** | 초록색 | 하얀색 체크(✓) |
| **미확인** | 주황색 | 시계/대기 또는 빈 원, 짙은 주황/갈색 |

이 스펙대로 적용하면 확인/미확인을 시각적으로 구분할 수 있다.
