from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.elements import Executable

from DATABASE.dbms.postgre.pg_database import DataBaseMaker
from DATABASE.dbms.postgre.pg_identifiers import quote_identifier, quote_search_path
from DATABASE.dbms.postgre.pg_manager import PGDBManager


class HardeningBase(DeclarativeBase):
    pass


class PublicSameName(HardeningBase):
    __tablename__ = "same_name"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_code: Mapped[str] = mapped_column(String(20), unique=True)


class TenantSameName(HardeningBase):
    __tablename__ = "same_name"
    __table_args__ = {"schema": "tenant_a"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_code: Mapped[str] = mapped_column(String(20), unique=True)


class DateModel(HardeningBase):
    __tablename__ = "date_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[object] = mapped_column(DateTime)


def make_manager() -> PGDBManager:
    mgr = PGDBManager.__new__(PGDBManager)
    mgr.base_model = HardeningBase
    mgr.unique_constraints = {}
    mgr.primary_constraints = {}
    mgr.foreign_key_constraints = {}
    mgr.nullable_columns = {}
    mgr.not_null_columns = {}
    mgr.unique_keys = {}
    mgr.primary_keys = {}
    mgr._get_uniqueness(HardeningBase)
    return mgr


def test_identifier_helpers_quote_unsafe_names() -> None:
    assert quote_identifier("tenant_1") == "tenant_1"
    assert quote_identifier("Foo Bar") == '"Foo Bar"'
    assert quote_identifier('x"; DROP SCHEMA public;--') == '"x""; DROP SCHEMA public;--"'
    assert quote_search_path(["tenant_1", "public"]) == "tenant_1, public"


def test_constraint_cache_uses_schema_qualified_table_keys() -> None:
    mgr = make_manager()

    assert mgr.unique_keys["public.same_name"] == ["public_code"]
    assert mgr.unique_keys["tenant_a.same_name"] == ["tenant_code"]
    assert mgr._get_most_suitable_unique_keys(PublicSameName, pd.DataFrame([{"public_code": "A"}])) == ["public_code"]
    assert mgr._get_most_suitable_unique_keys(TenantSameName, pd.DataFrame([{"tenant_code": "B"}])) == ["tenant_code"]


def test_try_convert_false_keeps_values_unconverted() -> None:
    mgr = make_manager()
    df = pd.DataFrame([{"id": 1, "created_at": "2026-05-14T01:02:03"}])

    converted = mgr._convert_df_for_db(df, DateModel, try_convert=True)
    unconverted = mgr._convert_df_for_db(df, DateModel, try_convert=False)

    assert converted.loc[0, "created_at"] != df.loc[0, "created_at"]
    assert unconverted.loc[0, "created_at"] == df.loc[0, "created_at"]
    assert unconverted is not df


@pytest.mark.asyncio
async def test_partial_commit_returns_failed_batches_without_raise() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.commits = 0
            self.rollbacks = 0

        async def execute(self, stmt: Executable) -> None:
            return None

        async def commit(self) -> None:
            self.commits += 1

        async def rollback(self) -> None:
            self.rollbacks += 1

    mgr = make_manager()
    session = FakeSession()
    df = pd.DataFrame([{"id": 1}, {"id": 2}])

    async def execute_batch(batch: pd.DataFrame) -> None:
        if int(batch.iloc[0]["id"]) == 1:
            raise RuntimeError("batch failed")
        await session.execute(text("SELECT 1"))

    result = await mgr._execute_batches(df, session=session, rows_per_batch=1, partial_commit=True, execute_batch=execute_batch)

    assert result["cnt_success_rows"] == 1
    assert result["cnt_failed_rows"] == 1
    assert len(result["df_failed"]) == 1
    assert result["errors"]
    assert session.commits == 1
    assert session.rollbacks == 1


@pytest.mark.asyncio
async def test_database_maker_run_inside_running_loop() -> None:
    maker = DataBaseMaker("dev", "user", "password", "localhost")

    async def fake_run_async() -> bool:
        return True

    maker._run_async = fake_run_async

    assert maker.run() is True
