from __future__ import annotations

import json
import sqlite3

from graphsql.dataset import find_sqlite_database, introspect_sqlite_schema, load_bird_examples, render_schema


def test_loads_bird_json_and_introspects_database(tmp_path):
    dataset_path = tmp_path / "dev.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "question_id": 7,
                    "db_id": "shop",
                    "question": "How many customers are there?",
                    "evidence": "Customers are stored in customers.",
                    "SQL": "SELECT COUNT(*) FROM customers",
                }
            ]
        )
    )
    database_directory = tmp_path / "databases" / "shop"
    database_directory.mkdir(parents=True)
    database_path = database_directory / "shop.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)")

    examples = load_bird_examples(dataset_path)
    assert examples[0].example_id == "7"
    assert examples[0].db_id == "shop"
    assert find_sqlite_database(tmp_path / "databases", "shop") == database_path
    schema = introspect_sqlite_schema(database_path)
    assert schema == {"customers": ("id", "name")}
    assert render_schema(schema) == "customers(id, name)"

