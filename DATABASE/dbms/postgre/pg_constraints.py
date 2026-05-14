from __future__ import annotations

import pandas as pd
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, Table, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from typing import TypeAlias, TypeVar


ColumnNames: TypeAlias = list[str]
ConstraintColumns: TypeAlias = list[list[str]]
CacheValue = TypeVar("CacheValue", ColumnNames, ConstraintColumns)


class ConstraintInspectorMixin:
    unique_constraints: dict[str, ConstraintColumns]
    primary_constraints: dict[str, ConstraintColumns]
    foreign_key_constraints: dict[str, ConstraintColumns]
    nullable_columns: dict[str, ColumnNames]
    not_null_columns: dict[str, ColumnNames]
    unique_keys: dict[str, ColumnNames]
    primary_keys: dict[str, ColumnNames]

    @staticmethod
    def _table_key(table_or_model: Table | type[DeclarativeBase]) -> str:
        table = table_or_model.__table__ if hasattr(table_or_model, "__table__") else table_or_model
        return f"{table.schema}.{table.name}" if table.schema else table.name

    def _table_cache_values(
        self,
        store: dict[str, CacheValue],
        table: Table | type[DeclarativeBase],
        default: CacheValue,
    ) -> CacheValue:
        key = self._table_key(table)
        if key in store:
            return store[key]
        table_obj = table.__table__ if hasattr(table, "__table__") else table
        return store.get(table_obj.name, default)

    def _contains_all_not_nullable_cols(self, cols: list[str], table: type[DeclarativeBase]) -> bool:
        not_nullable_cols = self._table_cache_values(self.not_null_columns, table, [])
        return all(col in cols for col in not_nullable_cols)

    def _is_valid_conflict_cols(self, conflict_cols: list[str], table: type[DeclarativeBase]) -> bool:
        candidates: list[list[str]] = []
        candidates.extend(self._table_cache_values(self.unique_constraints, table, []))
        candidates.extend(self._table_cache_values(self.primary_constraints, table, []))
        candidates.extend([[c] for c in self._table_cache_values(self.unique_keys, table, [])])
        candidates.extend([[c] for c in self._table_cache_values(self.primary_keys, table, [])])

        target = set(conflict_cols)
        return any(set(candidate) == target for candidate in candidates)

    def _get_most_suitable_unique_keys(self, table: type[DeclarativeBase], df: pd.DataFrame) -> list[str]:
        table_name = table.__table__.name
        cols_df = set(df.columns)
        ucs = self._table_cache_values(self.unique_constraints, table, [])
        pcs = self._table_cache_values(self.primary_constraints, table, [])
        uks = self._table_cache_values(self.unique_keys, table, [])
        pks = self._table_cache_values(self.primary_keys, table, [])

        if not (ucs or pcs or uks or pks):
            raise ValueError(f"Can't find suitable PK/UK in {table_name}")

        for keys in ucs:
            if all(col in cols_df for col in keys):
                return keys
        for keys in pcs:
            if all(col in cols_df for col in keys):
                return keys
        for key in uks:
            if key in cols_df:
                return [key]
        for key in pks:
            if key in cols_df:
                return [key]

        raise ValueError(
            f"Missing required PK/UK/Constraint columns in DataFrame for table '{table_name}'. "
            f"Required columns (candidates): unique_constraints={ucs}, "
            f"primary_constraints={pcs}, unique_keys={uks}, primary_keys={pks}. "
            f"Available columns: {list(df.columns)}"
        )

    def _get_uniqueness(self, base_model: type[DeclarativeBase]) -> None:
        for table in base_model.metadata.tables.values():
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
        self._store_table_cache(self.unique_constraints, table, unique_constraints)
        self._store_table_cache(self.primary_constraints, table, primary_constraints)
        self._store_table_cache(self.foreign_key_constraints, table, foreign_key_constraints)

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
            else:
                not_null_columns.append(col.name)

        self._store_table_cache(self.unique_keys, table, unique_keys)
        self._store_table_cache(self.primary_keys, table, primary_keys)
        self._store_table_cache(self.nullable_columns, table, nullable_columns)
        self._store_table_cache(self.not_null_columns, table, not_null_columns)

    def _store_table_cache(self, store: dict[str, CacheValue], table: Table, value: CacheValue) -> None:
        store[self._table_key(table)] = value
        store.setdefault(table.name, value)
