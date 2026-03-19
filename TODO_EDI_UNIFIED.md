## EDI / EDI_UNIFIED TODO

- [ ] PGDBManager 세션 초기화 시 PostgreSQL 타임아웃 설정 추가 (작성자: Yun Daeyoung)
  - `lock_timeout` 예: `SET lock_timeout = '5s'`
  - `statement_timeout` 예: `SET statement_timeout = '30s'`
  - 적용 위치 후보:
    - `PGDBManager.open_session()` 내부에서 세션마다 한 번 설정
    - 또는 EDI/매칭 등 고비용 서비스에서만 선택적으로 설정
  - 실제 운영 환경에서 데드락/슬로쿼리 패턴 확인 후 구체 값 조정

---

## VerifiedReceipt / VerifiedPassport 머지/삭제 전략 메모

### 1. 변경 사유 (이전 안 vs 현재 안)

- **이전 안 (폐기됨)**  
  - `VerifiedReceipt`, `VerifiedPassport` 에 `is_deleted` 플래그를 추가해서 **논리 삭제(soft delete)** 로 과거 버전을 보존하려 했음.
  - 유니크 제약은 그대로 두고(`uuid_record` + 복합 유니크),  
    덮어쓰기/머지 시에는:
    - 기존 row `is_deleted = true`
    - 새 row `is_deleted = false`
    - FK(`MATCHED`, `EDI_UNIFIED`) 는 새 uuid를 가리키도록 변경하는 방향.
- **문제점**
  - 유니크 제약이 `is_deleted`를 포함하지 않아, 삭제된 행과 활성 행이 **같은 유니크 키**를 가질 때 충돌.
  - partial unique index(`WHERE is_deleted = false`)로 바꿔도,
    - 한 배치 DataFrame 안에 **같은 유니크 키를 가진 행이 여러 개** 있으면
      `ON CONFLICT DO UPDATE` 한 명령 안에서 같은 행을 두 번 수정하려고 해서 `CardinalityViolationError` 발생.
  - FK 머지(기존 uuid를 새 uuid로 갈아타기)까지 고려하면, soft delete 기반 설계가 과도하게 복잡해짐.
- **현재 결정**
  - `is_deleted` 플래그는 제거.
  - 본 테이블(`VerifiedReceipt`, `VerifiedPassport`)은 항상 **현재 활성 레코드 한 건만** 유지하는 구조로 단순화.
  - 과거 버전/삭제 이력은 필요 시 **별도 아카이브 테이블**로 분리해서 보관하는 방향으로 확장.

### 2. 현안: 기존 내용 삭제 + FK 재배선 머지

- 목표:
  - 유니크 제약(복합 키 또는 `uuid_record`)이 충돌할 때,
  - **기존 레코드를 삭제(or 아카이브로 이동)하고 새 레코드를 살리면서**,  
    `MATCHED`, `EDI_UNIFIED` 등에서 기존 uuid를 참조하던 FK를 **모두 새 uuid로 변경**하는 머지 플로우를 구현한다.

- 개략 플로우 (머지 예시, VerifiedReceipt 기준):
  1. 충돌 탐지:
     - 같은 `uuid_record` 또는 같은 복합 키(`dutyfree_company`, `receipt_no`, ...) 를 가진 기존 row(`old_uuid`)가 이미 있음.
  2. 머지 선택(프론트에서 “덮어쓰기” 승인):
     - 트랜잭션 시작.
     - FK 재배선:
       - `MATCHED.uuid_receipt`, `EDI_UNIFIED.uuid_receipt` 에서 `old_uuid → new_uuid` 로 업데이트.
     - 기존 row 정리:
       - 현재 안: 본 테이블에서 `DELETE` (또는 나중에 아카이브 테이블에 INSERT 후 DELETE).
     - 트랜잭션 커밋.

- 주의점:
  - 한 번의 `upsert_batch`/`INSERT ... ON CONFLICT DO UPDATE` 안에  
    **같은 유니크 키가 여러 번 등장하지 않도록**, DataFrame 단계에서 유니크 키 기준으로 `drop_duplicates(subset=key_cols, keep="last")` 필요.
  - FK 재배선/머지는 별도 도메인 서비스로 분리해서 구현할 것  
    (예: `merge_verified_receipt(old_uuid, new_uuid)`, `merge_verified_passport(old_uuid, new_uuid)`).

### 3. 향후 확장: 아카이브 테이블 도입 (히스토리 필요 시)

- soft delete 대신, 삭제/머지 시점에 **별도 아카이브 테이블**로 과거 버전을 옮겨 두는 설계:
  - 예: `verified_receipt_archive`, `verified_passport_archive`.
  - 구조:
    - 본 테이블과 거의 동일한 스키마에,  
      추가 메타데이터 컬럼(삭제 시각, 삭제 사유, 머지 대상 uuid 등)만 추가.
  - 동작:
    1. 머지/삭제 직전, 기존 레코드 전체를 아카이브 테이블에 `INSERT`.
    2. 본 테이블에서는 `DELETE` (또는 머지 후 덮어쓰기).
    3. FK는 항상 본 테이블의 **현재 uuid_record** 만 가리키도록 유지.
- 장점:
  - 본 테이블은 “현재 상태”만 유지 → 유니크/ON CONFLICT/매칭/조회 로직 단순.
  - 과거 이력/검수 변경 흐름은 필요할 때만 아카이브에서 조회 가능.
