"""
PGDBManager._get_most_suitable_unique_keys() / _is_valid_conflict_cols() 전용 유닛 테스트.

- 실제 DB 연결 없이 SQLAlchemy 메타데이터 + pandas DataFrame만으로 동작
- PGDBManager.__init__ 에서 _get_uniqueness()를 호출해 유니크/PK 정보 캐싱
"""

from typing import Optional

import pandas as pd
import pytest
from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from DATABASE.dbms.postgre.pg_manager import PGDBManager


# === 1) 테스트용 Base & 모델 정의 =========================================


class OrmTestBase(DeclarativeBase):
    """테스트 전용 DeclarativeBase"""

    pass


class TableWithUC(OrmTestBase):
    """
    다중 UniqueConstraint(a, b) + PK(id)
    → DataFrame에 a, b가 둘 다 있으면 UC가 우선적으로 선택되어야 함
    """

    __tablename__ = "table_with_uc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    a: Mapped[str] = mapped_column(String(50))
    b: Mapped[str] = mapped_column(String(50))

    __table_args__ = (UniqueConstraint("a", "b", name="uq_a_b"),)


class TableWithCompositePK(OrmTestBase):
    """
    복합 PrimaryKeyConstraint(x, y)
    → UC가 없고, DataFrame에 x, y가 둘 다 있으면 PK 리스트가 선택되어야 함
    """

    __tablename__ = "table_with_composite_pk"

    x: Mapped[int] = mapped_column(Integer, primary_key=True)
    y: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[str] = mapped_column(String(50))


class TableWithUniqueColumn(OrmTestBase):
    """
    단일 unique=True 컬럼(unique_col) + PK(id)
    → UC/복합PK가 없고, DataFrame에 unique_col이 있으면 [\"unique_col\"] 선택
    """

    __tablename__ = "table_with_unique_column"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unique_col: Mapped[str] = mapped_column(String(50), unique=True)
    normal: Mapped[str] = mapped_column(String(50))


class TableWithSimplePK(OrmTestBase):
    """
    단일 PK(id)만 있는 경우
    → UC/복합PK/unique 컬럼이 없고, DataFrame에 id가 있으면 [\"id\"] 선택
    """

    __tablename__ = "table_with_simple_pk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


class TableWithoutAnyUnique(OrmTestBase):
    """
    SQLAlchemy ORM은 최소 한 개의 PK가 필요하므로,
    여기서는 형식상 PK(id) 하나만 두고, 테스트 시점에
    PGDBManager가 가진 unique/primary 관련 캐시를 강제로 비워서
    \"유니크 정보가 전혀 없는 테이블\" 상황을 시뮬레이션한다.
    """

    __tablename__ = "table_without_any_unique"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    col1: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    col2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


# === 2) 공통 PGDBManager 생성 헬퍼 =======================================


def make_manager() -> PGDBManager:
    """
    OrmTestBase 메타데이터를 이용하는 PGDBManager 생성.

    - test_mode=False 로 두어 실제 DB 엔진은 만들지 않음
    - __init__ 내부에서 _get_uniqueness()가 호출되며,
      위에서 정의한 테스트 테이블들의 제약/키 정보가 캐싱됨
    """

    return PGDBManager(
        base_model=OrmTestBase,
        db_name="dummy_db",
        user="dummy",
        password="dummy",
        host="localhost",
        port=5432,
        test_mode=False,  # 엔진/세션 안 만듦 (DB 연결 X)
    )


# === 3) _get_most_suitable_unique_keys() 케이스별 테스트 ==================


def test_choose_unique_constraint_first():
    """
    DataFrame이 UniqueConstraint(a, b)를 모두 포함하면
    → [\"a\", \"b\"] 를 우선 선택해야 함
    """

    mgr = make_manager()
    df = pd.DataFrame([{"a": "A1", "b": "B1", "id": 1}])

    keys = mgr._get_most_suitable_unique_keys(TableWithUC, df)

    assert keys == ["a", "b"]


def test_choose_composite_pk_when_no_uc():
    """
    UniqueConstraint가 없고,
    DataFrame이 복합 PK(x, y)를 모두 포함하면
    → [\"x\", \"y\"] 선택
    """

    mgr = make_manager()
    df = pd.DataFrame([{"x": 10, "y": 20, "value": "v"}])

    keys = mgr._get_most_suitable_unique_keys(TableWithCompositePK, df)

    assert keys == ["x", "y"]


def test_choose_unique_column_when_no_uc_and_composite_pk():
    """
    UC/복합PK가 없고,
    DataFrame에 unique=True 컬럼(unique_col)이 들어 있으면
    → [\"unique_col\"] 선택
    """

    mgr = make_manager()
    df = pd.DataFrame([{"id": 1, "unique_col": "U1", "normal": "N1"}])

    keys = mgr._get_most_suitable_unique_keys(TableWithUniqueColumn, df)

    assert keys == ["unique_col"]


def test_choose_simple_pk_as_fallback():
    """
    UC/복합PK/unique 컬럼이 모두 조건에 안 맞고,
    DataFrame에 PK(id)만 존재하는 경우
    → [\"id\"] 선택
    """

    mgr = make_manager()
    df = pd.DataFrame([{"id": 123, "name": "test"}])

    keys = mgr._get_most_suitable_unique_keys(TableWithSimplePK, df)

    assert keys == ["id"]


def test_raise_when_required_columns_missing():
    """
    UC/PK/unique/PK 정보는 있으나,
    DataFrame에 그 중 어떤 조합도 만족하지 못하면
    → ValueError + 친절한 메시지
    """

    mgr = make_manager()
    # TableWithUC: UC(a, b), PK(id) 가 있지만, df에는 'a'만 있음 (b, id 없음)
    df = pd.DataFrame([{"a": "only_a"}])

    with pytest.raises(ValueError) as exc:
        mgr._get_most_suitable_unique_keys(TableWithUC, df)

    msg = str(exc.value)
    assert "Missing required PK/UK/Constraint columns" in msg
    assert "table 'table_with_uc'" in msg


def test_raise_when_no_unique_info_at_all():
    """
    테이블에 PK/UK/Constraint 정보가 전혀 없는 경우
    → \"Can't find suitable PK/UK in ...\" 에러
    """

    mgr = make_manager()

    # TableWithoutAnyUnique 에 대해서는, 매니저가 캐싱한
    # unique / primary 관련 정보를 모두 제거해
    # \"유니크 정보 전혀 없음\" 상태를 강제로 만든다.
    tbl_name = TableWithoutAnyUnique.__table__.name
    mgr.unique_constraints[tbl_name] = []
    mgr.primary_constraints[tbl_name] = []
    mgr.unique_keys[tbl_name] = []
    mgr.primary_keys[tbl_name] = []

    df = pd.DataFrame([{"col1": "v1", "col2": "v2"}])

    with pytest.raises(ValueError) as exc:
        mgr._get_most_suitable_unique_keys(TableWithoutAnyUnique, df)

    assert "Can't find suitable PK/UK in table_without_any_unique" in str(exc.value)


# === 4) _is_valid_conflict_cols() 테스트 ===================================


def test_is_valid_conflict_cols_true_for_uc():
    mgr = make_manager()
    valid = mgr._is_valid_conflict_cols(["a", "b"], TableWithUC)
    assert valid is True


def test_is_valid_conflict_cols_true_for_unique_col():
    mgr = make_manager()
    valid = mgr._is_valid_conflict_cols(["unique_col"], TableWithUniqueColumn)
    assert valid is True


def test_is_valid_conflict_cols_true_for_pk():
    mgr = make_manager()
    valid = mgr._is_valid_conflict_cols(["id"], TableWithSimplePK)
    assert valid is True


def test_is_valid_conflict_cols_false_for_invalid_combo():
    mgr = make_manager()
    # 존재하지 않는 조합
    valid = mgr._is_valid_conflict_cols(["a", "non_existing"], TableWithUC)
    assert valid is False

