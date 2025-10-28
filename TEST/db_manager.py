from CUSTOMIZED.cust_logger import logger
import urllib 
from sqlalchemy import create_engine, engine, Table, text
from pandas import DataFrame
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from typing import Type, TypeVar

TableModel = TypeVar('TableModel', bound=DeclarativeBase)

class PGDBManager:
    """Postgre 전용"""
    pg_engine: engine.Engine = None
    session_maker: sessionmaker = None
    base_model: Type[DeclarativeBase] = None  

    def __init__(self, base_model: Type[DeclarativeBase], dbname: str, user: str, password: str, host: str, port: int = 5432):
        self.initialize_engine(dbname, user, password, host, port)
        self.session: Session = PGDBManager.session_maker()  
        self.uniqueness: dict = self.get_uniqueness(base_model)
        PGDBManager.base_model = base_model

    @classmethod
    def initialize_engine(cls, dbname: str, user: str, password: str, host: str, port: int = 5432):
        if cls.pg_engine is None:
            pw: str = urllib.parse.quote_plus(password)
            uri: str = f"postgresql://{user}:{pw}@{host}:{str(port)}/{dbname}"
            cls.pg_engine = create_engine(uri, echo=True)
            cls.session_maker = sessionmaker(bind=cls.pg_engine) 

    @classmethod
    def create_tables(cls):
        cls.base_model.metadata.create_all(bind=cls.pg_engine)  
        logger.info("✅All tables are CREATED.")

    @classmethod
    def drop_tables(cls):
        cls.base_model.metadata.drop_all(bind=cls.pg_engine)  
        logger.info("✅All tables are REMOVED.")

    def execute_query(self, query: str):
        """ORM 세션을 사용해서 쿼리 실행"""
        try:
            result = self.session.execute(text(query))
            return result
        except Exception as e:
            self.session.rollback()
            logger.exception(f"Query execution error: {str(e)}")
            raise e

    def upsert_dataframe(self, table: Type[TableModel], df: DataFrame, db_session: Session):
        """
        DataFrame을 받아서 지정된 테이블에 upsert 수행.

        유효한 컬럼명은 DataFrame에서 사전에 맞추어 두어야 함.
        """
        try:
            for _, row in df.iterrows():
                row_dict = {col: row.get(col) for col in row.index if row.get(col) is not None}
                rec = table(**row_dict)
                db_session.merge(rec)

            db_session.flush()
            db_session.commit()
            
        except Exception as e:
            db_session.rollback()
            logger.exception(f"❌ An error occurred: {str(e)}")
            raise e

    def get_uniqueness(self, base_model: Type[DeclarativeBase]) -> dict:
        """
        DB 내 모든 테이블을 순회하며,
        테이블명: list(유니크키 컬럼 리스트 또는 프라이머리키 컬럼 리스트) 
        반환
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
    def _get_unique_columns(table: Table, unique_cols: list = []) -> list:
        if not unique_cols:
            return unique_cols

        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                unique_cols = [col.name for col in constraint.columns]
                break
        return unique_cols

    @staticmethod
    def _get_primary_columns(table: Table, unique_cols: list = []) -> list:
        if not unique_cols:
            return unique_cols
        
        return [col.name for col in table.primary_key.columns]
        