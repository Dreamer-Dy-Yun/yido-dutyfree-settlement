from __future__ import annotations

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import dialect


_PREPARER = dialect().identifier_preparer


def quote_identifier(name: str) -> str:
    """Return a PostgreSQL-safe SQL identifier."""
    if not isinstance(name, str):
        raise TypeError(f"Identifier must be str, got {type(name)!r}")
    if not name:
        raise ValueError("Identifier must not be empty.")
    if "\x00" in name:
        raise ValueError("Identifier must not contain null bytes.")
    return _PREPARER.quote(name)


def quote_table(table: Table) -> str:
    """Return a schema-qualified PostgreSQL table identifier when possible."""
    table_name = quote_identifier(table.name)
    if table.schema:
        return f"{quote_identifier(table.schema)}.{table_name}"
    return table_name


def quote_search_path(schemas: list[str] | tuple[str, ...]) -> str:
    if not schemas:
        raise ValueError("Search path must contain at least one schema.")
    return ", ".join(quote_identifier(schema) for schema in schemas)
