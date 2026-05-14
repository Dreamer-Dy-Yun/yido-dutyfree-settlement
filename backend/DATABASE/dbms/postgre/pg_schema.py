from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Self

from sqlalchemy import Table, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.schema import AddConstraint

from CUSTOMIZED.cust_logger import logger
from DATABASE.dbms.postgre.pg_identifiers import quote_identifier, quote_search_path, quote_table


class SchemaManagerMixin:
    base_model: type[DeclarativeBase]
    client_encoding: str
    schemas: list[str] | None
    async_engine: AsyncEngine
    session_maker: sessionmaker[AsyncSession]

    async def set_schemas(self, schemas: list[str] | None = None) -> Self:
        if schemas:
            await self.exist_schemas(schemas, raise_error=True)
            self.schemas = schemas.copy()
        else:
            self.schemas = None
        return self

    async def exist_schemas(self, schemas: list[str], raise_error: bool = False) -> bool:
        if not schemas:
            return False
        existing = set(await self.get_all_schemas())
        missing = set(schemas) - existing
        if not missing:
            return True
        message = f"Schemas do not exist: {', '.join(sorted(missing))}"
        logger.error(message)
        if raise_error:
            raise ValueError(message)
        return False

    async def exists_schema(self, schema: str) -> bool:
        result = await self.execute_query(
            text("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = :schema)"),
            {"schema": schema},
        )
        return bool(result.scalar())

    async def create_schema(self, schema: str) -> bool:
        await self.execute_query(text(f"CREATE SCHEMA IF NOT EXISTS {quote_identifier(schema)}"))
        return True

    async def drop_schema(self, schema: str) -> bool:
        await self.execute_query(text(f"DROP SCHEMA IF EXISTS {quote_identifier(schema)}"))
        return True

    async def _set_session_schemas(self, session: AsyncSession, schemas: list[str] | None = None) -> None:
        target_schemas = schemas or self.schemas
        if target_schemas:
            await session.execute(text(f"SET search_path TO {quote_search_path(target_schemas)}"))

    async def get_all_schemas(self) -> list[str]:
        result = await self.execute_query(text("SELECT nspname FROM pg_namespace ORDER BY nspname"))
        return [row[0] for row in result.fetchall()]

    @asynccontextmanager
    async def open_session(self, schemas: list[str] | None = None) -> AsyncIterator[AsyncSession]:
        async with self.session_maker() as session:
            await self._set_session_schemas(session, schemas)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self, schema: str | None = None) -> int:
        if schema and not await self.exists_schema(schema):
            await self.create_schema(schema)
            logger.info(f"Schema '{schema}' is created.")

        async with self.async_engine.begin() as conn:
            await conn.execute(text(f"SET client_encoding TO '{self.client_encoding}'"))
            if not schema:
                await conn.run_sync(self.base_model.metadata.create_all)
                logger.info("All tables are created.")
                return 0

            tables = self._filter_tables_by_schema(schema)
            if not tables:
                logger.warning(f"No tables found for schema '{schema}'.")
                return 0

            for table in tables:
                await conn.run_sync(lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True))
            logger.info(f"{len(tables)} tables in schema '{schema}' are created.")
            return len(tables)

    def _filter_tables_by_schema(self, schema: str) -> list[Table]:
        return [table for table in self.base_model.metadata.tables.values() if table.schema == schema]

    async def drop_tables(self, schema: str | None = None) -> int:
        async with self.async_engine.begin() as conn:
            tables = list(self.base_model.metadata.tables.values()) if not schema else self._filter_tables_by_schema(schema)
            if not tables:
                logger.warning(f"No tables found for schema '{schema}' to drop." if schema else "No tables to drop.")
                return 0

            for table in reversed(tables):
                await conn.execute(text(f"DROP TABLE IF EXISTS {quote_table(table)} CASCADE"))
            logger.info(f"{len(tables)} tables are removed.")
            return len(tables)

    async def copy_tables_of_schema(self, schema_to_make: str, schemas_for_fk: list[str] | None = None) -> int:
        tenant_tables = [table for table in self.base_model.metadata.tables.values() if table.schema is None]
        if not tenant_tables:
            raise RuntimeError("No tenant tables (schema=None).")

        async with self.async_engine.begin() as conn:
            if await self._schema_exists(conn, schema_to_make):
                raise RuntimeError(f"Schema '{schema_to_make}' already exists.")

            await conn.execute(text(f"CREATE SCHEMA {quote_identifier(schema_to_make)}"))
            search_path = [schema_to_make] + (schemas_for_fk or [])
            await conn.execute(text(f"SET search_path TO {quote_search_path(search_path)}"))

            for table in tenant_tables:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(
                        bind=sync_conn,
                        checkfirst=False,
                        include_foreign_key_constraints=[],
                    )
                )

            for table in tenant_tables:
                for fk in table.foreign_key_constraints:
                    await conn.run_sync(lambda sync_conn, c=fk: sync_conn.execute(AddConstraint(c)))

        return len(tenant_tables)

    async def truncate_table(self, table: type[DeclarativeBase], restart_identity: bool = True, cascade: bool = True) -> bool:
        try:
            query = f"TRUNCATE TABLE {quote_table(table.__table__)}"
            if restart_identity:
                query += " RESTART IDENTITY"
            if cascade:
                query += " CASCADE"
            await self.execute_query(query)
            return True
        except Exception as exc:
            logger.exception(f"TRUNCATE failed @ {table.__table__.fullname}: {exc}")
            return False

    async def _schema_exists(self, conn: AsyncConnection, schema: str) -> bool:
        result = await conn.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = :schema)"),
            {"schema": schema},
        )
        return bool(result.scalar())
