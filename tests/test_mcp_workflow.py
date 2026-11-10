from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp import Client
from mcp.types import CreateMessageResult, TextContent

from sqlharness.authority import DatabaseAuthority
from sqlharness.mcp_server import create_demo_database, create_server
from sqlharness.workflow import WorkflowEngine


QUESTION = "Which region has the most customers?"
REGION_SQL = (
    "SELECT regions.name, COUNT(customers.id) AS customer_count "
    "FROM customers JOIN regions ON customers.region_id = regions.id "
    "GROUP BY regions.name ORDER BY COUNT(customers.id) DESC LIMIT 1"
)


def graph_payload():
    return json.loads((Path(__file__).parents[1] / "examples/intent_graph_region.json").read_text())


def test_one_call_workflow_requests_graph_then_assembly_from_connected_client(tmp_path):
    root = create_demo_database(tmp_path)
    plan = WorkflowEngine(DatabaseAuthority(root)).prepare("shop", QUESTION, graph_payload())
    assembly = {"sql": REGION_SQL, "selections": plan["assembly_contract"]["selections"]}
    samples = []

    async def sample(_context, params):
        samples.append(params)
        payload = graph_payload() if len(samples) == 1 else assembly
        return CreateMessageResult(role="assistant", content=TextContent(type="text", text=json.dumps(payload)), model="test-fixture", stop_reason="endTurn")

    async def exercise():
        async with Client(create_server(root), sampling_callback=sample) as client:
            tools = await client.list_tools()
            result = await client.call_tool("query_database", {"db_id": "shop", "question": QUESTION})
            return tools, result

    tools, result = asyncio.run(exercise())
    question_tool = next(t for t in tools.tools if t.name == "query_database")
    assert set(question_tool.input_schema["properties"]) == {"db_id", "question", "evidence"}
    assert not result.is_error, result
    trace = result.structured_content
    assert trace["decision"] == "executed", trace
    assert trace["execution"]["rows"] == [["Northeast", 3]]
    assert len(trace["retrieval"]["relationships"]) == 5
    assert [s["stage"] for s in trace["stage_trace"]] == [
        "request", "intent_graph", "graph_validation", "fragment_retrieval", "ranking",
        "query_assembly", "authority", "result",
    ]
    assert len(samples) == 2
    assert all(p.include_context == "none" for p in samples)
    assert "graph contract" in samples[0].messages[0].content.text
    assert "assembly contract" in samples[1].messages[0].content.text
    assert trace["generation"]["origin"] == "connected_mcp_client"


def test_invalid_sampled_graph_stops_before_assembly_or_execution(tmp_path):
    root = create_demo_database(tmp_path)
    samples = []

    async def sample(_context, params):
        samples.append(params)
        graph = graph_payload()
        graph["request"] = "A different request"
        return CreateMessageResult(role="assistant", content=TextContent(type="text", text=json.dumps(graph)), model="test-fixture")

    async def exercise():
        async with Client(create_server(root), sampling_callback=sample) as client:
            return await client.call_tool("query_database", {"db_id": "shop", "question": QUESTION})

    result = asyncio.run(exercise()).structured_content
    assert result["decision"] == "abstained"
    assert result["failure_stage"] == "intent_graph"
    assert len(samples) == 1
    assert not result["database_touched"]


def test_client_without_sampling_gets_staged_workflow_guidance(tmp_path):
    root = create_demo_database(tmp_path)

    async def exercise():
        async with Client(create_server(root)) as client:
            result = await client.call_tool("query_database", {"db_id": "shop", "question": QUESTION})
            prepared = await client.call_tool("prepare_query", {"db_id": "shop", "question": QUESTION, "graph": graph_payload()})
            return result, prepared

    result, prepared = asyncio.run(exercise())
    assert result.is_error
    assert "prepare_query" in str(result.content)
    assert prepared.structured_content["decision"] == "prepared"
