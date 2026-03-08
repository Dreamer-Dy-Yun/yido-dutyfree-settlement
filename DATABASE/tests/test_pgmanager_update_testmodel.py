"""
TestModel updater 통합 테스트.

목적:
- DB에 이미 존재하는 유니크 키(a)를 가진 레코드가 있을 때,
- nullable=False 컬럼(b)을 입력하지 않고 update_batch()를 수행해도
  정상 업데이트되는지 검증.
"""

from __future__ import annotations

import pandas as pd
import pytest

from DATABASE.models import BaseModel
from DATABASE.models.public_model import TestModel as DBTestModel
from DATABASE.dbms.postgre.pg_manager import DataBaseMaker, PGDBManager


# 개발용 로컬 DB 기준
DB_NAME = "dev"
DB_USER = "admin"
DB_PASSWORD = "123!@#qwe"
DB_HOST = "localhost"
DB_PORT = 5432


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database() -> None:
    """테스트 DB 존재 보장."""
    maker = DataBaseMaker(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    ok = maker.run()
    assert ok, "테스트용 DB 생성/확인 실패"


@pytest.fixture(scope="function")
def pg_manager(ensure_test_database) -> PGDBManager:
    """테스트용 PGDBManager 생성."""
    return PGDBManager(
        base_model=BaseModel,
        db_name=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        pool_size=2,
        max_overflow=2,
    )


@pytest.mark.asyncio
async def test_update_without_non_nullable_column(pg_manager: PGDBManager) -> None:
    """
    시나리오:
    - 기존 데이터: a,b,c 모두 존재
    - 업데이트 데이터: a,c만 전달 (b 생략)
    기대:
    - a 기준으로 UPDATE 1건 수행
    - b는 기존값 유지
    - c는 새 값으로 변경
    """
    await pg_manager.create_tables(schema="public")

    unique_a = "UPDATE-TEST-A-001"
    initial_b = "B-INITIAL"
    initial_c = "C-INITIAL"
    updated_c = "C-UPDATED"

    await pg_manager.execute_query(
        "DELETE FROM public.test_model WHERE a = :a",
        {"a": unique_a},
    )

    # 선행 데이터 세팅 (insert)
    df_seed = pd.DataFrame(
        [
            {
                "a": unique_a,
                "b": initial_b,
                "c": initial_c,
            }
        ]
    )
    inserted = await pg_manager._upsert_dataframe(DBTestModel, df_seed)
    assert inserted == 1

    # non-nullable(b) 제외하고 UPDATE
    df_update = pd.DataFrame(
        [
            {
                "a": unique_a,   # key
                "c": updated_c,  # update target
                # b intentionally omitted (nullable=False)
            }
        ]
    )
    update_result = await pg_manager.update_batch(
        table=DBTestModel,
        data=df_update,
        conflict_cols=["a"],
    )
    assert int(update_result["cnt_success_rows"]) == 1

    # 결과 검증
    result = await pg_manager.execute_query(
        "SELECT a, b, c FROM public.test_model WHERE a = :a",
        {"a": unique_a},
    )
    row = result.fetchone()

    assert row is not None
    assert row.a == unique_a
    assert row.b == initial_b
    assert row.c == updated_c

    await pg_manager.execute_query(
        "DELETE FROM public.test_model WHERE a = :a",
        {"a": unique_a},
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
