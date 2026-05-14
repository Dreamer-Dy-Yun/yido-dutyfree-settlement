from __future__ import annotations

from typing import TYPE_CHECKING, Any

from DATABASE.dbms.postgre.pg_batch import PGBatchWriter
from DATABASE.dbms.postgre.pg_batch_executor import PGBatchExecutor
from DATABASE.dbms.postgre.pg_constraints import PGConstraintInspector
from DATABASE.dbms.postgre.pg_dataframe import PGDataFrameConverter
from DATABASE.dbms.postgre.pg_schema import PGSchemaManager

if TYPE_CHECKING:
    from DATABASE.dbms.postgre.pg_manager import PGDBManager


CONSTRAINT_CACHE_NAMES = (
    "unique_constraints",
    "primary_constraints",
    "foreign_key_constraints",
    "nullable_columns",
    "not_null_columns",
    "unique_keys",
    "primary_keys",
)
SCHEMA_METHODS = frozenset((
    "set_schemas",
    "exist_schemas",
    "exists_schema",
    "create_schema",
    "drop_schema",
    "_set_session_schemas",
    "get_all_schemas",
    "copy_tables_of_schema",
    "truncate_table",
    "_filter_tables_by_schema",
    "_schema_exists",
))
BATCH_METHODS = frozenset((
    "_upsert_dataframe",
    "_upsert_dataframe_core",
    "_update_dataframe_core",
    "_execute_upsert_batches",
    "_execute_update_batches",
    "_build_upsert_statement",
    "_stmt_upsert_dataframe",
    "_build_update_statement",
    "_stmt_update_dataframe",
    "_filter_model_columns",
))
CONVERTER_METHODS = frozenset((
    "convert_df_by_model",
    "convert_string_cols_by_model",
    "_convert_df_for_db",
    "_convert_series_by_column",
    "_fix_cols_string",
    "_fix_cols_integer",
    "_fix_cols_float",
    "_fix_cols_datetime",
    "_fix_cols_date",
    "_fix_cols_time",
    "_fix_cols_boolean",
    "_fix_cols_json",
    "_to_decimal",
))
CONSTRAINT_METHODS = frozenset((
    "_table_key",
    "_table_cache_values",
    "_contains_all_not_nullable_cols",
    "_is_valid_conflict_cols",
    "_get_most_suitable_unique_keys",
    "_get_uniqueness",
    "_get_constraints",
    "_get_keys",
    "_store_table_cache",
))


class PGManagerComponents:
    def __init__(self, manager: PGDBManager) -> None:
        self.manager = manager
        self.converter = PGDataFrameConverter()
        self.constraints = PGConstraintInspector(
            unique_constraints=manager.__dict__.get("unique_constraints"),
            primary_constraints=manager.__dict__.get("primary_constraints"),
            foreign_key_constraints=manager.__dict__.get("foreign_key_constraints"),
            nullable_columns=manager.__dict__.get("nullable_columns"),
            not_null_columns=manager.__dict__.get("not_null_columns"),
            unique_keys=manager.__dict__.get("unique_keys"),
            primary_keys=manager.__dict__.get("primary_keys"),
        )
        self.batch_executor = PGBatchExecutor()
        self.schema_manager = PGSchemaManager(manager)
        self.batch_writer = PGBatchWriter(manager, self.converter, self.constraints, self.batch_executor)
        self.sync_constraint_cache_refs()

    def sync_constraint_cache_refs(self) -> None:
        for name in CONSTRAINT_CACHE_NAMES:
            setattr(self.manager, name, getattr(self.constraints, name))

    def resolve(self, name: str) -> Any:
        if name in SCHEMA_METHODS:
            return getattr(self.schema_manager, name)
        if name in BATCH_METHODS:
            return getattr(self.batch_writer, name)
        if name == "_execute_batches":
            return self.batch_executor.execute_batches
        if name in CONVERTER_METHODS:
            return getattr(self.converter, name)
        if name in CONSTRAINT_METHODS:
            self._bind_manager_constraint_refs()
            return getattr(self.constraints, name)
        raise AttributeError(f"PGDBManager object has no attribute {name!r}")

    def _bind_manager_constraint_refs(self) -> None:
        for name in CONSTRAINT_CACHE_NAMES:
            if name in self.manager.__dict__:
                setattr(self.constraints, name, self.manager.__dict__[name])
        self.sync_constraint_cache_refs()


__all__ = ["PGManagerComponents"]
