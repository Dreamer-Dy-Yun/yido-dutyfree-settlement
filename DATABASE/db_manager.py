###########################################
# Module name : models
# Module class : SQLAlchemy ORM Models
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.11.30
# Updated at : 2025.11.30
# Supported by : ChatGPT-4o
# Note : 
# TODO : Steaming용 모듈 작성 고려
############################################
from abc import ABC, abstractmethod
from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase
from typing import TypeVar, Type, Any

TableModel = TypeVar('TableModel', bound=DeclarativeBase)


class DBManager(ABC):
    """
    데이터베이스 관리자 추상 클래스
    
    모든 데이터베이스 구현체(PGDBManager, MySQLManager 등)가 상속받아야 하는
    기본 인터페이스를 정의합니다.
    
    Attributes:
        None (추상 클래스이므로 인스턴스 변수는 구현체에서 정의)
    
    Methods:
        execute_query: SQL 쿼리 실행
        create_tables: 테이블 생성
        drop_tables: 테이블 삭제
        get_uniqueness: 테이블의 유니크 키/프라이머리 키 정보 추출
        _get_unique_columns: 테이블의 유니크 컬럼 추출 (내부 메서드)
        _get_primary_columns: 테이블의 프라이머리 키 컬럼 추출 (내부 메서드)
    """

    @abstractmethod
    async def execute_query(self, query: str | Any, params: dict | list[dict] | None = None) -> Any:
        """
        SQL 쿼리를 실행합니다.
        
        Args:
            query: 실행할 SQL 쿼리 문자열 또는 Executable 객체
            params: 쿼리 파라미터 (딕셔너리 또는 딕셔너리 리스트)
        
        Returns:
            쿼리 실행 결과 (DB별로 다를 수 있음, 일반적으로 SQLAlchemy Result 객체)
        
        Raises:
            DB별 예외 (예: PostgreSQL의 경우 asyncpg 예외)
        """
        pass

    @abstractmethod
    async def create_tables(self) -> None:
        """
        데이터베이스에 모든 테이블을 생성합니다.
        
        Raises:
            DB별 예외
        """
        pass

    @abstractmethod
    async def drop_tables(self) -> None:
        """
        데이터베이스의 모든 테이블을 삭제합니다.
        
        Raises:
            DB별 예외
        """
        pass

    @abstractmethod
    def get_uniqueness(self, base_model: Type[DeclarativeBase]) -> dict[str, list[str]]:
        """
        모든 테이블의 유니크 키 및 프라이머리 키 정보를 추출합니다.
        
        Args:
            base_model: SQLAlchemy DeclarativeBase 모델 클래스
        
        Returns:
            테이블명을 키로, 유니크/프라이머리 키 컬럼 리스트를 값으로 하는 딕셔너리
            예: {"table_name": ["col1", "col2"]}
        """
        pass

    @staticmethod
    @abstractmethod
    def _get_unique_columns(table: Table, unique_cols: list[str] | None = None) -> list[str]:
        """
        테이블의 유니크 제약 조건 컬럼을 추출합니다.
        
        Args:
            table: SQLAlchemy Table 객체
            unique_cols: 이미 찾은 유니크 컬럼 리스트 (있으면 그대로 반환)
        
        Returns:
            유니크 컬럼 이름 리스트
        """
        pass

    @staticmethod
    @abstractmethod
    def _get_primary_columns(table: Table, unique_cols: list[str] | None = None) -> list[str]:
        """
        테이블의 프라이머리 키 컬럼을 추출합니다.
        
        Args:
            table: SQLAlchemy Table 객체
            unique_cols: 이미 찾은 컬럼 리스트 (있으면 그대로 반환)
        
        Returns:
            프라이머리 키 컬럼 이름 리스트
        """
        pass
