from __future__ import annotations

import pytest

pytest.importorskip("sqlglot")

from sqlharness.validation import validate_readonly_sql


SCHEMA = {
    "customers": ("id", "name", "region_id"),
    "regions": ("id", "name"),
}


def test_accepts_readonly_query_with_aliases():
    result = validate_readonly_sql(
        "SELECT c.name FROM customers AS c WHERE c.id > 2",
        SCHEMA,
    )
    assert result.valid
    assert result.errors == ()
    assert result.referenced_tables == ("customers",)


def test_accepts_output_alias_in_order_by():
    result = validate_readonly_sql(
        "SELECT region_id, COUNT(*) AS customer_count "
        "FROM customers GROUP BY region_id ORDER BY customer_count DESC",
        SCHEMA,
    )
    assert result.valid
    assert result.errors == ()


def test_rejects_mutation_and_unknown_schema_references():
    mutation = validate_readonly_sql("DELETE FROM customers", SCHEMA)
    unknown = validate_readonly_sql("SELECT missing FROM customers", SCHEMA)
    assert not mutation.valid
    assert mutation.errors == ("non_readonly_operations: DELETE",)
    assert not unknown.valid
    assert unknown.errors == ("unknown_column: missing",)


def test_rejects_column_from_an_unreferenced_table():
    result = validate_readonly_sql(
        "SELECT amount_usd FROM customers",
        {"customers": ("id", "name"), "orders": ("id", "amount_usd")},
    )
    assert not result.valid
    assert any("invalid_column_scope" in error for error in result.errors)


def test_resolves_cte_and_derived_table_columns():
    for sql in (
        "WITH names AS (SELECT name FROM customers) SELECT name FROM names",
        "SELECT x.name FROM (SELECT name FROM customers) AS x",
    ):
        assert validate_readonly_sql(sql, SCHEMA).valid
