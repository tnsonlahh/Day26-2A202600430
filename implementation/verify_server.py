from __future__ import annotations

import json

try:
    from .db import SQLiteAdapter, ValidationError
    from .init_db import DB_PATH, create_database
except ImportError:
    from db import SQLiteAdapter, ValidationError
    from init_db import DB_PATH, create_database


def main() -> None:
    create_database(DB_PATH)
    adapter = SQLiteAdapter(DB_PATH)

    checks = {
        "server_start_import": "implementation.mcp_server imports after fastmcp is installed",
        "tools": ["search", "insert", "aggregate"],
        "resources": ["schema://database", "schema://table/{table_name}"],
        "search_A1": adapter.search(
            "students",
            filters={"column": "cohort", "op": "eq", "value": "A1"},
            order_by="name",
        ),
        "insert_student": adapter.insert(
            "students",
            {"name": "Mai Hoang", "cohort": "A1", "email": "mai.hoang@example.edu"},
        ),
        "count_students": adapter.aggregate("students", "count"),
        "avg_score_by_status": adapter.aggregate("enrollments", "avg", "score", group_by="status"),
        "database_schema_tables": adapter.list_tables(),
    }

    try:
        adapter.search("missing_table")
    except ValidationError as exc:
        checks["invalid_request_error"] = str(exc)
    else:
        raise AssertionError("Invalid table search did not fail.")

    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
