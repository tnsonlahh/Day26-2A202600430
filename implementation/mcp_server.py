from __future__ import annotations

import json
from functools import wraps
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

try:
    from .db import SQLiteAdapter, ValidationError
    from .init_db import DB_PATH, create_database
except ImportError:
    from db import SQLiteAdapter, ValidationError
    from init_db import DB_PATH, create_database


if not Path(DB_PATH).exists():
    create_database(DB_PATH)

adapter = SQLiteAdapter(DB_PATH)
mcp = FastMCP("SQLite Lab MCP Server")


def _handle_validation_error(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValidationError as exc:
            return {"ok": False, "error": str(exc)}

    return wrapper


@mcp.tool(name="search")
@_handle_validation_error
def search(
    table: str,
    filters: list[dict[str, Any]] | dict[str, Any] | None = None,
    columns: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict[str, Any]:
    """Search rows with optional filters, ordering, and pagination."""
    result = adapter.search(table, columns, filters, limit, offset, order_by, descending)
    return {"ok": True, **result}


@mcp.tool(name="insert")
@_handle_validation_error
def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Insert one row into a validated table and return the inserted payload."""
    result = adapter.insert(table, values)
    return {"ok": True, **result}


@mcp.tool(name="aggregate")
@_handle_validation_error
def aggregate(
    table: str,
    metric: str,
    column: str | None = None,
    filters: list[dict[str, Any]] | dict[str, Any] | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Run count, avg, sum, min, or max with optional filters and grouping."""
    result = adapter.aggregate(table, metric, column, filters, group_by)
    return {"ok": True, **result}


@mcp.resource("schema://database")
def database_schema() -> str:
    """Return a JSON snapshot of the full database schema."""
    return json.dumps(adapter.get_database_schema(), indent=2)


@mcp.resource("schema://table/{table_name}")
def table_schema(table_name: str) -> str:
    """Return a JSON schema description for one table."""
    try:
        payload = adapter.get_table_schema(table_name)
    except ValidationError as exc:
        payload = {"ok": False, "error": str(exc)}
    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    mcp.run()
