from __future__ import annotations

import asyncio
import json

from fastmcp import Client

try:
    from .init_db import DB_PATH, create_database
    from .mcp_server import mcp
except ImportError:
    from init_db import DB_PATH, create_database
    from mcp_server import mcp


async def main() -> None:
    create_database(DB_PATH)

    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()

        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": {"column": "cohort", "op": "eq", "value": "A1"},
                "order_by": "name",
            },
        )
        aggregate_result = await client.call_tool(
            "aggregate",
            {"table": "enrollments", "metric": "avg", "column": "score", "group_by": "status"},
        )
        invalid_result = await client.call_tool("search", {"table": "missing_table"})
        schema_result = await client.read_resource("schema://database")

    payload = {
        "tools": [tool.name for tool in tools],
        "resources": [str(resource.uri) for resource in resources],
        "resource_templates": [template.uriTemplate for template in templates],
        "search_A1": search_result.data,
        "avg_score_by_status": aggregate_result.data,
        "invalid_search": invalid_result.data,
        "schema_resource_read": bool(schema_result),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
