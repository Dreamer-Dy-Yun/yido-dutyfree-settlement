# DB 트랜잭션/세션 리스크 점검 체크리스트

## 목적
- 현재 `PGDBManager`의 메서드 단위 세션/커밋 구조에서 발생 가능한 원자성 리스크를 정리한다.
- 실제 코드 위치를 기준으로 수정 우선순위를 정하고, 하나씩 개선한다.

## 현재 전제
- `PGDBManager.execute_query()`는 호출마다 세션을 열고 `commit()` 한다.
- `PGDBManager.upsert_dataframe()`, `update_dataframe()`도 각 호출마다 독립 커밋한다.
- 따라서 한 API에서 DB write를 여러 번 수행하면 "중간까지 반영" 상태가 남을 수 있다.

---

## A. 우선 대응 (High)

### 1) 테넌트 승인 플로우 (원자성 핵심 구간)
- 파일: `WEB_SERVER/routers/router_system_admin.py`
- 함수: `approve_tenant()`
- 현재 흐름:
  1. 스키마 생성
  2. 테이블 생성
  3. 관리자 계정 upsert
  4. `tenant.is_db_built = True`
  5. 승인 메일 발송
  6. `tenant.is_active = True`
- 리스크:
  - 중간 실패 시 일부 단계만 반영될 수 있음 (예: 계정 생성됨 + 활성화 미완료).
  - 메일 발송 실패가 DB 상태와 섞여 처리되면 재시도/복구가 어려움.
- 개선 방향:
  - DB 변경 단계(1~4,6)를 하나의 트랜잭션 단위로 묶고,
  - 메일 발송은 트랜잭션 밖으로 분리(실패 시 재시도 가능 구조).

체크박스:
- [ ] DB 변경 단계 트랜잭션 경계 재설계
- [ ] 메일 발송 분리 및 실패 처리 정책 정리
- [ ] 실패 복구 시나리오(재시도/보상) 문서화

---

## B. 2차 대응 (Medium)

### 2) OCR 이미지 처리 파이프라인
- 파일: `WEB_SERVER/services/service_image_ocr.py`
- 함수: `run()`, `set_image_processing()`, `set_image_processed()`, `upsert_ocr_receipt()`, `upsert_ocr_passport()`, `insert_llm_usage()`
- 현재 흐름(이미지 1건 기준):
  - OCR 결과 upsert(영수증/여권) -> LLM usage insert -> 이미지 상태 업데이트
- 리스크:
  - 각 단계가 독립 커밋이라 일부만 반영될 수 있음.
  - 예: OCR row 저장 성공 후 usage 저장 실패, 또는 processed flag만 누락.
- 개선 방향:
  - "이미지 1건 처리 단위"를 하나의 트랜잭션으로 묶는 구조 검토.
  - 최소한 상태 플래그 업데이트와 결과 저장의 일관성 보장.

체크박스:
- [ ] 1건 처리 단위 트랜잭션 적용 가능성 검토
- [ ] 실패 시 상태 복구 규칙(`is_processing`, `is_processed`) 명확화
- [ ] 중복 실행/재처리 시 idempotency 점검

---

## C. 점진 개선 (Medium/Low)

### 3) Read-Check-Write 경쟁 구간
- 파일: `WEB_SERVER/routers/router_system_admin.py`
- 대상 함수:
  - `create_llm_api_key()`
  - `update_llm_api_key()`
  - `create_prompt()`
  - `update_prompt()`
- 리스크:
  - 중복 검사(select) 후 insert/update가 분리되어 동시 요청에서 경합 가능.
- 개선 방향:
  - DB 유니크 제약을 최종 안전장치로 사용.
  - 필요 시 단일 쿼리/트랜잭션으로 충돌 처리(`ON CONFLICT`, 예외 매핑).

체크박스:
- [ ] 테이블 유니크 제약 재확인
- [ ] 충돌 발생 시 API 에러 매핑 통일
- [ ] 중복 체크+쓰기 로직 단순화

---

## D. 운영 관점 점검

### 4) 커넥션 풀/동시성
- 기본 설정: `pool_size=50`, `max_overflow=150` (최대 200 연결/인스턴스)
- 리스크:
  - 멀티 워커 환경에서 총 연결 수가 DB `max_connections`를 쉽게 초과할 수 있음.
- 개선 방향:
  - 배포 워커 수 기준으로 총 연결 수 산정.
  - timeout/대기 전략 점검.

체크박스:
- [ ] 인스턴스/워커 수 기준 전체 연결 상한 계산
- [ ] DB 서버 `max_connections`와 정합성 확인
- [ ] 풀 파라미터 운영값 확정

---

## 구현 순서 제안
1. `approve_tenant()` 트랜잭션 경계 확정
2. OCR 1건 처리 단위 트랜잭션 모델 확정
3. API key/prompt read-check-write 경쟁 완화
4. 운영 환경 풀 파라미터 튜닝

## 메모
- 현재 구조는 조회 API가 대부분이라 즉시 치명도는 낮지만,
- 승인/처리 파이프라인 같은 write-heavy 경로는 우선순위 높게 관리해야 한다.
