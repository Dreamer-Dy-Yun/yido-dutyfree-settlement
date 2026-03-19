###########################################
# Module name : pg_manager.py
# Module class : PGDBManager, DataBaseMaker
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.11
# Updated at : 2026.02.23
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
#       2025.11.07 : PGDBManager.upsert_dataframe() 수정(불필요한 컬럼 제거)
#                       - 롤백하면서 제거된 로직 복구. 
#                       - 롤백 원인 : AI의 잘못된 대규모 코드 수정 
#                                   (다른 파일의 로직을 수정요청 하였으나, 이 파일을 수정. 심지어 잘못된 방향으로.)
#       2025.11.22 : PGDBManager.initialize_engine() 수정(pool_size, max_overflow 추가)
#       2025.11.30 : DBManager 추상 클래스 추가 및 상속
#       2026.02.19 : PGDBManager.set_schema() 등 스키마 관련 메서드 추가 (멀티 테넌트 대응)
#       2026.02.20 : 컨텍스트 매니저 수정
#       2026.02.23 : PGDBManager.create_tables() 수정(스키마 명시적 지정 가능)
#                    PGDBManager.copy_tables_of_schema() 추가 (스키마 복사 기능 추가. supported by ChatGPT-5.3)
#       2026.02.24 : PGDBManager._get_most_suitable_unique_keys() 추가 및 피영향 메서드 수정
#       2026.03.02 : PGDBManager.normalize_datetime_columns() -> PGDBManager.convert_datetime_for_db()로 수정
#                    PGDBManager.convert_numeric_for_db()로 추가
#       2026.03.04 : 싱글톤 호환을 위해, 주요 메서드들에 스키마 설정 옵션 추가, 매서드 레벨에서 스키마 선택(인젝션) 가능하도록 변경
#                    PGDBManager.open_session() 추가 (세션 컨트롤 필요시 사용), 레거시 컨텍스트 매니저 삭제
#       2026.03.05 : PGDBManager.update_dataframe() 추가, PGDBManager.batch_update_dataframe() 추가
#       2026.03.08 : PGDBManager.batch_upsert_dataframe() / PGDBManager.upsert_dataframe() -> PGDBManager.upsert_batch() 로 통합/수정
#                    PGDBManager.upsert_batch() 에서 스키마 설정 옵션 추가, 매서드 레벨에서 스키마 선택(인젝션) 가능하도록 변경
#                    PGDBManager.upsert_batch() : 세션 주입 가능한 옵션 추가
#                    ※ PGDBManager.update_batch()도 동일 수정
#       2026.03.19 : PGDBManager.upsert_batch() 에서 배치 단위 에러 메시지 모음 추가
# TODO : Steaming용 모듈 작성 고려
# TODO : 임의의 스키마 내 테이블 일괄 변경 (퍼블릭, 테넌트 스키마(스키마 미지정) 모두 가능)
# TODO : PGDBManager.convert_df_by_model() 추가. 테스트 완료시 기존 함수 삭제 (구현 : 2026.03.19)
############################################
import urllib
from decimal import Decimal


from DATABASE.dbms import DBManager
from sqlalchemy import (
    Table, text, Column, and_, values,
    update,
    UniqueConstraint, PrimaryKeyConstraint, ForeignKeyConstraint,
    String as SAString,
    Numeric, Integer, Float,
    DateTime, Date ,Time,
    Boolean, JSON,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.sql import quoted_name
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.elements import ColumnElement, Executable
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.schema import AddConstraint
from typing import Type, TypeVar, Optional, AsyncContextManager, Self, AsyncIterator, overload, Any
from pandas import DataFrame
import asyncpg
import asyncio
import numpy as np
import pandas as pd
from CUSTOMIZED.cust_logger import logger
from contextlib import asynccontextmanager

TableModel = TypeVar('TableModel', bound=DeclarativeBase)

# TODO : Error 클래스 등 나누기.
'''
asyncpg 사용시 유니코드 문제로 비동기로 pg 접속이 안될 수 있음. 그 경우 아래 확인

제어판 > 국가 또는 지역 > 관리자 옵션 > 유니코드를 지원하지 않는 프로그램용 언어 
> 시스템 로캘 변경(C)... > ✅Beta: 세계 언어 지원을 위해 Unicode UTF-8 사용

체크필수!!!
'''

class DataBaseMaker:
    """테스트용 DB 생성 클래스"""
    def __init__(self, db_name: str, user: str, password: str, host: str, port: int = 5432):
        self.db_name: str = db_name
        self.user: str = user
        self.password: str = password
        self.host: str = host
        self.port: int = port
        self.conn: Optional[asyncpg.Connection] = None
        self._session_cm: AsyncContextManager[AsyncSession] | None = None
        self.session: AsyncSession | None = None


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


    async def _exists_database(self, make_db_if_not_exists: bool = True) -> None:
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


class PGDBManager(DBManager):
    """Postgre 전용 (비동기)"""
    def __init__(
        self, 
        base_model: TableModel, 
        db_name: str, 
        user: str, 
        password: str, 
        host: str, 
        port: int = 5432,
        pool_size: int = 50,
        max_overflow: int = 150,
        ):
        self.db_name: str = db_name
        self.user: str = user
        self.password: str = password
        self.host: str = host
        self.port: int = port

        self.async_engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[sessionmaker] = None
        self.base_model: Optional[Type[DeclarativeBase]] = base_model
        self.client_encoding: str = ""
        
        self.initialize_engine(self.db_name, self.user, self.password, self.host, self.port, pool_size=pool_size, max_overflow=max_overflow)
        self.unique_constraints: dict[str, list[list[str]]] = {}
        self.primary_constraints: dict[str, list[list[str]]] = {}
        self.foreign_key_constraints: dict[str, list[list[str]]] = {}
        self.nullable_columns: dict[str, list[str]] = {}
        self.not_null_columns: dict[str, list[str]] = {}
        self.unique_keys: dict[str, list[str]] = {}
        self.primary_keys: dict[str, list[str]] = {}
        self._get_uniqueness(self.base_model)
        self.base_fields: dict = {key : val for key, val in vars(self.base_model).items() if isinstance(val, Column)}
        self.schemas: list[str] | None = None


    async def set_schemas(self, schemas: list[str] | None = None) -> Self:
        """
        기본 스키마 설정 (search_path 변경)
        각 메서드에서 스키마 미설정시 여기서 설정한 스키마가 기본값이 됨.
        Args:
            schemas: 설정할 스키마 이름 리스트 (예: ["tenant_123", "public"])
                    기본값은 None (public 스키마만 사용)
                    순서대로 검색 경로에 추가됨
                    
        Returns:
            Self (메서드 체이닝)
        """
        # 스키마 존재 여부 확인 (get_all_schemas 사용)
        # AI에게 맡겨놓으면 불필요한 최적화 + 부피 늘이는 코드 작성 시도하므로 유의.
        if schemas:
            await self.exist_schemas(schemas, raise_error=True)
            self.schemas = schemas.copy()
        return self
        

    async def exist_schemas(self, schemas: list[str], raise_error: bool = False) -> bool:
        """
        스키마 목록 존재 여부 확인
        
        Args:
            schemas: 존재 여부를 확인할 스키마 이름 리스트
        
        Returns:
            True: 모든 스키마가 존재하는 경우
            False: 하나 이상의 스키마가 존재하지 않는 경우
        """
        if schemas:
            all_schemas : set[str] = set(await self.get_all_schemas())
            missing_schemas : set[str] = set(schemas) - all_schemas
            if missing_schemas:
                logger.error(f"Schemas do not exist: {', '.join(missing_schemas)}")
                if raise_error:
                    raise ValueError(f"Schemas do not exist: {', '.join(missing_schemas)}")
                return False
            return True
        return False


    async def exists_schema(self, schema: str) -> bool:
        """단일 스키마 존재 여부 확인"""
        result = await self.execute_query(
            text("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = :schema)"),
            {"schema": schema}
        )
        return bool(result.scalar())


    async def create_schema(self, schema: str) -> bool:
        """스키마 생성"""
        # quoted_name을 사용하여 식별자 안전하게 처리
        schema_quoted = quoted_name(schema, quote=True)
        await self.execute_query(text(f'CREATE SCHEMA IF NOT EXISTS {schema_quoted}'))
        return True
    

    async def drop_schema(self, schema: str) -> bool:
        """스키마 삭제"""
        # quoted_name을 사용하여 식별자 안전하게 처리
        schema_quoted = quoted_name(schema, quote=True)
        await self.execute_query(text(f'DROP SCHEMA IF EXISTS {schema_quoted}'))
        return True


    async def _set_session_schemas(self, session: AsyncSession, schemas: list[str] | None = None) -> None:
        """세션에 스키마 설정 (헬퍼 메서드)"""
        schemas = schemas or self.schemas
        if schemas:
            # quoted_name을 사용하여 식별자 안전하게 처리
            schema_list = ", ".join([str(quoted_name(s, quote=True)) for s in schemas])
            await session.execute(text(f"SET search_path TO {schema_list}"))


    async def get_all_schemas(self) -> list[str]:
        """DB에 등록된 모든 스키마 목록 조회"""
        result = await self.execute_query(text("SELECT nspname FROM pg_namespace ORDER BY nspname"))
        schemas = [row[0] for row in result.fetchall()]
        return schemas


    def initialize_engine(
        self, 
        dbname: str, 
        user: str, 
        password: str, 
        host: str, 
        port: int = 5432, 
        client_encoding: str = "utf8",
        pool_size: int = 50,
        max_overflow: int = 150
        ):
        if self.async_engine is None:
            logger.info(f"{user}:***@{host}:{str(port)}/{dbname}")

            pw: str = urllib.parse.quote_plus(password)
            uri: str = f"postgresql+asyncpg://{user}:{pw}@{host}:{str(port)}/{dbname}"
            self.client_encoding = client_encoding
            self.async_engine = create_async_engine(uri, echo=False, pool_size=pool_size, max_overflow=max_overflow)
            self.session_maker = sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )


    @asynccontextmanager
    async def open_session(
        self,
        schemas: list[str] | None = None,
    ) -> AsyncIterator[AsyncSession]:
        '''
        세션 컨트롤이 필요한 경우 사용.
        Args:
            schemas: search_path로 설정할 스키마 리스트 (예: ["tenant_xxx", "public"])
        Returns:
            AsyncSession
        '''
        async with self.session_maker() as session:
            await self._set_session_schemas(session, schemas)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


    async def create_tables(self, schema: str | None = None) -> int:
        """
        테이블 생성
        
        Args:
            schema: 특정 스키마의 테이블만 생성 (None이면 모든 테이블 생성)
                    예: "public" → public 스키마 테이블만 생성
        """
        # 스키마가 지정된 경우, 스키마 존재 여부 확인 및 생성
        if schema:
            if not await self.exists_schema(schema):
                await self.create_schema(schema)
                logger.info(f"✅Schema '{schema}' is CREATED.")
        
        async with self.async_engine.begin() as conn:
            await conn.execute(text(f"SET client_encoding TO '{self.client_encoding}'"))
            
            if not schema:
                await conn.run_sync(self.base_model.metadata.create_all)
                logger.info("✅All tables are CREATED.")
                return 0

            filtered_tables = self._filter_tables_by_schema(schema)
            
            if not filtered_tables:
                logger.warning(f"⚠️No tables found for schema '{schema}'.")
                return 0

            for table in filtered_tables:
                await conn.run_sync(lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True))
            logger.info(f"✅Tables in schema '{schema}' are CREATED.")
            return len(filtered_tables)

    
    def _filter_tables_by_schema(self, schema: str) -> list[Table]:
        """특정 스키마의 테이블만 필터링"""
        return [
            table for table in self.base_model.metadata.tables.values()
            if table.schema == schema
        ]
        
        
    async def drop_tables(self, schema: str | None = None) -> int:
        """
        테이블 삭제
        
        Args:
            schema: 특정 스키마의 테이블만 삭제 (None이면 모든 테이블 삭제)
                    예: "public" → public 스키마 테이블만 삭제
                    
        Returns:
            삭제된 테이블 개수
        """
        async with self.async_engine.begin() as conn:
            if not schema:
                # 모든 테이블 삭제 (기존 동작)
                tables_to_drop = list(self.base_model.metadata.tables.values())
            else:
                # 특정 스키마의 테이블만 필터링
                tables_to_drop = self._filter_tables_by_schema(schema)
            
            if not tables_to_drop:
                logger.warning(f"⚠️No tables found for schema '{schema}' to drop." if schema else "⚠️No tables to drop.")
                return 0
            
            # 의존성 순서를 고려하여 역순으로 삭제
            for table in reversed(tables_to_drop):
                # 스키마가 있으면 스키마.테이블명 형식으로 삭제
                if table.schema:
                    schema_quoted = str(quoted_name(table.schema, quote=True))
                    name_quoted = str(quoted_name(table.name, quote=True))
                    table_ref = f"{schema_quoted}.{name_quoted}"
                else:
                    table_ref = str(quoted_name(table.name, quote=True))
                await conn.execute(text(f"DROP TABLE IF EXISTS {table_ref} CASCADE;"))
            
            schema_msg = f" in schema '{schema}'" if schema else ""
            logger.info(f"✅{len(tables_to_drop)} tables{schema_msg} are REMOVED.")
            return len(tables_to_drop)


    async def copy_tables_of_schema(self, schema_to_make: str, schemas_for_fk: list[str] | None = None) -> int:
        """
        schema가 지정되지 않은 테이블을 대상으로 DB에 새로운 스키마를 생성하고, 테이블을 복사.

        정책:
        - schema_to_make 존재하면 raise
        - tenant 대상은 schema=None 모델만
        """

        # tenant 대상: schema=None
        tenant_tables: list[Table] = [
            t for t in self.base_model.metadata.tables.values()
            if t.schema is None
        ]

        if not tenant_tables:
            raise RuntimeError("No tenant tables (schema=None).")

        async with self.async_engine.begin() as conn:
            # 1) schema 존재하면 실패
            if await self.exists_schema(schema_to_make):
                raise RuntimeError(f"Schema '{schema_to_make}' already exists.")

            # 2) schema 생성 + search_path
            to_schema: str = str(quoted_name(schema_to_make, quote=True))
            await conn.execute(text(f"CREATE SCHEMA {to_schema}"))

            query: str = f"SET search_path TO {to_schema}"
            if schemas_for_fk:
                query += ", " + ", ".join([str(quoted_name(s, quote=True)) for s in schemas_for_fk])
            await conn.execute(text(query))

            # 3) 1-pass: FK 없이 테이블 생성
            for t in tenant_tables:
                await conn.run_sync(
                    lambda sync_conn, table=t: table.create(
                        bind=sync_conn,
                        checkfirst=False,
                        include_foreign_key_constraints=[],
                    )
                )

            # 4) 2-pass: FK 추가 (순환 포함 안전)
            for t in tenant_tables:
                for fk in t.foreign_key_constraints:
                    await conn.run_sync(
                        lambda sync_conn, c=fk: sync_conn.execute(AddConstraint(c))
                    )

        return len(tenant_tables)


    async def dispose_pool(self) -> None:
        """연결 풀 해제."""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("✅Connection pool disposed.")


    async def execute_query(
        self, query: str | Executable, 
        params: dict | list[dict] | None = None, 
        schemas: list[str] | None = None
        ):
        """
        단일 쿼리 실행. 반드시 커밋 됨.
        ※ 세션 컨트롤 필요시 PGDBManager에서 커넥션(conn) 직접 사용 할 것.
        Args:
            query: 실행할 SQL 쿼리 문자열 또는 Executable 객체
            params: 쿼리 파라미터 (딕셔너리 또는 딕셔너리 리스트)
            schemas: search_path로 설정할 스키마 리스트 (예: ["tenant_xxx", "public"])        
        Returns:
            쿼리 실행 결과 (DB별로 다를 수 있음, 일반적으로 SQLAlchemy Result 객체)
        """
        async with self.session_maker() as session:
            try:
                await self._set_session_schemas(session, schemas)
                if isinstance(query, str):
                    query = text(query)
                # logger.info(f"⏩SQL : {str(query)} | params: {params}")
                result = await session.execute(query, params or {})
                # DDL/DML 반영을 위해 명시적으로 커밋
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.exception(f"❌Query execution error: {str(e)}")
                raise 


    async def truncate_table(self, table: DeclarativeBase, restart_identity: bool = True, cascade: bool = True) -> bool:
        """
        테이블 비우기
        에러 없이, 성패 (True : 성공 / False : 에러) 만 반환.
        """
        try : 
            # quoted_name을 사용하여 식별자 안전하게 처리
            table_name_quoted = str(quoted_name(table.__tablename__, quote=True))
            query: str = f"TRUNCATE TABLE {table_name_quoted}"

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
        

    @staticmethod
    def convert_datetime_for_db(df: pd.DataFrame, deep_copy: bool = True) -> pd.DataFrame:
        """datetime 컬럼만 대상으로 NaT → None 변환(DB insert 직전용)."""
        # 이하는 이미 사용하지 않는 로직이나, 메모차 남겨놓음.
        #   numpy/pandas datetime 모두 동일하게 정규화 (NaT → None 등)
        #   if np.issubdtype(result[col].dtype, np.datetime64)    ----ⓐ
        #   if pd.api.types.is_datetime64_any_dtype(result[col])  ----ⓑ
        #   일 때, 
        #   ⓑ ⊃ ⓐ
        
        # 이하릐 로직 함부러 고쳐달라고 하면 개판 낼 수 있으니 주의

        result = df.copy() if deep_copy else df
        # datetime64[ns], datetime64[ns, tz] 컬럼만 선택 (numpy/pandas 포함)
        datetime_cols = result.select_dtypes(include=["datetime", "datetimetz"]).columns

        for col in datetime_cols:
            single_column : pd.Series = pd.to_datetime(result[col], errors="coerce")

            # 타입 변환 : Timestamp -> datetime.datetime
            py = single_column.dt.to_pydatetime()
            out = pd.Series(py, index=single_column.index, dtype="object")

            # 결측치 처리 : NaT -> None (DB 에는 NaT 허용되지 않음)
            out.loc[single_column.isna()] = None

            result[col] = out

        return result


    @staticmethod
    def convert_numeric_for_db(df: pd.DataFrame, set_none_as: float | int | None = None, allow_infinity: bool = True, deep_copy: bool = True) -> pd.DataFrame:
        """numeric 컬럼만: NaN 처리 + (옵션) inf 처리."""
        result = df.copy() if deep_copy else df
        numeric_cols = result.select_dtypes(include=["integer", "floating"]).columns

        for col in numeric_cols:
            s = pd.to_numeric(result[col], errors="coerce")

            # 유효값 mask
            if allow_infinity:
                mask = s.notna()
            else:
                mask = s.notna() & np.isfinite(s)

            # None 유지 or 지정값 치환
            if set_none_as is None:
                result[col] = s.astype("object").where(mask, None)
            else:
                result[col] = s.where(mask, set_none_as)

        return result


    def _contains_all_not_nullable_cols(self, cols: list[str], table: DeclarativeBase) -> bool:
        not_nullable_cols = self.not_null_columns.get(table.__table__.name, [])
        return all(col in cols for col in not_nullable_cols)


    def _is_valid_conflict_cols(self, conflict_cols: list[str], table: DeclarativeBase) -> bool:
        table_name = table.__table__.name

        unique_constraints = self.unique_constraints.get(table_name, [])
        primary_constraints = self.primary_constraints.get(table_name, [])
        unique_keys = self.unique_keys.get(table_name, [])
        primary_keys = self.primary_keys.get(table_name, [])

        candidates: list[list[str]] = []
        candidates.extend(unique_constraints)
        candidates.extend(primary_constraints)
        candidates.extend([[c] for c in unique_keys])
        candidates.extend([[c] for c in primary_keys])

        target = set(conflict_cols)

        return any(set(candidate) == target for candidate in candidates)


    def _get_most_suitable_unique_keys(self, table: DeclarativeBase, df: pd.DataFrame) -> list[str]:
        table_name = table.__table__.name 
        cols_df: set[str] = set(df.columns)

        ucs = self.unique_constraints.get(table_name, [])
        pcs = self.primary_constraints.get(table_name, [])
        uks = self.unique_keys.get(table_name, [])
        pks = self.primary_keys.get(table_name, [])

        if not (ucs or pcs or uks or pks):
            raise ValueError(f"Can't find suitable PK/UK in {table_name}")

        for uniqs in ucs:
            if all(col in cols_df for col in uniqs):
                return uniqs

        for uniqs in pcs:
            if all(col in cols_df for col in uniqs):
                return uniqs

        for uniq in uks:
            if uniq in cols_df:
                return [uniq]

        for uniq in pks:
            if uniq in cols_df:
                return [uniq]

        # === 에러 메시지 ===
        raise ValueError(
            f"Missing required PK/UK/Constraint columns in DataFrame for table '{table_name}'. "
            f"Required columns (candidates): "
            f"unique_constraints={ucs}, "
            f"primary_constraints={pcs}, "
            f"unique_keys={uks}, "
            f"primary_keys={pks}. "
            f"Available columns: {list(df.columns)}"
        )

    @overload
    async def upsert_batch(
        self, 
        table: DeclarativeBase, 
        data: pd.DataFrame, 
        schemas: list[str] | None = None, 
        conflict_cols: list[str] | None = None, 
        try_convert: bool = True, 
        params_per_chunk: int = 10000, 
        allow_infinity: bool = True,
        partial_commit: bool = True,
        ) -> dict[str, int | DataFrame]:
        
        """
        Session 생성 후 작업 수행
        이 경우 
            - 스키마 이름 주입 필요(필요시)
            - 부분 커밋/ 전체커밋 여부 지정 가능 (전체커밋 : partial_commit=False, 부분커밋 : partial_commit=True)
            - 반환값: dict[str, int | DataFrame]
                - "cnt_success_rows": 성공한 행 수
                - "cnt_failed_rows": 실패한 행 수
                - "df_failed": 실패한 행들의 DataFrame
        """
        ...

    @overload
    async def upsert_batch(
        self, 
        table: DeclarativeBase, 
        data: pd.DataFrame, 
        schemas: list[str] | None = None, 
        conflict_cols: list[str] | None = None, 
        try_convert: bool = True, 
        session: AsyncSession | None = None, 
        params_per_chunk: int = 10000, 
        allow_infinity: bool = True,
        ) -> dict[str, int | DataFrame]:
        """
        Session 주입하여 작업 수행
        이 경우 
            - 해당 세션에서 스키마 변경 후 작업 수행(필요시)
            - 커밋/롤백은 호출부에서 처리
        """
        ...


    async def upsert_batch(
        self, 
        table: DeclarativeBase, 
        data: pd.DataFrame, 
        schemas: list[str] | None = None, 
        conflict_cols: list[str] | None = None, 
        try_convert: bool = True, 
        session: AsyncSession | None = None, 
        params_per_chunk: int = 30000, 
        allow_infinity: bool = True,
        partial_commit: bool = True,
        ) -> dict[str, int | DataFrame]:
        if not isinstance(data, DataFrame):
            raise ValueError(f"Invalid data type: {type(data)}")

        # 항상 그렇듯 극한 성능 필요하면 언어 변경 및 SQL 수기 작성 필요
        # df = self._convert_df_for_db(data, try_convert, allow_infinity)
        df = self.convert_df_by_model(data, table, allow_infinity, deep_copy=True)

        if conflict_cols and not self._is_valid_conflict_cols(conflict_cols, table):
            raise ValueError(f"Invalid conflict columns: {conflict_cols}")

        cnt_rows: int = len(df)
        cnt_cols: int = len(df.columns)

        if cnt_rows == 0:
            return {"cnt_success_rows": 0, "cnt_failed_rows": 0, "df_failed": DataFrame()}
        if cnt_cols == 0:
            raise ValueError("DataFrame has no columns.")

        rows_per_batch: int = max(1, params_per_chunk // cnt_cols)

        if session is not None:
            # 세션 주입시 커밋 허용하지 않음. 이 경우 커밋/롤백은 호출부에서 처리
            return await self._upsert_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit=False)
        else:
            async with self.session_maker() as session:
                await self._set_session_schemas(session, schemas)
                try:
                    result = await self._upsert_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit=partial_commit)
                    if not partial_commit:
                        # 부분 커밋 안하면 전체 커밋
                        await session.commit()
                    return result
                except Exception:
                    if not partial_commit:
                        await session.rollback()
                    raise 

    @staticmethod
    def _fix_cols_string(series: pd.Series) -> pd.Series:
        return series.astype(object).where(pd.notna(series), None)

    @staticmethod
    def _fix_cols_integer(series: pd.Series) -> pd.Series:
        s : pd.Series = pd.to_numeric(series, errors="coerce").astype("Int64")
        return s.astype(object).where(s.notna(), None)

    @staticmethod
    def _fix_cols_float(series: pd.Series, allow_infinity: bool = True) -> pd.Series:
        s : pd.Series = pd.to_numeric(series, errors="coerce")
        mask : pd.Series = s.notna() if allow_infinity else s.notna() & np.isfinite(s)
        return s.astype(object).where(mask, None)

    @staticmethod
    def _fix_cols_datetime(series: pd.Series) -> pd.Series:
        s : pd.Series = pd.to_datetime(series, errors="coerce")
        py: np.ndarray = s.dt.to_pydatetime()
        out: pd.Series = pd.Series(py, index=s.index, dtype="object")
        out.loc[s.isna()] = None
        return out

    @staticmethod
    def _fix_cols_date(series: pd.Series) -> pd.Series:
        s : pd.Series = pd.to_datetime(series, errors="coerce")
        py : np.ndarray = s.dt.date
        out : pd.Series = pd.Series(py, index=s.index, dtype="object")
        out.loc[s.isna()] = None
        return out

    @staticmethod
    def _fix_cols_time(series: pd.Series) -> pd.Series:
        s : pd.Series = pd.to_datetime(series, errors="coerce")
        py : np.ndarray = s.dt.time
        out : pd.Series = pd.Series(py, index=s.index, dtype="object")
        out.loc[s.isna()] = None
        return out

    @staticmethod
    def _fix_cols_boolean(series: pd.Series) -> pd.Series:
        def to_bool(v):
            if pd.isna(v):
                return None
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return bool(v)
            if isinstance(v, str):
                v = v.strip().lower()
                if v in ("true", "t", "1", "y", "yes"):
                    return True
                if v in ("false", "f", "0", "n", "no"):
                    return False
            return None

        return series.astype(object).apply(to_bool)

    @staticmethod
    def _to_decimal(v: float | int | str | Decimal | None) -> Decimal | None:
        if v is None or pd.isna(v):
            return None
        return Decimal(str(v))

    @staticmethod
    def _fix_cols_json(series: pd.Series) -> pd.Series:
        return series.astype(object).where(pd.notna(series), None)


    def convert_df_by_model(self, df: pd.DataFrame, model: DeclarativeBase, allow_infinity: bool = True, deep_copy: bool = True) -> pd.DataFrame:
        result = df.copy() if deep_copy else df

        for col in model.__table__.columns:
            col_name = col.name

            if col_name not in result.columns:
                continue

            s : pd.Series = result[col_name]

            if isinstance(col.type, SAString):
                result[col_name] = self._fix_cols_string(s)
            elif isinstance(col.type, Integer):
                result[col_name] = self._fix_cols_integer(s)
            elif isinstance(col.type, Float):
                result[col_name] = self._fix_cols_float(s, allow_infinity)
            elif isinstance(col.type, Numeric):
                s: pd.Series = self._fix_cols_float(s, allow_infinity)
                result[col_name] = s.apply(self._to_decimal)
            elif isinstance(col.type, DateTime):
                result[col_name] = self._fix_cols_datetime(s)
            elif isinstance(col.type, Date):
                result[col_name] = self._fix_cols_date(s)
            elif isinstance(col.type, Time):
                result[col_name] = self._fix_cols_time(s)
            elif isinstance(col.type, Boolean):
                result[col_name] = self._fix_cols_boolean(s)
            elif isinstance(col.type, JSON):
                result[col_name] = self._fix_cols_json(s)
            else:
                # unknown type → 안전하게 None 처리만
                result[col_name] = s.astype(object).where(pd.notna(s), None)

        return result


    def _convert_df_for_db(self, df: pd.DataFrame, table: DeclarativeBase, try_convert: bool = True, allow_infinity: bool = True) -> pd.DataFrame:
        if try_convert:
            df = df.copy()
            df = self.convert_datetime_for_db(df, deep_copy=False)
            df = self.convert_numeric_for_db(df, set_none_as=None, allow_infinity=allow_infinity, deep_copy=False)
            df = self.convert_string_cols_by_model(df, table)
        return df

    @staticmethod
    def convert_string_cols_by_model(df: pd.DataFrame, model: DeclarativeBase) -> pd.DataFrame:
        result = df.copy()

        for col in model.__table__.columns:
            col_name = col.name

            if col_name not in result.columns:
                continue

            if isinstance(col.type, SAString):
                s = result[col_name]
                result[col_name] = s.astype(object).where(pd.notna(s), None)

        return result


    async def _upsert_dataframe_core(
        self, 
        table: DeclarativeBase, 
        df: pd.DataFrame, 
        session: AsyncSession,
        rows_per_batch : int,
        conflict_cols: list[str] | None = None,
        partial_commit: bool = True,
        ) -> dict[str, int | DataFrame]:
        '''
        자동 Upserter. batch단위 커밋.
        가용한 모든 df(DataFrame)컬럼 업데이트.
            - df(DataFrame)에는 table 의 아래 중 하나를 만족하는 컬럼이 존재하여야 함 (유니크 제약이 우선임에 유의)
              - UniqueConstraint 
              - PrimaryKeyConstraint
              - UniqueKey
              - PrimaryKey
            - Key나 Constraint 와 not nullable 컬럼을 제외한 모든 컬럼이 양쪽에 존재할 필요는 없음 
              (df에 not nullable인 모든 컬럼은 반드시 존재해야 함)
                - df에 존재하지 않는 컬럼은 table에 업데이트 되지 않음(에러 발생 X)
                - table에 존재하지 않는 df컬럼은 무시됨(에러 발생 X)
                - df 값이 None 인 경우 Null 값으로 업데이트 됨
            -conflict_cols: 업데이트 기준 키 명시적 설정 가능. (None 이면 자동 설정)
        Table 타입은 DeclarativeBase
        >> sqlalchemy.orm.DeclarativeBase

        ★ DataFrame[col_name] 의 타입이 datetime64[ns] 인 경우, 결측치가 NaT 객체로 변환되나, 
        SQLAlchemy에서는 NaT등을 허용하지 않고 None만을 허용하므로, NaT등의 경우 Error 반환.
        이를 방지하기 위해, "df[col_name].where(df[col_name].notna(), None)"으로 None으로 변환한 뒤 입력할 것.
        여기서 처리 할 수 있으나, 이 이상 범용화하면 성능저하가 우려되므로 필요한 경우에만 먼저 처리하여 입력 할 것.   
        '''
        cnt_success_rows: int = 0
        cnt_failed_rows: int = 0
        dfs_failed_batch: list[DataFrame] = []
        df_failed: DataFrame = DataFrame()

        list_error_messages: list[str] = []

        for i in range(0, len(df), rows_per_batch):
            df_batch: DataFrame = df.iloc[i:i+rows_per_batch]
            batch_idx: int = i // rows_per_batch
            try:
                stmt: Insert = self._stmt_upsert_dataframe(table, df_batch, conflict_cols)
                await session.execute(stmt)
                if partial_commit:
                    await session.commit()
                cnt_success_rows += len(df_batch)
            except Exception as e:
                err_type: str = type(e).__name__
                orig: Any = getattr(e, "orig", None)
                msg: str = str(orig) if orig else str(e)
                # 배치 인덱스와 함께 요약만 남긴다 (상세 스택은 상위에서 로깅)
                list_error_messages.append(f"[batch={batch_idx}] {err_type}: {msg}")
                if partial_commit:
                    cnt_failed_rows += len(df_batch)
                    dfs_failed_batch.append(df_batch)
                    await session.rollback()
                else:
                    raise
            finally:
                pass
        if dfs_failed_batch:
            df_failed = pd.concat(dfs_failed_batch, ignore_index=False)

        if list_error_messages:
            table_name = getattr(table, "__tablename__", str(table))
            summary = (
                f"Error upserting dataframe into '{table_name}' "
                f"(success_rows={cnt_success_rows}, failed_rows={cnt_failed_rows}):"
            )
            raise ValueError(summary + "\n" + "\n".join(list_error_messages))
        return {"cnt_success_rows": cnt_success_rows, "cnt_failed_rows": cnt_failed_rows, "df_failed": df_failed}


    def _stmt_upsert_dataframe(self, table: DeclarativeBase, df: pd.DataFrame, conflict_cols: list[str] | None = None) -> Executable :

        uniqs: list[str] = conflict_cols or self._get_most_suitable_unique_keys(table, df)

        # 모델에 정의된 컬럼만 선택 (불필요한 컬럼 제거)
        model_columns : list[str] = [col.name for col in table.__table__.columns]
        df_filtered : DataFrame = df[[col for col in model_columns if col in df.columns]]
        
        rows: list[dict] = df_filtered.to_dict(orient="records")

        stmt: Insert = insert(table).values(rows)
        ce: ColumnElement = stmt.excluded

        update_cols = {c: getattr(ce, c) for c in df_filtered.columns if c not in uniqs and hasattr(ce, c)}

        # 키/유니크 값만 있는 경우: conflict 시 아무것도 하지 않음 (insert만 수행)
        if not update_cols:
            stmt = stmt.on_conflict_do_nothing(index_elements=uniqs)
        else:
            stmt = stmt.on_conflict_do_update(index_elements=uniqs, set_=update_cols)
        return stmt


    @overload
    async def update_batch(
        self,
        table: DeclarativeBase,
        data_to_update: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
    ) -> dict[str, int | DataFrame]:
        ...

    @overload
    async def update_batch(
        self,
        table: DeclarativeBase,
        data_to_update: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        session: AsyncSession | None = None,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
    ) -> dict[str, int | DataFrame]:
        ...

    async def update_batch(
        self,
        table: DeclarativeBase,
        data_to_update: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        session: AsyncSession | None = None,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
    ) -> dict[str, int | DataFrame]:
        if not isinstance(data_to_update, DataFrame):
            raise ValueError(f"Invalid data_to_update type: {type(data_to_update)}")

        # df = self._convert_df_for_db(data_to_update, table, try_convert, allow_infinity)
        df = self.convert_df_by_model(data_to_update, table, allow_infinity, deep_copy=True)

        if conflict_cols and not self._is_valid_conflict_cols(conflict_cols, table):
            raise ValueError(f"Invalid conflict columns: {conflict_cols}")

        cnt_rows: int = len(df)
        cnt_cols: int = len(df.columns)
        if cnt_rows == 0:
            return {"cnt_success_rows": 0, "cnt_failed_rows": 0, "df_failed": DataFrame()}
        if cnt_cols == 0:
            raise ValueError("DataFrame has no columns.")

        rows_per_batch: int = max(1, params_per_chunk // cnt_cols)

        if session is not None:
            # 세션 주입시 커밋 허용하지 않음. 이 경우 커밋은 호출부에서
            return await self._update_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit=False)

        async with self.session_maker() as session:
            await self._set_session_schemas(session, schemas)
            try:
                result = await self._update_dataframe_core(table, df, session, rows_per_batch, conflict_cols, partial_commit=partial_commit)
                if not partial_commit:
                    await session.commit()
                return result
            except Exception:
                if not partial_commit:
                    await session.rollback()
                raise


    async def _update_dataframe_core(
        self,
        table: DeclarativeBase,
        df: pd.DataFrame,
        session: AsyncSession,
        rows_per_batch: int,
        conflict_cols: list[str] | None = None,
        partial_commit: bool = True,
    ) -> dict[str, int | DataFrame]:
        cnt_success_rows: int = 0
        cnt_failed_rows: int = 0
        dfs_failed_batch: list[DataFrame] = []
        df_failed: DataFrame = DataFrame()

        for i in range(0, len(df), rows_per_batch):
            df_batch: DataFrame = df.iloc[i:i + rows_per_batch]
            try:
                stmt = self._stmt_update_dataframe(table, df_batch, conflict_cols)
                if stmt is None:
                    cnt_success_rows += len(df_batch)
                    continue

                await session.execute(stmt)
                
                if partial_commit:
                    await session.commit()
                cnt_success_rows += len(df_batch)

            except Exception:
                if partial_commit:
                    cnt_failed_rows += len(df_batch)
                    dfs_failed_batch.append(df_batch)
                    await session.rollback()
                else:
                    raise

        if dfs_failed_batch:
            df_failed = pd.concat(dfs_failed_batch, ignore_index=False)
        return {"cnt_success_rows": cnt_success_rows, "cnt_failed_rows": cnt_failed_rows, "df_failed": df_failed}


    def _stmt_update_dataframe(
        self,
        table: DeclarativeBase,
        df: pd.DataFrame,
        conflict_cols: list[str] | None = None,
    ) -> Executable | None:
        uniqs: list[str] = conflict_cols or self._get_most_suitable_unique_keys(table, df)

        model_columns = [col.name for col in table.__table__.columns]
        df_filtered = df[[col for col in model_columns if col in df.columns]]

        missing_keys = [k for k in uniqs if k not in df_filtered.columns]
        if missing_keys:
            raise ValueError(f"Missing key columns in df: {missing_keys} (keys={uniqs})")

        rows: list[dict] = df_filtered.to_dict(orient="records")
        update_col_names = [c for c in df_filtered.columns if c not in uniqs]
        if not update_col_names:
            return None

        v_cols = uniqs + update_col_names
        t = table.__table__
        v = (
            values(*[t.c[c] for c in v_cols], name="v")
            .data([tuple(r.get(c) for c in v_cols) for r in rows])
            .alias("v")
        )

        where_clause = and_(*[t.c[k] == v.c[k] for k in uniqs])
        set_clause = {c: v.c[c] for c in update_col_names}

        return (
            update(t)
            .where(where_clause)
            .values(**set_clause)
            .execution_options(synchronize_session=False)
        )


    def _get_uniqueness(self, base_model: Type[DeclarativeBase]) -> None:
        """
        DB 내 모든 테이블을 순회하며,
        테이블명: list(유니크키 컬럼 리스트 또는 프라이머리키 컬럼 리스트) 반환
        """
        for _, table in base_model.metadata.tables.items():
            self._get_constraints(table)
            self._get_keys(table)


    def _get_constraints(self, table: Table) -> None:

        unique_constraints: list[list[str]] = []
        primary_constraints: list[list[str]] = []
        foreign_key_constraints: list[list[str]] = []

        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                unique_constraints.append([col.name for col in constraint.columns])
            elif isinstance(constraint, PrimaryKeyConstraint):
                primary_constraints.append([col.name for col in constraint.columns])
            elif isinstance(constraint, ForeignKeyConstraint):
                foreign_key_constraints.append([col.name for col in constraint.columns])

        unique_constraints.sort(key=len, reverse=True)
        primary_constraints.sort(key=len, reverse=True)
        foreign_key_constraints.sort(key=len, reverse=True)
        self.unique_constraints[table.name] = unique_constraints
        self.primary_constraints[table.name] = primary_constraints
        self.foreign_key_constraints[table.name] = foreign_key_constraints


    def _get_keys(self, table: Table) -> None:
        unique_keys: list[str] = []
        primary_keys: list[str] = []
        nullable_columns: list[str] = []
        not_null_columns: list[str] = []
        for col in table.columns:
            if col.unique:
                unique_keys.append(col.name)
            if col.primary_key:
                primary_keys.append(col.name)
            if col.nullable:
                nullable_columns.append(col.name)
            if not col.nullable:
                not_null_columns.append(col.name)
        self.unique_keys[table.name] = unique_keys
        self.primary_keys[table.name] = primary_keys
        self.nullable_columns[table.name] = nullable_columns
        self.not_null_columns[table.name] = not_null_columns


