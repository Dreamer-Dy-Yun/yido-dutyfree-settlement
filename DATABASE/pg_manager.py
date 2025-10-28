###########################################
# Module name : models
# Module class : SQLAlchemy ORM Models
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.11
# Updated at : 2025.07.11
# Supported by : ChatGPT-4o
# Note : SQLAlchemy ORM 모델 정의
#       2025.09.23 : PGDBManager.upsert_dataframe()에 주석 추가
#       2025.10.14 : PGDBManager.truncate_table() 추가
#       2025.10.16 : 버그 수정 
#                    PGDBManager.upsert_dataframe()
#                       - df에 존재하나 table에 존재하지 않는 컬럼은 무시되도록 수정
#                       - 주석 수정/추가
#       2025.10.17 : PGDBManager.execute_query() 확장
#       2025.10.20 : PGDBManager.upsert_dataframe() 반환값 변경(None → 업데이트 된 행 수(int))
#                    PGDBManager 클래스 변수를 인스턴스 변수로 변경
# TODO : Steaming용 모듈 작성 고려
############################################

import urllib
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy import Table, text, UniqueConstraint, Column
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Type, TypeVar, Optional
from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.elements import ColumnElement, Executable
import asyncpg
import asyncio

from CUSTOMIZED.cust_logger import logger

TableModel = TypeVar('TableModel', bound=DeclarativeBase)

# TODO : Error 클래스 등 나누기.
'''
asyncpg 사용시 유니코드 문제로 비동기로 pg 접속이 안될 수 있음. 그 경우 아래 확인

제어판 > 국가 또는 지역 > 관리자 옵션 > 유니코드를 지원하지 않는 프로그램용 언어 
> 시스템 로캘 변경(C)... > ✅Beta: 세계 언어 지원을 위해 Unicode UTF-8 사용

체크필수!!!
'''

class DataBaseMaker:

    def __init__(self, db_name: str, user: str, password: str, host: str, port: int = 5432):
        self.db_name: str = db_name
        self.user: str = user
        self.password: str = password
        self.host: str = host
        self.port: int = port
        self.conn: Optional[asyncpg.Connection] = None


    def run(self) -> bool:
        return asyncio.run(self._run_async())


    async def _run_async(self) -> bool:
        try:
            self.conn = await asyncpg.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database="postgres"
            )
            await self._exists_database()
            logger.info("✅ Done.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            return False
        finally:
            if self.conn:
                await self.conn.close()


    async def _exists_database(self, make_db_if_not_exists: bool = True):
        try:
            exists = await self.conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
                self.db_name
            )

            if not exists and make_db_if_not_exists:
                await self.conn.execute(f'CREATE DATABASE "{self.db_name}"')
                logger.info(f'✅ Database "{self.db_name}" is created.')
            else:
                logger.info(f'✅ Database "{self.db_name}" is already exists.')
            
        except Exception as e:
            logger.warning(f'Failed to create database "{self.db_name}": {e}')


class PGDBManager:
    """Postgre 전용 (비동기)"""

    def __init__(self, base_model: Type[DeclarativeBase], db_name: str, user: str, password: str, host: str, port: int = 5432):
        self.db_name: str = db_name
        self.user: str = user
        self.password: str = password
        self.host: str = host
        self.port: int = port

        self.async_engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[sessionmaker] = None
        self.base_model: Optional[Type[DeclarativeBase]] = None
        self.client_encoding: str = ""
        
        self.initialize_engine(self.db_name, self.user, self.password, self.host, self.port)
        self.base_model = base_model
        self.uniqueness: dict[str, list] = self.get_uniqueness(self.base_model)
        self.base_fields: dict = {key : val for key, val in vars(self.base_model).items() if isinstance(val, Column)}


    async def __aenter__(self):
        self.session = self.session_maker()
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.__aexit__(exc_type, exc, tb)


    def initialize_engine(self, dbname: str, user: str, password: str, host: str, port: int = 5432, client_encoding: str = "utf8"):
        if self.async_engine is None:
            logger.info(f"{user}:password@{host}:{str(port)}/{dbname}")

            pw: str = urllib.parse.quote_plus(password)
            uri: str = f"postgresql+asyncpg://{user}:{pw}@{host}:{str(port)}/{dbname}"
            self.client_encoding = client_encoding
            self.async_engine = create_async_engine(uri, echo=True)
            self.session_maker = sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )


    async def create_tables(self):
        async with self.async_engine.begin() as conn:
            await conn.execute(text(f"SET client_encoding TO '{self.client_encoding}'"))
            await conn.run_sync(self.base_model.metadata.create_all)
        logger.info("✅All tables are CREATED.")
    

    async def drop_tables(self):
        async with self.async_engine.begin() as conn:
            # 테이블별로 CASCADE 옵션으로 삭제
            for table_name in reversed(self.base_model.metadata.tables.keys()):
                await conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
        logger.info("✅All tables are REMOVED.")


    async def execute_query(self, query: str | Executable, params: dict | list[dict] | None = None):
        """비동기 ORM 세션을 사용해서 쿼리 실행 (파라미터 바인딩 지원)"""
        async with self.session_maker() as session:
            try:
                if isinstance(query, str):
                    query = text(query)
                logger.info(f"⏩SQL : {str(query)} | params: {params}")
                result = await session.execute(query, params or {})
                return result
            except Exception as e:
                await session.rollback()
                logger.exception(f"❌Query execution error: {str(e)}")
                raise e


    async def truncate_table(self, table: DeclarativeBase, restart_identity: bool = True, cascade: bool = True) -> bool:
        """
        테이블 비우기
        에러 없이, 성패 (True : 성공 / False : 에러) 만 반환.
        """
        try : 
            query: str = f"TRUNCATE TABLE {table.__tablename__}"

            if restart_identity:
                query += " RESTART IDENTITY"
            if cascade:
                query += " CASCADE"
            query += ";"

            await self.execute_query(query)
            return True

        except Exception as e:
            logger.exception(f"❌ TRUNCATE 실패 @ {table.__tablename__} | 이유: {str(e)}")
            return False


    async def upsert_dataframe(self, table: DeclarativeBase, df: DataFrame) -> int:
        '''
        자동 Upserter.
        가용한 모든 df(DataFrame)컬럼 업데이트.
            - df(DataFrame)에는 table의 모든 Unique / Primary Key 컬럼이 존재하여야 함.
            - Unique / Primary Key를 제외한 모든 컬럼이 양쪽에 존재할 필요는 없음 
                - df에 존재하지 않는 컬럼은 table에 업데이트 되지 않음(에러 발생 X)
                - table에 존재하지 않는 df컬럼은 무시됨(에러 발생 X)
                - df 값이 None 인 경우 Null 값으로 업데이트 됨

        Table 타입은 DeclarativeBase
        >> sqlalchemy.orm.DeclarativeBase

        ★ DataFrame[col_name] 의 타입이 datetime64[ns] 인 경우, 결측치가 NaT 객체로 변환되나, 
        SQLAlchemy에서는 NaT등을 허용하지 않고 None만을 허용하므로, NaT등의 경우 Error 반환.
        이를 방지하기 위해, "df[col_name].where(df[col_name].notna(), None)"으로 None으로 변환한 뒤 입력할 것.
        여기서 처리 할 수 있으나, 이 이상 범용화하면 성능저하가 우려되므로 필요한 경우에만 먼저 처리하여 입력 할 것.   
        '''
        # 항상 그렇듯 극한 성능 필요하면 언어 변경 및 SQL 수기 작성 필요 
        async with self.session_maker() as session:
            try:
                logger.info(f"🚀 START [upsert_dataframe]")
                table_name: str = table.__tablename__
                uniqs: list = self.uniqueness[table_name]

                if not uniqs:
                    raise ValueError(f"Can't find PK/UK in {table_name}")

                rows: list[dict] = df.to_dict(orient="records")

                stmt: Insert = insert(table).values(rows)
                ce: ColumnElement = stmt.excluded

                update_cols = {c: getattr(ce, c) for c in df.columns if hasattr(ce, c)}

                if not update_cols:
                    raise ValueError(f"No column to update except for PK/UK")

                # index_elements에는 list, set, dict 타입 사용 가능
                stmt = stmt.on_conflict_do_update(index_elements=uniqs, set_=update_cols)

                logger.info(f"⏫ UPSERT {table_name} rows={len(rows)} keys={uniqs} set={list(update_cols.keys())}")
                await session.execute(stmt)
                await session.commit()

                return len(rows)

            except Exception as e:
                await session.rollback()
                logger.exception(f"❌ UPSERT 실패 @ {table.__tablename__} | 이유: {str(e)}")
                raise e


    def get_uniqueness(self, base_model: Type[DeclarativeBase]) -> dict:
        """
        DB 내 모든 테이블을 순회하며,
        테이블명: list(유니크키 컬럼 리스트 또는 프라이머리키 컬럼 리스트) 반환
        """
        uniqueness = {}
        tables = base_model.metadata.tables

        for table_name, table in tables.items():
            unique_cols: list = []
            unique_cols = self._get_unique_columns(table, unique_cols)
            unique_cols = self._get_primary_columns(table, unique_cols)
            uniqueness.update({table_name: unique_cols})
        return uniqueness


    @staticmethod
    def _get_unique_columns(table: Table, unique_cols: list | None = None) -> list:
        if unique_cols:
            return unique_cols

        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                unique_cols = [col.name for col in constraint.columns]
                break
        return unique_cols


    @staticmethod
    def _get_primary_columns(table: Table, unique_cols: list | None = None) -> list:
        if unique_cols:
            return unique_cols

        return [col.name for col in table.primary_key.columns]
        