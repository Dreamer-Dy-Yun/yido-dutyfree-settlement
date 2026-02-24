###########################################
# Module name : models
# Module class : SQLAlchemy ORM Models
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
#       2025.11.07 : PGDBManager.upsert_dataframe() 수정(불필요한 컬럼 제거)(롤백하면서 제거된 로직 복구)
#       2025.11.22 : PGDBManager.initialize_engine() 수정(pool_size, max_overflow 추가)
#       2025.11.30 : DBManager 추상 클래스 추가 및 상속
#       2026.02.19 : PGDBManager.set_schema() 등 스키마 관련 메서드 추가 (멀티 테넌트 대응)
#       2026.02.20 : 컨텍스트 매니저 수정
#       2026.02.23 : PGDBManager.create_tables() 수정(스키마 명시적 지정 가능)
#                    PGDBManager.copy_tables_of_schema() 추가 (스키마 복사 기능 추가. supported by ChatGPT-5.3)
#       2026.02.24 : PGDBManager._get_most_suitable_unique_keys() 추가 및 피영향 메서드 수정
# TODO : Steaming용 모듈 작성 고려
############################################
import urllib

from numpy._core.strings import str_len
from DATABASE.dbms import DBManager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy import Table, text, UniqueConstraint, Column, PrimaryKeyConstraint, ForeignKeyConstraint
from sqlalchemy.sql import quoted_name
from sqlalchemy.orm import sessionmaker, DeclarativeBase, strategies
from sqlalchemy.schema import AddConstraint
from typing import Type, TypeVar, Optional, AsyncContextManager, Self
from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.elements import ColumnElement, Executable
import asyncpg
import asyncio
import numpy as np
import pandas as pd
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
        self.unique_keys: dict[str, list[str]] = {}
        self.primary_keys: dict[str, list[str]] = {}
        self._get_uniqueness(self.base_model)
        self.base_fields: dict = {key : val for key, val in vars(self.base_model).items() if isinstance(val, Column)}
        self.schemas: list[str] | None = None


    async def set_schemas(self, schemas: list[str] | None = None) -> Self:
        """
        스키마 설정 (search_path 변경)
        
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


    async def _set_session_schemas(self, session: AsyncSession) -> None:
        """세션에 스키마 설정 (헬퍼 메서드)"""
        if self.schemas:
            # quoted_name을 사용하여 식별자 안전하게 처리
            schema_list = ", ".join([str(quoted_name(s, quote=True)) for s in self.schemas])
            await session.execute(text(f"SET search_path TO {schema_list}"))


    async def get_all_schemas(self) -> list[str]:
        """DB에 등록된 모든 스키마 목록 조회"""
        result = await self.execute_query(text("SELECT nspname FROM pg_namespace ORDER BY nspname"))
        schemas = [row[0] for row in result.fetchall()]
        return schemas
 

    async def __aenter__(self) -> AsyncSession:
        self._session_cm = self.session_maker()  
        self.session = await self._session_cm.__aenter__()
        
        try:
            await self._set_session_schemas(self.session)
            return self.session
        except Exception:
            # 스키마 설정 실패 시 세션 정리
            await self._session_cm.__aexit__(None, None, None)
            raise


    async def __aexit__(self, exc_type, exc, tb) -> bool: # 변경후 검증 안됨
        try:
            if self._session_cm is not None:
                await self._session_cm.__aexit__(exc_type, exc, tb)
        finally:
            self.session = None
            self._session_cm = None


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


    async def create_tables(self, schema: str | None = None) -> int:
        """
        테이블 생성
        
        Args:
            schema: 특정 스키마의 테이블만 생성 (None이면 모든 테이블 생성)
                    예: "public" → public 스키마 테이블만 생성
        """
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


    async def dispose_pool(self) -> None:
        """연결 풀 해제."""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("✅Connection pool disposed.")


    async def execute_query(self, query: str | Executable, params: dict | list[dict] | None = None):
        """비동기 ORM 세션 사용 쿼리 실행"""
        async with self.session_maker() as session:
            try:
                await self._set_session_schemas(session)
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


    async def batch_upsert_dataframe(self, table: DeclarativeBase, df: DataFrame, allowed_param_size: int = 10000) -> int:
        # TODO : Copy / executemany 등을 이용한 최적화 시도 (필요시)
        # TODO : 배치 크기 최적화 시도 (바인딩 개수 계산 방법 확인 필요)
        
        cnt_rows: int = len(df)
        cnt_cols: int = len(df.columns)

        if cnt_rows == 0:
            return 0

        number_of_rows_for_one_request: int = allowed_param_size // cnt_cols

        cnt_upserted: int = 0

        for i in range(0, cnt_rows, number_of_rows_for_one_request):
            df_batch: DataFrame = df.iloc[i:i+number_of_rows_for_one_request]
            cnt_upserted += await self.upsert_dataframe(table, df_batch)

        return cnt_upserted


    @staticmethod
    def normalize_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        for col in result.columns:
            if np.issubdtype(result[col].dtype, np.datetime64):
                # 일단 datetime으로 강제 파싱
                result[col] = pd.to_datetime(result[col], errors="coerce")

                # datetime → object로 변경
                result[col] = result[col].astype("object")

                # NaT → None
                result.loc[result[col].isna(), col] = None
        return result


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


    async def upsert_dataframe(self, table: DeclarativeBase, df: pd.DataFrame, conflict_cols: list[str] | None = None, try_normalize: bool = True) -> int:
        '''
        자동 Upserter.
        가용한 모든 df(DataFrame)컬럼 업데이트.
            - df(DataFrame)에는 table 의 아래 중 하나를 만족하는 컬럼이 존재하여야 함 (유니크 제약이 우선임에 유의)
              - UniqueConstraint 
              - PrimaryKeyConstraint
              - UniqueKey
              - PrimaryKey
            - Key나 Constraint 를 제외한 모든 컬럼이 양쪽에 존재할 필요는 없음 
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
        # 항상 그렇듯 극한 성능 필요하면 언어 변경 및 SQL 수기 작성 필요
        
        if try_normalize:
            # Datetime 컬럼을 모두 object로 변환하여 NaT를 None으로 변환 
            df = self.normalize_datetime_columns(df)

        async with self.session_maker() as session:
            await self._set_session_schemas(session)
            try:
                # logger.info(f"🚀 START [upsert_dataframe]")

                if conflict_cols and not self._is_valid_conflict_cols(conflict_cols, table):
                    raise ValueError(f"Invalid conflict columns: {conflict_cols}")
                
                uniqs: list[str] = conflict_cols or self._get_most_suitable_unique_keys(table, df)

                # 모델에 정의된 컬럼만 선택 (불필요한 컬럼 제거)
                model_columns = [col.name for col in table.__table__.columns]
                df_filtered = df[[col for col in model_columns if col in df.columns]]
                
                rows: list[dict] = df_filtered.to_dict(orient="records")

                stmt: Insert = insert(table).values(rows)
                ce: ColumnElement = stmt.excluded

                update_cols = {c: getattr(ce, c) for c in df_filtered.columns if hasattr(ce, c)}

                # 키/유니크 값만 있는 경우: conflict 시 아무것도 하지 않음 (insert만 수행)
                if not update_cols:
                    stmt = stmt.on_conflict_do_nothing(index_elements=uniqs)
                else:
                    stmt = stmt.on_conflict_do_update(index_elements=uniqs, set_=update_cols)

                # if update_cols:
                #     logger.info(f"⏫ UPSERT {table_name} rows={len(rows)} keys={uniqs} set={list(update_cols.keys())}")
                # else:
                #     logger.info(f"⏫ INSERT {table_name} rows={len(rows)} keys={uniqs} (no update columns)")
                await session.execute(stmt)
                await session.commit()

                return len(rows)

            except Exception as e:
                await session.rollback()
                logger.exception(f"❌ UPSERT 실패 @ {table.__tablename__} | 이유: {str(e)}")
                raise


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
        for col in table.columns:
            if col.unique:
                unique_keys.append(col.name)
            if col.primary_key:
                primary_keys.append(col.name)
        self.unique_keys[table.name] = unique_keys
        self.primary_keys[table.name] = primary_keys


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
            to_schema : str = str(quoted_name(schema_to_make, quote=True))
            await conn.execute(text(f"CREATE SCHEMA {to_schema}"))

            query : str = f"SET search_path TO {to_schema}"
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
