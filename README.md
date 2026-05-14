# SQLite FastMCP Database Lab

This repository implements a local Model Context Protocol (MCP) server with FastMCP and SQLite. The server exposes exactly three tools:

- `search`
- `insert`
- `aggregate`

It also exposes schema context through:

- `schema://database`
- `schema://table/{table_name}`

## Project Structure

```text
implementation/
  db.py                  # SQLite adapter, validation, safe SQL construction
  init_db.py             # Reproducible schema and seed data
  mcp_server.py          # FastMCP tools and resources
  verify_server.py       # Repeatable smoke verification
  start_inspector.ps1    # MCP Inspector helper for Windows PowerShell
  tests/
    test_server.py       # Automated unit tests
requirements.txt
```

## Data Model

The SQLite database contains three related tables:

- `students`: student name, cohort, and email
- `courses`: course code, title, and credits
- `enrollments`: student/course relationship with score and status

The seed data is recreated every time `implementation/init_db.py` or `implementation/verify_server.py` runs.

## Setup

Use Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python implementation\init_db.py
```

Expected result: `implementation\lab.db` is created with seeded `students`, `courses`, and `enrollments`.

## Run The MCP Server

```powershell
python implementation\mcp_server.py
```

The server runs over stdio by default, which is the simplest transport for local MCP clients.

## Tool Descriptions

### `search`

Searches rows in a validated table.

Arguments:

- `table`: table name
- `filters`: one filter object or a list of filter objects
- `columns`: optional list of selected columns
- `limit`: 1 to 100
- `offset`: zero or greater
- `order_by`: optional column name
- `descending`: boolean

Supported filter operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`.

Example:

```json
{
  "table": "students",
  "filters": {"column": "cohort", "op": "eq", "value": "A1"},
  "order_by": "name"
}
```

### `insert`

Inserts one row into a validated table and returns the inserted payload.

Example:

```json
{
  "table": "students",
  "values": {
    "name": "Mai Hoang",
    "cohort": "A1",
    "email": "mai.hoang@example.edu"
  }
}
```

### `aggregate`

Runs `count`, `avg`, `sum`, `min`, or `max`.

Example:

```json
{
  "table": "enrollments",
  "metric": "avg",
  "column": "score",
  "group_by": "status"
}
```

## Resources

Read the full schema:

```text
schema://database
```

Read one table schema:

```text
schema://table/students
```

## Validation And Safety

The database layer rejects:

- unknown table names
- unknown column names
- unsupported filter operators
- unsupported aggregate metrics
- aggregate metrics that require a missing column
- empty inserts
- invalid pagination

SQL values are passed through bound parameters. Table and column identifiers are validated against SQLite schema metadata before they are included in SQL.

## Automated Verification

Run unit tests:

```powershell
python -m unittest discover -s implementation\tests
```

Run the repeatable smoke check:

```powershell
python implementation\verify_server.py
```

Run an MCP-level verification with FastMCP's in-process client:

```powershell
python implementation\verify_mcp.py
```

Generate demo screenshots from live MCP client calls:

```powershell
python implementation\make_demo_screenshots.py
```

The smoke check demonstrates:

- expected tool names: `search`, `insert`, `aggregate`
- expected resource URIs
- valid `search` for cohort `A1`
- valid `insert` of a student
- valid `count` aggregate
- valid average score grouped by status
- invalid missing-table request returning `Unknown table: missing_table.`

The MCP-level check additionally verifies actual FastMCP discovery and resource reads.

## MCP Inspector

From the repository root:

```powershell
.\implementation\start_inspector.ps1
```

Or run Inspector directly:

```powershell
npx -y @modelcontextprotocol/inspector python "%CD%\implementation\mcp_server.py"
```

In Inspector, verify:

- the server starts
- the three tools are discoverable
- `schema://database` is discoverable
- `schema://table/students` is readable
- a valid tool call succeeds
- an invalid call such as `{"table": "missing_table"}` returns a clear error

## Client Configuration Example

### Codex

Add this to `~/.codex/config.toml`, replacing the path with the absolute path on your machine:

```toml
[mcp_servers.sqlite_lab]
command = "python"
args = ["D:/Git/Git/Day26-2A202600430/implementation/mcp_server.py"]
```

Then start Codex and ask it to use the `sqlite_lab` MCP server, for example:

```text
Use the sqlite_lab MCP server to search all students in cohort A1, then read schema://table/students.
```

### Gemini CLI

Replace both paths with absolute paths for your machine:

```powershell
gemini mcp add sqlite-lab C:\Path\To\python.exe D:\Git\Git\Day26-2A202600430\implementation\mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
gemini --allowed-mcp-server-names sqlite-lab --yolo -p "Use the sqlite-lab MCP server and show me the top 2 students by score."
```

Expected result: `gemini mcp list` shows `sqlite-lab` as connected, and Gemini can call `search`, `insert`, and `aggregate`.

## Demo Video Checklist

Record a short video of about 2 minutes showing:

1. `python implementation\init_db.py`
2. `python -m unittest discover -s implementation\tests`
3. MCP Inspector or an MCP client connected to the server
4. the tools list showing `search`, `insert`, and `aggregate`
5. the schema resource `schema://database`
6. a valid search for students in cohort `A1`
7. a valid insert of a new student
8. a valid aggregate, such as average score by status
9. an invalid request, such as searching `missing_table`, returning a clear error

## Verification Status

Verified locally in `.venv`:

- FastMCP dependency installation
- SQLite database creation
- unit tests
- repeatable smoke script
- validation and error handling
- FastMCP in-process client discovery for tools and resources
- valid and invalid MCP tool calls

Not verified in this environment:

- MCP Inspector connection
- external MCP client connection

Run MCP Inspector or your chosen MCP client to complete the final UI/client demonstration for grading.
