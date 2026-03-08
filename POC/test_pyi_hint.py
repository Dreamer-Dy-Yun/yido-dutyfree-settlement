from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
import pandas as pd

from DATABASE.dbms.postgre.pg_manager import PGDBManager


async def test_upsert_without_session(
    db: PGDBManager,
    table: type[DeclarativeBase],
    df: pd.DataFrame,
) -> None:
    await db.upsert_batch(table=table, data=df, partial_commit=True)
    result = await db.upsert_batch(table=table, data=df, partial_commit=True)
    reveal_type(result)


async def test_upsert_with_session(
    db: PGDBManager,
    session: AsyncSession,
    table: type[DeclarativeBase],
    df: pd.DataFrame,
) -> None:
    result = await db.upsert_batch(
        table=table,
        data=df,
        session=session,
        params_per_chunk=1000,
    )
    reveal_type(result)


async def test_update_without_session(
    db: PGDBManager,
    table: type[DeclarativeBase],
    df: pd.DataFrame,
) -> None:
    result = await db.update_batch(
        table=table,
        data_to_update=df,
        params_per_chunk=1000,
        partial_commit=True,
    )
    reveal_type(result)
