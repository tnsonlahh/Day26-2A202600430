from __future__ import annotations

import unittest
from uuid import uuid4
from pathlib import Path

from implementation.db import SQLiteAdapter, ValidationError
from implementation.init_db import create_database


class SQLiteAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(__file__).parent / ".tmp"
        self.tempdir.mkdir(exist_ok=True)
        self.db_path = self.tempdir / f"{self._testMethodName}_{uuid4().hex}.db"
        create_database(self.db_path)
        self.adapter = SQLiteAdapter(self.db_path)

    def tearDown(self) -> None:
        try:
            if self.db_path.exists():
                self.db_path.unlink()
        except PermissionError:
            pass

    def test_search_filters_ordering_and_pagination(self) -> None:
        result = self.adapter.search(
            "students",
            filters={"column": "cohort", "op": "eq", "value": "A1"},
            columns=["name", "cohort"],
            limit=1,
            order_by="name",
        )
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["cohort"], "A1")

    def test_insert_returns_inserted_payload(self) -> None:
        result = self.adapter.insert(
            "students",
            {"name": "Mai Hoang", "cohort": "A1", "email": "mai.hoang@example.edu"},
        )
        self.assertEqual(result["inserted"]["name"], "Mai Hoang")
        self.assertIsInstance(result["inserted"]["id"], int)

    def test_aggregate_count_and_avg_group_by(self) -> None:
        count = self.adapter.aggregate("students", "count")
        avg = self.adapter.aggregate("enrollments", "avg", "score", group_by="status")
        self.assertEqual(count["rows"][0]["value"], 4)
        self.assertGreater(avg["rows"][0]["value"], 0)

    def test_schema_resources_payload(self) -> None:
        schema = self.adapter.get_database_schema()
        table = self.adapter.get_table_schema("students")
        self.assertIn("students", schema["tables"])
        self.assertEqual(table["table"], "students")

    def test_rejects_invalid_requests(self) -> None:
        with self.assertRaises(ValidationError):
            self.adapter.search("missing_table")
        with self.assertRaises(ValidationError):
            self.adapter.search("students", filters={"column": "name", "op": "contains", "value": "An"})
        with self.assertRaises(ValidationError):
            self.adapter.insert("students", {})
        with self.assertRaises(ValidationError):
            self.adapter.aggregate("students", "median", "id")


if __name__ == "__main__":
    unittest.main()
