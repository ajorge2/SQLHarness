from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path

import pytest

from sqlharness.authority import DatabaseAuthority
from sqlharness.workflow import WorkflowEngine


@pytest.fixture
def engine(tmp_path):
    directory = tmp_path / "shop"
    directory.mkdir()
    with sqlite3.connect(directory / "shop.sqlite") as connection:
        connection.executescript("""
            CREATE TABLE regions(id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE customers(id INTEGER PRIMARY KEY, region_id INTEGER, segment TEXT);
            CREATE TABLE orders(id INTEGER PRIMARY KEY, amount_usd REAL, status TEXT);
            INSERT INTO regions VALUES (1,'Northeast'),(2,'South');
            INSERT INTO customers VALUES (1,1,'Startup'),(2,1,'Enterprise'),(3,1,'Startup'),(4,2,'Enterprise');
            INSERT INTO orders VALUES (1,120,'paid'),(2,900,'paid'),(3,80,'pending'),(4,200,'paid');
        """)
    return WorkflowEngine(DatabaseAuthority(tmp_path, max_rows=10))


@pytest.fixture
def region_graph():
    return json.loads((Path(__file__).resolve().parents[1] / "examples/intent_graph_region.json").read_text())


@pytest.fixture
def paid_graph():
    return {
        "graph_version": "0.2", "request": "What is total paid revenue?", "evidence": "",
        "nodes": [
            {"node_id": "answer", "kind": "output", "concept": "answer"},
            {"node_id": "total", "kind": "operation", "concept": "sum", "attributes": {"inferred": True}},
            {"node_id": "amount", "kind": "attribute", "concept": "amount", "schema_candidates": ["orders.amount_usd"], "attributes": {"inferred": True}},
            {"node_id": "paid", "kind": "condition", "concept": "paid", "schema_candidates": ["orders.status"], "attributes": {"inferred": True, "operator": "=", "value": "paid"}},
        ],
        "edges": [
            {"source": "answer", "role": "returns", "target": "total"},
            {"source": "total", "role": "theme", "target": "amount"},
            {"source": "total", "role": "filter", "target": "paid"},
        ],
    }


def assembly(engine, graph, sql):
    plan = engine.prepare("shop", graph["request"], graph)
    assert plan["decision"] == "prepared", plan.get("errors")
    return {"sql": sql, "selections": plan["assembly_contract"]["selections"]}


def test_region_request_runs_all_stages_with_relationship_rankings(engine, region_graph):
    sql = """SELECT regions.name, COUNT(customers.id) AS customer_count
        FROM customers JOIN regions ON customers.region_id = regions.id
        GROUP BY regions.name ORDER BY COUNT(customers.id) DESC LIMIT 1"""
    result = engine.execute("shop", region_graph["request"], region_graph, assembly(engine, region_graph, sql))
    assert result["decision"] == "executed", result.get("errors")
    assert result["execution"]["rows"] == (("Northeast", 3),)
    assert len(result["retrieval"]["relationships"]) == len(region_graph["edges"])
    assert [step["stage"] for step in result["stage_trace"]] == ["request", "intent_graph", "graph_validation", "fragment_retrieval", "ranking", "query_assembly", "authority", "result"]
    assert result["receipt"]["receipt_id"]


def test_paid_revenue_binds_graph_predicate_and_returns_actual_rows(engine, paid_graph):
    sql = "SELECT SUM(amount_usd) AS total FROM orders WHERE status = 'paid'"
    result = engine.execute("shop", paid_graph["request"], paid_graph, assembly(engine, paid_graph, sql))
    assert result["decision"] == "executed", result.get("errors")
    assert result["execution"]["rows"] == ((1220.0,),)


def test_prepared_graph_round_trips_directly_into_execute(engine, paid_graph):
    plan = engine.prepare("shop", paid_graph["request"], paid_graph)
    assert isinstance(plan["graph"]["nodes"], list)
    result = engine.execute("shop", paid_graph["request"], plan["graph"], {
        "sql": "SELECT SUM(amount_usd) FROM orders WHERE status='paid'",
        "selections": plan["assembly_contract"]["selections"],
    })
    assert result["decision"] == "executed", result.get("errors")


@pytest.mark.parametrize("ordering", ["regions.name DESC", "SUM(customers.id) DESC"])
def test_region_ranking_must_order_the_graphs_customer_count(engine, region_graph, ordering):
    sql = f"SELECT regions.name, COUNT(customers.id) AS customer_count FROM customers JOIN regions ON customers.region_id=regions.id GROUP BY regions.name ORDER BY {ordering} LIMIT 1"
    result = engine.execute("shop", region_graph["request"], region_graph, assembly(engine, region_graph, sql))
    assert result["decision"] == "abstained"
    assert any("order_measure_binding_mismatch" in error for error in result["errors"])


def test_region_can_order_a_bound_projection_alias(engine, region_graph):
    sql = "SELECT regions.name, COUNT(customers.id) AS customer_count FROM customers JOIN regions ON customers.region_id=regions.id GROUP BY regions.name ORDER BY customer_count DESC LIMIT 1"
    result = engine.execute("shop", region_graph["request"], region_graph, assembly(engine, region_graph, sql))
    assert result["decision"] == "executed", result.get("errors")


@pytest.mark.parametrize("sql", [
    "SELECT SUM(amount_usd) FROM orders",
    "SELECT SUM(amount_usd) FROM orders WHERE status = 'pending'",
    "SELECT COUNT(*) FROM orders WHERE status = 'paid'",
    "SELECT 42",
    "SELECT SUM(amount_usd) FROM orders WHERE status = 'paid' OR 1=1",
    "SELECT SUM(amount_usd) FROM orders WHERE status = 'paid' AND amount_usd > 500",
    "SELECT SUM(id), amount_usd FROM orders WHERE status = 'paid'",
])
def test_safe_but_unrelated_sql_abstains_before_execution(engine, paid_graph, sql):
    result = engine.execute("shop", paid_graph["request"], paid_graph, assembly(engine, paid_graph, sql))
    assert result["decision"] == "abstained"
    assert result["failure_stage"] == "query_assembly"
    assert result["database_touched"] is False
    assert "receipt" not in result


def test_sql_cannot_invent_order_or_limit(engine, paid_graph):
    sql = "SELECT SUM(amount_usd) FROM orders WHERE status = 'paid' ORDER BY 1 LIMIT 1"
    result = engine.execute("shop", paid_graph["request"], paid_graph, assembly(engine, paid_graph, sql))
    assert result["decision"] == "abstained"
    assert any("clause_not_supported" in error for error in result["errors"])


def test_unknown_selection_and_missing_selection_rejected(engine, paid_graph):
    proposal = assembly(engine, paid_graph, "SELECT SUM(amount_usd) FROM orders WHERE status = 'paid'")
    proposal["selections"][0]["fragment_id"] = "invented"
    result = engine.execute("shop", paid_graph["request"], paid_graph, proposal)
    assert result["decision"] == "abstained"
    assert any("unknown_ranked_selection" in error for error in result["errors"])
    proposal["selections"] = []
    assert engine.execute("shop", paid_graph["request"], paid_graph, proposal)["decision"] == "abstained"


def test_graph_request_and_schema_cannot_be_substituted(engine, paid_graph):
    graph = copy.deepcopy(paid_graph)
    graph["request"] = "Different question"
    assert engine.prepare("shop", paid_graph["request"], graph)["failure_stage"] == "intent_graph"
    graph = copy.deepcopy(paid_graph)
    graph["nodes"][2]["schema_candidates"] = ["orders.secret"]
    result = engine.prepare("shop", paid_graph["request"], graph)
    assert result["failure_stage"] == "graph_validation"
    assert any("unknown_schema_candidate" in error for error in result["errors"])


def test_invalid_graph_never_reaches_retrieval(engine, paid_graph):
    paid_graph["edges"].append({"source": "paid", "role": "filter", "target": "total"})
    result = engine.prepare("shop", paid_graph["request"], paid_graph)
    assert result["decision"] == "abstained"
    assert result["failure_stage"] == "graph_validation"
    assert "retrieval" not in result


def test_unsupported_graph_operation_stops_for_catalog_coverage(engine, paid_graph):
    paid_graph["nodes"][1]["concept"] = "invented_aggregate"
    result = engine.prepare("shop", paid_graph["request"], paid_graph)
    assert result["decision"] == "abstained"
    assert result["failure_stage"] == "ranking"
    assert result["retrieval"]["coverage"]["complete"] is False


@pytest.mark.parametrize("bad_graph", [{}, {"nodes": "bad", "edges": []}, {"nodes": [{}] * 65, "edges": []}])
def test_malformed_and_oversized_graphs_fail_with_bounded_error(engine, bad_graph):
    result = engine.prepare("shop", "Question", bad_graph)
    assert result["decision"] == "abstained"
    assert result["failure_stage"] == "intent_graph"


def test_question_limits_and_exact_evidence_are_enforced(engine, paid_graph):
    assert engine.describe("shop", "x" * 8001)["decision"] == "abstained"
    assert engine.describe("shop", "question", "x" * 8001)["decision"] == "abstained"
    assert engine.prepare("shop", paid_graph["request"], paid_graph, "new evidence")["failure_stage"] == "intent_graph"


def test_write_is_blocked_by_shared_authority(engine, paid_graph):
    result = engine.execute("shop", paid_graph["request"], paid_graph, assembly(engine, paid_graph, "DELETE FROM orders"))
    assert result["decision"] == "blocked"
    assert result["failure_stage"] == "authority"
    assert result["receipt"]["database_touched"] is False
    assert engine.authority.execute("shop", "SELECT COUNT(*) FROM orders")["execution"]["rows"] == ((4,),)


def test_unqualified_column_from_unreferenced_table_is_rejected(engine, paid_graph):
    sql = "SELECT SUM(amount_usd) FROM customers WHERE segment = 'paid'"
    result = engine.execute("shop", paid_graph["request"], paid_graph, assembly(engine, paid_graph, sql))
    assert result["decision"] in {"abstained", "blocked"}
    assert result["database_touched"] is False
