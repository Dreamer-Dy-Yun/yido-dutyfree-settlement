from __future__ import annotations

import asyncio
import threading
from typing import Optional

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncContextManager

from CUSTOMIZED.cust_logger import logger
from DATABASE.dbms.postgre.pg_identifiers import quote_identifier


class DataBaseMaker:
    """테스트/개발용 PostgreSQL database 생성기."""

    def __init__(self, db_name: str, user: str, password: str, host: str, port: int = 5432) -> None:
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn: Optional[asyncpg.Connection] = None
        self._session_cm: AsyncContextManager[AsyncSession] | None = None
        self.session: AsyncSession | None = None

    def run(self) -> bool:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._run_async())

        result: list[bool] = []
        worker = threading.Thread(target=lambda: result.append(asyncio.run(self._run_async())))
        worker.start()
        worker.join()
        return result[0] if result else False

    async def _run_async(self) -> bool:
        try:
            self.conn = await asyncpg.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database="postgres",
            )
            await self._ensure_database()
            logger.info("Database check is done.")
            return True
        except Exception as exc:
            logger.error(f"Database check failed: {exc}")
            return False
        finally:
            if self.conn:
                await self.conn.close()

    async def _ensure_database(self, make_db_if_not_exists: bool = True) -> None:
        if self.conn is None:
            raise RuntimeError("Database connection is not open.")

        exists = await self.conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            self.db_name,
        )

        if exists:
            logger.info(f'Database "{self.db_name}" already exists.')
            return

        if not make_db_if_not_exists:
            raise RuntimeError(f'Database "{self.db_name}" does not exist.')

        await self.conn.execute(f"CREATE DATABASE {quote_identifier(self.db_name)}")
        logger.info(f'Database "{self.db_name}" is created.')

    async def _exists_database(self, make_db_if_not_exists: bool = True) -> None:
        """Backward-compatible alias for older tests/callers."""
        await self._ensure_database(make_db_if_not_exists)
