import os

import pytest
from sqlalchemy import insert, select, text

from DATABASE import models
from PROCESSOR_MATCHING.matcher import PRM_Lotte
from PROCESSOR_MATCHING.run_match_worker import _create_db_manager


TEST_TENANT_SCHEMA_ENV = "TEST_TENANT_SCHEMA"
DEFAULT_TEST_TENANT_SCHEMA = "test_tenant_matching"
DEFAULT_PUBLIC_SCHEMA = "public"


def _get_schemas() -> tuple[str, str]:
    """
    테스트에서 사용할 테넌트/퍼블릭 스키마 이름을 반환.

    - 테넌트 스키마는 환경 변수 TEST_TENANT_SCHEMA 로 오버라이드 가능.
    - 기본값은 'test_tenant_matching' / 'public' 조합을 사용한다.
    """
    tenant_schema = os.getenv(TEST_TENANT_SCHEMA_ENV, DEFAULT_TEST_TENANT_SCHEMA)
    public_schema = os.getenv("PUBLIC_SCHEMA", DEFAULT_PUBLIC_SCHEMA)
    return tenant_schema, public_schema


async def _truncate_matching_tables(db) -> None:
    """
    테스트용 테넌트 스키마에서 매칭 관련 테이블만 정리.

    실제 스키마/테이블 존재 여부는 테스트 실행 환경에 따라 달라질 수 있으므로,
    필요시 스키마/마이그레이션은 외부에서 선행해 두어야 한다.
    """
    tenant_schema, public_schema = _get_schemas()
    schemas = [tenant_schema, public_schema]

    # TRUNCATE 순서는 FK 제약이나 CASCADE 여부에 따라 조정 가능
    for table in ("matched", "verified_receipt", "verified_passport"):
        stmt = text(f"TRUNCATE TABLE {tenant_schema}.{table} RESTART IDENTITY CASCADE")
        await db.execute_query(stmt, schemas=schemas)


async def _insert_verified_receipt(
    db,
    uuid_batch: str,
    uuid_record: str,
) -> None:
    """
    최소 필수 컬럼만 채운 VerifiedReceipt 한 건 삽입.
    """
    tenant_schema, public_schema = _get_schemas()
    schemas = [tenant_schema, public_schema]

    stmt = (
        insert(models.VerifiedReceipt)
        .values(
            dutyfree_company="LOTTE",
            group_no=None,
            receipt_no="R001",
            passport_no=None,
            name=None,
            rotation=None,
            coordinate=None,
            verifier_id=None,
            verifier_name=None,
            is_processed=False,
            locked_by=None,
            hash_img="TEST_HASH_RECEIPT",
            is_verified=True,
            is_corrected=True,
            uuid_batch=uuid_batch,
            uuid_record=uuid_record,
        )
    )
    await db.execute_query(stmt, schemas=schemas)


async def _insert_verified_passport(
    db,
    uuid_batch: str,
    uuid_record: str,
) -> None:
    """
    최소 필수 컬럼만 채운 VerifiedPassport 한 건 삽입.
    """
    tenant_schema, public_schema = _get_schemas()
    schemas = [tenant_schema, public_schema]

    stmt = (
        insert(models.VerifiedPassport)
        .values(
            country_code="KOR",
            passport_no="P00123456",
            name="TEST USER",
            gender=None,
            place_of_birth=None,
            date_of_birth=None,
            place_of_issue=None,
            date_of_issue=None,
            authority=None,
            date_of_expiry=None,
            verifier_id=None,
            verifier_name=None,
            is_processed=False,
            locked_by=None,
            hash_img="TEST_HASH_PASSPORT",
            rotation=None,
            coordinate=None,
            is_verified=True,
            is_corrected=True,
            uuid_batch=uuid_batch,
            uuid_record=uuid_record,
        )
    )
    await db.execute_query(stmt, schemas=schemas)


@pytest.mark.asyncio
async def test_matching_e2e_basic_success() -> None:
    """
    단일 영수증/여권 케이스에 대해:
    - 매처 실행 후 MATCHED 에 결과가 생성되고,
    - VerifiedReceipt 가 is_processed=True + locked_by=None 으로 업데이트되는지 검증.

    이 테스트는 실제 DB/스키마 상태에 의존하므로,
    - TEST_TENANT_SCHEMA 환경변수로 사용할 테넌트 스키마를 지정해 두고,
    - 해당 스키마에 테이블이 생성되어 있어야 한다.
    """
    db = _create_db_manager()
    tenant_schema, public_schema = _get_schemas()

    # 정리
    await _truncate_matching_tables(db)

    uuid_batch = "TEST_BATCH_001"
    uuid_receipt = "TEST_RECEIPT_001"
    uuid_passport = "TEST_PASSPORT_001"

    # GIVEN: 영수증 / 여권 한 건씩 준비
    await _insert_verified_receipt(db, uuid_batch=uuid_batch, uuid_record=uuid_receipt)
    await _insert_verified_passport(db, uuid_batch=uuid_batch, uuid_record=uuid_passport)

    # WHEN: 롯데 매처 실행
    matcher = PRM_Lotte(
        db=db,
        public_schema=public_schema,
        tenant_schema=tenant_schema,
    )
    locked_by = "test_worker:basic_success"
    await matcher.run(locked_by=locked_by, try_fallback=False)

    # THEN: MATCHED 테이블에 uuid_receipt 기준 결과가 생성되었는지 확인
    stmt_matched = select(models.MATCHED).where(models.MATCHED.uuid_receipt == uuid_receipt)
    result_matched = await db.execute_query(stmt_matched, schemas=[tenant_schema, public_schema])
    rows_matched = result_matched.mappings().all() if result_matched.mappings() else []

    assert len(rows_matched) == 1, "MATCHED 에 해당 영수증 UUID 행이 1건 존재해야 한다."

    # THEN: VerifiedReceipt 가 is_processed=True, locked_by=None 으로 변경되었는지 확인
    stmt_receipt = select(models.VerifiedReceipt).where(models.VerifiedReceipt.uuid_record == uuid_receipt)
    result_receipt = await db.execute_query(stmt_receipt, schemas=[tenant_schema, public_schema])
    rows_receipt = result_receipt.mappings().all() if result_receipt.mappings() else []

    assert len(rows_receipt) == 1, "VerifiedReceipt 에 해당 uuid_record 행이 1건 존재해야 한다."

    receipt = rows_receipt[0]
    assert receipt["is_processed"] is True, "매칭 후 VerifiedReceipt.is_processed 는 True 여야 한다."
    assert receipt["locked_by"] is None, "매칭 후 VerifiedReceipt.locked_by 는 None (언락 상태) 여야 한다."

