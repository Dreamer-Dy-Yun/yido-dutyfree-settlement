from typing import Optional

import pandas as pd
import pytest
from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from DATABASE.dbms.postgre.pg_manager import PGDBManager


class OrmTestBase(DeclarativeBase):
    pass


class TableWithUC(OrmTestBase):
    __tablename__ = "table_with_uc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    a: Mapped[str] = mapped_column(String(50))
    b: Mapped[str] = mapped_column(String(50))

    __table_args__ = (UniqueConstraint("a", "b", name="uq_a_b"),)


class TableWithCompositePK(OrmTestBase):
    __tablename__ = "table_with_composite_pk"

    x: Mapped[int] = mapped_column(Integer, primary_key=True)
    y: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[str] = mapped_column(String(50))


class TableWithUniqueColumn(OrmTestBase):
    __tablename__ = "table_with_unique_column"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unique_col: Mapped[str] = mapped_column(String(50), unique=True)
    normal: Mapped[str] = mapped_column(String(50))


class TableWithSimplePK(OrmTestBase):
    __tablename__ = "table_with_simple_pk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


class TableWithoutAnyUnique(OrmTestBase):
    __tablename__ = "table_without_any_unique"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    col1: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    col2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


def make_manager() -> PGDBManager:
    """Build only the PGDBManager metadata cache without opening a DB engine."""
    mgr = PGDBManager.__new__(PGDBManager)
    mgr.base_model = OrmTestBase
    mgr.unique_constraints = {}
    mgr.primary_constraints = {}
    mgr.foreign_key_constraints = {}
    mgr.nullable_columns = {}
    mgr.not_null_columns = {}
    mgr.unique_keys = {}
    mgr.primary_keys = {}
    mgr._get_uniqueness(OrmTestBase)
    return mgr


def test_choose_unique_constraint_first():
    mgr = make_manager()
    df = pd.DataFrame([{"a": "A1", "b": "B1", "id": 1}])

    keys = mgr._get_most_suitable_unique_keys(TableWithUC, df)

    assert keys == ["a", "b"]


def test_choose_composite_pk_when_no_uc():
    mgr = make_manager()
    df = pd.DataFrame([{"x": 10, "y": 20, "value": "v"}])

    keys = mgr._get_most_suitable_unique_keys(TableWithCompositePK, df)

    assert keys == ["x", "y"]


def test_choose_unique_column_when_no_uc_and_composite_pk():
    mgr = make_manager()
    df = pd.DataFrame([{"id": 1, "unique_col": "U1", "normal": "N1"}])

    keys = mgr._get_most_suitable_unique_keys(TableWithUniqueColumn, df)

    assert keys == ["unique_col"]


def test_choose_simple_pk_as_fallback():
    mgr = make_manager()
    df = pd.DataFrame([{"id": 123, "name": "test"}])

    keys = mgr._get_most_suitable_unique_keys(TableWithSimplePK, df)

    assert keys == ["id"]


def test_raise_when_required_columns_missing():
    mgr = make_manager()
    df = pd.DataFrame([{"a": "only_a"}])

    with pytest.raises(ValueError) as exc:
        mgr._get_most_suitable_unique_keys(TableWithUC, df)

    msg = str(exc.value)
    assert "Missing required PK/UK/Constraint columns" in msg
    assert "table 'table_with_uc'" in msg


def test_raise_when_no_unique_info_at_all():
    mgr = make_manager()
    tbl_name = TableWithoutAnyUnique.__table__.name
    mgr.unique_constraints[tbl_name] = []
    mgr.primary_constraints[tbl_name] = []
    mgr.unique_keys[tbl_name] = []
    mgr.primary_keys[tbl_name] = []

    df = pd.DataFrame([{"col1": "v1", "col2": "v2"}])

    with pytest.raises(ValueError) as exc:
        mgr._get_most_suitable_unique_keys(TableWithoutAnyUnique, df)

    assert "Can't find suitable PK/UK in table_without_any_unique" in str(exc.value)


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
    valid = mgr._is_valid_conflict_cols(["a", "non_existing"], TableWithUC)

    assert valid is False
