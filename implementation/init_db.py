from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("lab.db")

SCHEMA_SQL = """
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    score REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, email) VALUES
    ('An Nguyen', 'A1', 'an.nguyen@example.edu'),
    ('Binh Tran', 'A1', 'binh.tran@example.edu'),
    ('Chi Le', 'B2', 'chi.le@example.edu'),
    ('Dung Pham', 'B2', 'dung.pham@example.edu');

INSERT INTO courses (code, title, credits) VALUES
    ('MCP101', 'Model Context Protocol Basics', 3),
    ('DB201', 'Applied SQLite', 4),
    ('PY150', 'Python Tooling', 3);

INSERT INTO enrollments (student_id, course_id, score, status) VALUES
    (1, 1, 88.5, 'active'),
    (1, 2, 91.0, 'active'),
    (2, 1, 76.0, 'active'),
    (2, 3, 82.0, 'active'),
    (3, 2, 94.5, 'active'),
    (4, 3, 69.5, 'inactive');
"""


def create_database(db_path: str | Path = DB_PATH) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode = OFF")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.executescript(SEED_SQL)
        conn.commit()
    return path


if __name__ == "__main__":
    print(create_database())
