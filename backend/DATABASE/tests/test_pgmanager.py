import os

import pytest

from DATABASE.models import BaseModel
from DATABASE.dbms.postgre.pg_manager import DataBaseMaker, PGDBManager


DB_NAME = os.getenv("TEST_DB_NAME", "dev")
DB_USER = os.getenv("TEST_DB_USER", "admin")
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "123!@#qwe")
DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = int(os.getenv("TEST_DB_PORT", "5432"))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_tables_manual_integration():
    maker = DataBaseMaker(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    assert maker.run()

    db = PGDBManager(BaseModel, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    count = await db.create_tables()

    assert count >= 1
