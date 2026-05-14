from __future__ import annotations

from typing import TYPE_CHECKING, overload

import pandas as pd
from pandas import DataFrame
from sqlalchemy import and_, update, values
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.elements import ColumnElement, Executable

from DATABASE.dbms.postgre.pg_batch_executor import BatchResult, PGBatchExecutor
from DATABASE.dbms.postgre.pg_constraints import PGConstraintInspector
from DATABASE.dbms.postgre.pg_dataframe import PGDataFrameConverter

if TYPE_CHECKING:
    from DATABASE.dbms.postgre.pg_manager import PGDBManager


class PGBatchWriter:
    def __init__(
        self,
        manager: PGDBManager,
        converter: PGDataFrameConverter,
        constraints: PGConstraintInspector,
        executor: PGBatchExecutor,
    ) -> None:
        self.manager = manager
        self.converter = converter
        self.constraints = constraints
        self.executor = executor

    @overload
    async def upsert_batch(
        self,
        table: type[DeclarativeBase],
        data: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        params_per_chunk: int = 30000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
    ) -> BatchResult:
        ...

    @overload
    async def upsert_batch(
        self,
        table: type[DeclarativeBase],
        data: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        session: AsyncSession | None = None,
        params_per_chunk: int = 30000,
        allow_infinity: bool = True,
    ) -> BatchResult:
        ...

    async def upsert_batch(
        self,
        table: type[DeclarativeBase],
        data: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        session: AsyncSession | None = None,
        params_per_chunk: int = 30000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
    ) -> BatchResult:
        df = self._prepare_batch_dataframe(data, table, try_convert, allow_infinity, "data")
        self._validate_conflict_cols(conflict_cols, table)
        rows_per_batch = self._rows_per_batch(df, params_per_chunk)

        if session is not None:
            return await self._upsert_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit=False)

        async with self.manager._session_factory()() as session:
            await self.manager._set_session_schemas(session, schemas)
            try:
                result = await self._upsert_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit)
                if not partial_commit:
                    await session.commit()
                return result
            except Exception:
                if not partial_commit:
                    await session.rollback()
                raise

    async def _upsert_dataframe(
        self,
        table: type[DeclarativeBase],
        df: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
    ) -> int:
        result = await self.upsert_batch(table, df, schemas, conflict_cols, try_convert)
        return int(result["cnt_success_rows"])

    @overload
    async def update_batch(
        self,
        table: type[DeclarativeBase],
        data_to_update: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
    ) -> BatchResult:
        ...

    @overload
    async def update_batch(
        self,
        table: type[DeclarativeBase],
        data_to_update: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        session: AsyncSession | None = None,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
    ) -> BatchResult:
        ...

    async def update_batch(
        self,
        table: type[DeclarativeBase],
        data_to_update: pd.DataFrame | None = None,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        session: AsyncSession | None = None,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
        data: pd.DataFrame | None = None,
    ) -> BatchResult:
        source = data_to_update if data_to_update is not None else data
        df = self._prepare_batch_dataframe(source, table, try_convert, allow_infinity, "data_to_update")
        self._validate_conflict_cols(conflict_cols, table)
        rows_per_batch = self._rows_per_batch(df, params_per_chunk)

        if session is not None:
            return await self._update_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit=False)

        async with self.manager._session_factory()() as session:
            await self.manager._set_session_schemas(session, schemas)
            try:
                result = await self._update_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit)
                if not partial_commit:
                    await session.commit()
                return result
            except Exception:
                if not partial_commit:
                    await session.rollback()
                raise

    def _prepare_batch_dataframe(
        self,
        data: pd.DataFrame | None,
        table: type[DeclarativeBase],
        try_convert: bool,
        allow_infinity: bool,
        label: str,
    ) -> pd.DataFrame:
        if not isinstance(data, DataFrame):
            raise ValueError(f"Invalid {label} type: {type(data)}")
        if len(data) == 0:
            return DataFrame()
        if len(data.columns) == 0:
            raise ValueError("DataFrame has no columns.")
        return self.converter._convert_df_for_db(data, table, try_convert=try_convert, allow_infinity=allow_infinity)

    def _rows_per_batch(self, df: pd.DataFrame, params_per_chunk: int) -> int:
        if len(df) == 0:
            return 1
        return max(1, params_per_chunk // max(1, len(df.columns)))

    def _validate_conflict_cols(self, conflict_cols: list[str] | None, table: type[DeclarativeBase]) -> None:
        if conflict_cols and not self.constraints._is_valid_conflict_cols(conflict_cols, table):
            raise ValueError(f"Invalid conflict columns: {conflict_cols}")

    async def _upsert_dataframe_core(
        self,
        table: type[DeclarativeBase],
        df: pd.DataFrame,
        session: AsyncSession,
        rows_per_batch: int,
        conflict_cols: list[str] | None = None,
        partial_commit: bool = True,
    ) -> BatchResult:
        return await self._execute_upsert_batches(table, df, session, rows_per_batch, conflict_cols, partial_commit)

    async def _update_dataframe_core(
        self,
        table: type[DeclarativeBase],
        df: pd.DataFrame,
        session: AsyncSession,
        rows_per_batch: int,
        conflict_cols: list[str] | None = None,
        partial_commit: bool = True,
    ) -> BatchResult:
        return await self._execute_update_batches(table, df, session, rows_per_batch, conflict_cols, partial_commit)

    async def _execute_upsert_batches(
        self,
        table: type[DeclarativeBase],
        df: pd.DataFrame,
        session: AsyncSession,
        rows_per_batch: int,
        conflict_cols: list[str] | None,
        partial_commit: bool,
    ) -> BatchResult:
        async def execute_batch(batch: pd.DataFrame) -> None:
            upsert_stmt = self._build_upsert_statement(table, batch, conflict_cols)
            await session.execute(upsert_stmt)

        return await self.executor.execute_batches(df, session, rows_per_batch, partial_commit, execute_batch)

    async def _execute_update_batches(
        self,
        table: type[DeclarativeBase],
        df: pd.DataFrame,
        session: AsyncSession,
        rows_per_batch: int,
        conflict_cols: list[str] | None,
        partial_commit: bool,
    ) -> BatchResult:
        async def execute_batch(batch: pd.DataFrame) -> None:
            update_stmt = self._build_update_statement(table, batch, conflict_cols)
            if update_stmt is not None:
                await session.execute(update_stmt)

        return await self.executor.execute_batches(df, session, rows_per_batch, partial_commit, execute_batch)

    def _build_upsert_statement(self, table: type[DeclarativeBase], df: pd.DataFrame, conflict_cols: list[str] | None = None) -> Executable:
        uniqs = conflict_cols or self.constraints._get_most_suitable_unique_keys(table, df)
        df_filtered = self._filter_model_columns(table, df)
        rows = df_filtered.to_dict(orient="records")
        stmt: Insert = insert(table).values(rows)
        excluded: ColumnElement = stmt.excluded
        update_cols = {col: getattr(excluded, col) for col in df_filtered.columns if col not in uniqs and hasattr(excluded, col)}
        if not update_cols:
            return stmt.on_conflict_do_nothing(index_elements=uniqs)
        return stmt.on_conflict_do_update(index_elements=uniqs, set_=update_cols)

    def _stmt_upsert_dataframe(self, table: type[DeclarativeBase], df: pd.DataFrame, conflict_cols: list[str] | None = None) -> Executable:
        return self._build_upsert_statement(table, df, conflict_cols)

    def _build_update_statement(
        self,
        table: type[DeclarativeBase],
        df: pd.DataFrame,
        conflict_cols: list[str] | None = None,
    ) -> Executable | None:
        uniqs = conflict_cols or self.constraints._get_most_suitable_unique_keys(table, df)
        df_filtered = self._filter_model_columns(table, df)
        missing_keys = [key for key in uniqs if key not in df_filtered.columns]
        if missing_keys:
            raise ValueError(f"Missing key columns in df: {missing_keys} (keys={uniqs})")

        update_cols = [col for col in df_filtered.columns if col not in uniqs]
        if not update_cols:
            return None

        sql_table = table.__table__
        value_cols = uniqs + update_cols
        value_table = values(*[sql_table.c[col] for col in value_cols], name="v").data(
            [tuple(row.get(col) for col in value_cols) for row in df_filtered.to_dict(orient="records")]
        ).alias("v")

        return (
            update(sql_table)
            .where(and_(*[sql_table.c[key] == value_table.c[key] for key in uniqs]))
            .values(**{col: value_table.c[col] for col in update_cols})
            .execution_options(synchronize_session=False)
        )

    def _stmt_update_dataframe(
        self,
        table: type[DeclarativeBase],
        df: pd.DataFrame,
        conflict_cols: list[str] | None = None,
    ) -> Executable | None:
        return self._build_update_statement(table, df, conflict_cols)

    @staticmethod
    def _filter_model_columns(table: type[DeclarativeBase], df: pd.DataFrame) -> DataFrame:
        model_columns = [col.name for col in table.__table__.columns]
        return df[[col for col in model_columns if col in df.columns]]

__all__ = ["BatchResult", "PGBatchWriter"]
