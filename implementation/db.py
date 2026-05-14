from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


SUPPORTED_OPERATORS = {
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
}

SUPPORTED_METRICS = {"count", "avg", "sum", "min", "max"}


class SQLiteAdapter:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = OFF")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def list_tables(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> dict[str, Any]:
        self._validate_table(table)
        with self.connect() as conn:
            columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            foreign_keys = conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
        return {
            "table": table,
            "columns": [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "not_null": bool(row["notnull"]),
                    "default": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
                for row in columns
            ],
            "foreign_keys": [
                {
                    "column": row["from"],
                    "references_table": row["table"],
                    "references_column": row["to"],
                }
                for row in foreign_keys
            ],
        }

    def get_database_schema(self) -> dict[str, Any]:
        return {
            "database": str(self.db_path),
            "tables": {table: self.get_table_schema(table) for table in self.list_tables()},
        }

    def search(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: list[dict[str, Any]] | dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        table_columns = self._validate_table(table)
        selected_columns = self._validate_columns(table_columns, columns)
        where_sql, params = self._build_filters(table_columns, filters)
        limit, offset = self._validate_pagination(limit, offset)

        sql = f'SELECT {", ".join(selected_columns)} FROM "{table}"'
        if where_sql:
            sql += f" WHERE {where_sql}"
        if order_by:
            self._validate_column(table_columns, order_by)
            direction = "DESC" if descending else "ASC"
            sql += f' ORDER BY "{order_by}" {direction}'
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return {
            "table": table,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
            "limit": limit,
            "offset": offset,
        }

    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        table_columns = self._validate_table(table)
        if not values:
            raise ValidationError("Insert values cannot be empty.")
        for column in values:
            self._validate_column(table_columns, column)

        column_sql = ", ".join(f'"{column}"' for column in values)
        placeholders = ", ".join("?" for _ in values)
        sql = f'INSERT INTO "{table}" ({column_sql}) VALUES ({placeholders})'

        with self.connect() as conn:
            cursor = conn.execute(sql, list(values.values()))
            conn.commit()
            inserted = dict(values)
            if "id" in table_columns and "id" not in inserted:
                inserted["id"] = cursor.lastrowid

        return {"table": table, "inserted": inserted}

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: list[dict[str, Any]] | dict[str, Any] | None = None,
        group_by: str | None = None,
    ) -> dict[str, Any]:
        table_columns = self._validate_table(table)
        metric = metric.lower()
        if metric not in SUPPORTED_METRICS:
            raise ValidationError(f"Unsupported aggregate metric: {metric}.")
        if metric == "count":
            aggregate_expr = "COUNT(*)"
        else:
            if not column:
                raise ValidationError(f"Metric '{metric}' requires a column.")
            self._validate_column(table_columns, column)
            aggregate_expr = f'{metric.upper()}("{column}")'

        select_parts = []
        if group_by:
            self._validate_column(table_columns, group_by)
            select_parts.append(f'"{group_by}" AS group_value')
        select_parts.append(f"{aggregate_expr} AS value")

        where_sql, params = self._build_filters(table_columns, filters)
        sql = f'SELECT {", ".join(select_parts)} FROM "{table}"'
        if where_sql:
            sql += f" WHERE {where_sql}"
        if group_by:
            sql += f' GROUP BY "{group_by}" ORDER BY "{group_by}"'

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return {
            "table": table,
            "metric": metric,
            "column": column,
            "group_by": group_by,
            "rows": [dict(row) for row in rows],
        }

    def _validate_table(self, table: str) -> set[str]:
        if table not in self.list_tables():
            raise ValidationError(f"Unknown table: {table}.")
        with self.connect() as conn:
            rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        return {row["name"] for row in rows}

    def _validate_columns(self, table_columns: set[str], columns: list[str] | None) -> list[str]:
        if not columns:
            return [f'"{column}"' for column in sorted(table_columns)]
        for column in columns:
            self._validate_column(table_columns, column)
        return [f'"{column}"' for column in columns]

    def _validate_column(self, table_columns: set[str], column: str) -> None:
        if column not in table_columns:
            raise ValidationError(f"Unknown column: {column}.")

    def _build_filters(
        self,
        table_columns: set[str],
        filters: list[dict[str, Any]] | dict[str, Any] | None,
    ) -> tuple[str, list[Any]]:
        if not filters:
            return "", []

        normalized = [filters] if isinstance(filters, dict) else filters
        clauses: list[str] = []
        params: list[Any] = []
        for item in normalized:
            if not isinstance(item, dict):
                raise ValidationError("Filters must be objects with column, op, and value fields.")
            column = item.get("column")
            operator = item.get("op", "eq")
            value = item.get("value")
            if column is None:
                raise ValidationError("Each filter must include a column.")
            self._validate_column(table_columns, column)
            if operator not in SUPPORTED_OPERATORS:
                raise ValidationError(f"Unsupported filter operator: {operator}.")
            clauses.append(f'"{column}" {SUPPORTED_OPERATORS[operator]} ?')
            params.append(value)
        return " AND ".join(clauses), params

    def _validate_pagination(self, limit: int, offset: int) -> tuple[int, int]:
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")
        if offset < 0:
            raise ValidationError("Offset must be zero or greater.")
        return limit, offset
