"""Stateless, inspectable request-to-result workflow shared by MCP transports.

The host model supplies graph/SQL proposals. Every deterministic stage is rerun
before execution; neither a client trace nor a previous preparation is authority.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from .authority import DatabaseAuthority
from .intent import EDGE_ROLES, GRAPH_VERSION, NODE_KINDS, ROLE_SIGNATURES, IntentGraph, validate_intent_graph
from .workflow_retrieval import operation, rank_relationships

MAX_TEXT = 8_000
MAX_GRAPH_BYTES = 64_000
MAX_NODES = 64
MAX_EDGES = 96


def _step(stage: str, status: str, **details: Any) -> dict[str, Any]:
    return {"stage": stage, "status": status, **details}


def _abstain(result: dict[str, Any], stage: str, errors: list[str]) -> dict[str, Any]:
    result.update(decision="abstained", failure_stage=stage, errors=errors, database_touched=False)
    result["stage_trace"].append(_step(stage, "rejected", errors=errors))
    return result


def _request_errors(question: Any, evidence: Any) -> list[str]:
    errors = []
    if not isinstance(question, str) or not question.strip() or len(question) > MAX_TEXT:
        errors.append("question_must_contain_1_to_8000_characters")
    if not isinstance(evidence, str) or len(evidence) > MAX_TEXT:
        errors.append("evidence_must_contain_at_most_8000_characters")
    return errors


def _graph_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["graph_must_be_an_object"]
    try:
        if len(json.dumps(payload, allow_nan=False).encode("utf-8")) > MAX_GRAPH_BYTES:
            return ["graph_exceeds_64000_bytes"]
    except (TypeError, ValueError, RecursionError):
        return ["graph_must_be_bounded_json"]
    nodes, edges = payload.get("nodes"), payload.get("edges")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES:
        return ["graph_requires_1_to_64_nodes"]
    if not isinstance(edges, list) or not 1 <= len(edges) <= MAX_EDGES:
        return ["graph_requires_1_to_96_relationships"]
    for node in nodes:
        if not isinstance(node, dict) or any(not isinstance(node.get(k), str) for k in ("node_id", "kind", "concept")):
            return ["invalid_node_shape"]
        if not isinstance(node.get("attributes", {}), dict):
            return ["invalid_node_attributes"]
        if any(value is not None and not isinstance(value, (str, bool, int, float)) for value in node.get("attributes", {}).values()):
            return ["node_attributes_must_be_scalar_values"]
        candidates = node.get("schema_candidates", [])
        if not isinstance(candidates, list) or any(not isinstance(x, str) for x in candidates):
            return ["invalid_schema_candidates"]
        spans = node.get("spans", [])
        if not isinstance(spans, list):
            return ["invalid_source_spans"]
        for span in spans:
            if not isinstance(span, dict) or not isinstance(span.get("text"), str):
                return ["invalid_source_span"]
            if any(type(span.get(k)) is not int for k in ("start", "end")):
                return ["invalid_source_span_offsets"]
            if not isinstance(span.get("source", "request"), str):
                return ["invalid_source_span_source"]
    if any(not isinstance(e, dict) or any(not isinstance(e.get(k), str) for k in ("source", "role", "target")) for e in edges):
        return ["invalid_relationship_shape"]
    return []


class WorkflowEngine:
    """Run graph validation, per-edge retrieval/ranking, assembly checks and reads."""

    def __init__(self, authority: DatabaseAuthority) -> None:
        self.authority = authority

    def describe(self, db_id: str, question: str, evidence: str = "") -> dict[str, Any]:
        result: dict[str, Any] = {"workflow_version": "1", "db_id": db_id, "stage_trace": []}
        errors = _request_errors(question, evidence)
        if errors:
            return _abstain(result, "request", errors)
        schema = self.authority.schema(db_id)
        contract = {
            "graph_version": GRAPH_VERSION,
            "node_kinds": sorted(NODE_KINDS),
            "edge_roles": sorted(EDGE_ROLES),
            "role_signatures": {role: {"source_kinds": sorted(source), "target_kinds": sorted(target)} for role, (source, target) in ROLE_SIGNATURES.items()},
            "limits": {"nodes": MAX_NODES, "edges": MAX_EDGES, "json_bytes": MAX_GRAPH_BYTES},
            "supported_operations": ["count", "sum", "avg", "min", "max", "argmax", "argmin"],
            "predicate_attributes": {"operator": "=, !=, >, >=, <, <=, LIKE, IS NULL, IS NOT NULL", "value": "Exact scalar comparison value, or use a condition-value edge."},
            "unsupported_relationships": ["operand", "numerator", "denominator", "member_of", "scoped_to", "optional"],
        }
        instructions = (
            "Convert the question and evidence into the supplied SQLHarness graph contract. "
            "Return JSON with graph_version, request, evidence, nodes and edges. Copy request/evidence exactly. "
            "Each node has node_id, kind, concept, spans, schema_candidates and attributes. "
            "Spans use exact zero-based end-exclusive start/end/text and source=request or evidence. "
            "A node without a source span must have attributes.inferred=true, except output/scope nodes. "
            "Use one output, connected acyclic relationships and exact table/table.column schema names. "
            "Include operations, predicates (operator and value), grouping, order direction, limits and joins "
            "needed by the question. Do not invent business definitions. Unsupported concepts must remain "
            "explicit so the workflow can abstain. Return a graph only, not SQL."
        )
        result.update(decision="awaiting_intent", question=question, evidence=evidence, schema=schema, graph_contract=contract)
        result["intent_prompt"] = instructions + "\n\n" + json.dumps({"question": question, "evidence": evidence, "schema": schema, "contract": contract}, ensure_ascii=False)
        result["stage_trace"].append(_step("request", "completed", schema_inspected=True))
        return result

    def prepare(self, db_id: str, question: str, graph: dict[str, Any], evidence: str = "") -> dict[str, Any]:
        result = self.describe(db_id, question, evidence)
        if result["decision"] == "abstained":
            return result
        errors = _graph_errors(graph)
        if errors:
            return _abstain(result, "intent_graph", errors)
        if graph.get("request") != question or graph.get("evidence", "") != evidence:
            return _abstain(result, "intent_graph", ["graph_request_or_evidence_does_not_match"])
        try:
            parsed = IntentGraph.from_dict(graph)
            validation = validate_intent_graph(parsed)
        except (ValueError, TypeError, KeyError, RecursionError):
            return _abstain(result, "intent_graph", ["malformed_graph"])
        result["stage_trace"].append(_step("intent_graph", "completed", proposal_origin="client_proposal", nodes=len(parsed.nodes), relationships=len(parsed.edges)))
        schema_map = {table["name"]: tuple(table["columns"]) for table in result["schema"]["tables"]}
        errors = list(validation.errors)
        for node in parsed.nodes:
            for candidate in node.schema_candidates:
                if candidate in schema_map:
                    continue
                table, _, column = candidate.partition(".")
                if table not in schema_map or column not in schema_map[table]:
                    errors.append(f"unknown_schema_candidate: {node.node_id}={candidate}")
        result["graph_validation"] = {"valid": not errors, "errors": errors}
        if errors:
            return _abstain(result, "graph_validation", errors)
        # Keep the public preparation payload directly reusable by execute(),
        # including when an in-process host skips a transport serialization.
        result["graph"] = json.loads(json.dumps(parsed.to_dict(), ensure_ascii=False))
        result["stage_trace"].append(_step("graph_validation", "completed"))
        retrieval = rank_relationships(parsed, schema_map, top_k=3)
        result["retrieval"] = retrieval
        result["stage_trace"].append(_step("fragment_retrieval", "completed", relationships=len(retrieval["relationships"]), catalog_version=retrieval.get("catalog_version")))
        if not retrieval["coverage"]["complete"]:
            return _abstain(result, "ranking", ["unsupported_relationship_coverage", *[str(item) for item in retrieval["coverage"]["missing"]]])
        result["stage_trace"].append(_step("ranking", "completed", ranker=retrieval.get("ranker"), coverage_complete=True))
        result["assembly_contract"] = {
            "sql": "One read-only SQLite SELECT, at most 16000 characters.",
            "selections": [{"relation_id": item["relation_id"], "fragment_id": item["selected_fragment_id"]} for item in retrieval["relationships"]],
            "rules": [
                "Use exactly one ranked candidate per relationship; prefer the top-ranked candidate.",
                "Bind templates to the graph and inspected schema. Include graph predicates, calculations, grouping, order, and limits.",
                "Joins may connect the graph's referenced tables. Do not add unrelated filters, calculations or clauses.",
                "Return {sql, selections}; do not execute SQL directly or claim an execution result.",
            ],
        }
        result["assembly_prompt"] = "Assemble the validated graph and selected fragments into SQLite. Return only JSON matching the assembly contract.\n\n" + json.dumps({key: result[key] for key in ("question", "evidence", "schema", "graph", "retrieval", "assembly_contract")}, ensure_ascii=False)
        result.update(decision="prepared", failure_stage=None)
        return result

    def execute(self, db_id: str, question: str, graph: dict[str, Any], assembly: dict[str, Any], evidence: str = "") -> dict[str, Any]:
        result = self.prepare(db_id, question, graph, evidence)
        if result["decision"] != "prepared":
            return result
        if not isinstance(assembly, dict) or not isinstance(assembly.get("sql"), str) or not 1 <= len(assembly["sql"]) <= 16_000:
            return _abstain(result, "query_assembly", ["assembly_requires_sql_of_1_to_16000_characters"])
        selections = assembly.get("selections")
        if not isinstance(selections, list) or len(selections) > MAX_EDGES:
            return _abstain(result, "query_assembly", ["assembly_requires_relationship_selections"])
        by_id = {item["relation_id"]: item for item in result["retrieval"]["relationships"]}
        chosen: dict[str, dict[str, Any]] = {}
        errors = []
        for selection in selections:
            if not isinstance(selection, dict) or not isinstance(selection.get("relation_id"), str) or not isinstance(selection.get("fragment_id"), str):
                errors.append("invalid_selection_shape")
                continue
            relation_id, fragment_id = selection["relation_id"], selection["fragment_id"]
            if relation_id in chosen:
                errors.append(f"duplicate_selection: {relation_id}")
                continue
            candidate = next((item for item in by_id.get(relation_id, {}).get("candidates", []) if item["fragment_id"] == fragment_id), None)
            if candidate is None:
                errors.append(f"unknown_ranked_selection: {relation_id}/{fragment_id}")
            else:
                chosen[relation_id] = candidate
        errors.extend(f"missing_selection: {relation_id}" for relation_id in by_id if relation_id not in chosen)
        if errors:
            return _abstain(result, "query_assembly", errors)
        sql = assembly["sql"]
        policy = self.authority.validate(db_id, sql)
        if not policy["validation"]["valid"]:
            result["stage_trace"].append(_step("query_assembly", "completed", proposal_origin="client_proposal", selections=selections))
            return self._finish(result, db_id, sql)
        errors = _assembly_errors(sql, IntentGraph.from_dict(result["graph"]), by_id, chosen, result["schema"])
        result["assembly_validation"] = {"valid": not errors, "errors": errors}
        if errors:
            return _abstain(result, "query_assembly", errors)
        result["stage_trace"].append(_step("query_assembly", "completed", proposal_origin="client_proposal", selections=selections))
        return self._finish(result, db_id, sql)

    def _finish(self, result: dict[str, Any], db_id: str, sql: str) -> dict[str, Any]:
        receipt = self.authority.execute(db_id, sql)
        result.update(decision=receipt["decision"], sql=sql, receipt=receipt, execution=receipt.get("execution"), database_touched=receipt.get("database_touched", False))
        result["stage_trace"].append(_step("authority", "completed" if receipt["decision"] != "blocked" else "blocked", validation=receipt["validation"]))
        if receipt.get("execution") is not None:
            result["stage_trace"].append(_step("result", "completed" if receipt["decision"] == "executed" else "failed", truncated=receipt["execution"].get("truncated", False)))
        result["failure_stage"] = None if receipt["decision"] == "executed" else ("authority" if receipt["decision"] == "blocked" else "result")
        # Prompts are preparation aids, not a second copy of the complete trace.
        result.pop("intent_prompt", None)
        result.pop("assembly_prompt", None)
        return result


def _assembly_errors(sql: str, graph: IntentGraph, relationships: Mapping[str, Any], chosen: Mapping[str, Any], schema: dict[str, Any]) -> list[str]:
    import sqlglot
    from sqlglot import exp

    tree = sqlglot.parse_one(sql, read="sqlite")
    if not isinstance(tree, exp.Select) or len(list(tree.find_all(exp.Select))) != 1 or tree.args.get("with_"):
        return ["unsupported_assembly_shape: only a single SELECT scope is currently verified"]
    errors: list[str] = []
    nodes = {node.node_id: node for node in graph.nodes}
    tables = {table.alias_or_name.lower(): table.name for table in tree.find_all(exp.Table)}
    table_names = set(tables.values())
    column_names: set[str] = set()
    schema_map = {item["name"]: set(item["columns"]) for item in schema["tables"]}
    output_aliases = {item.alias.lower() for item in tree.expressions if item.alias}
    for column in tree.find_all(exp.Column):
        if column.name == "*":
            continue
        if column.table:
            table = tables.get(column.table.lower(), column.table)
            column_names.add(f"{table}.{column.name}")
        else:
            candidates = [table for table in table_names if column.name in schema_map.get(table, set())]
            if len(candidates) == 1:
                column_names.add(f"{candidates[0]}.{column.name}")
            elif column.name.lower() not in output_aliases:
                errors.append(f"unresolved_or_ambiguous_column: {column.name}")
    def columns_in(expression: Any) -> set[str]:
        found: set[str] = set()
        for column in expression.find_all(exp.Column):
            if column.table:
                found.add(f"{tables.get(column.table.lower(), column.table)}.{column.name}")
            else:
                found.update(f"{table}.{column.name}" for table in table_names if column.name in schema_map.get(table, set()))
        return found

    def measured_columns(node: Any) -> set[str]:
        measured = {candidate for candidate in node.schema_candidates if "." in candidate}
        for edge in graph.edges:
            if edge.source == node.node_id and edge.role in {"theme", "measure"}:
                measured.update(candidate for candidate in nodes[edge.target].schema_candidates if "." in candidate)
        return measured

    def resolves_output_alias(expression: Any) -> Any:
        value = expression.this if isinstance(expression, exp.Ordered) else expression
        if isinstance(value, exp.Column) and not value.table:
            for projection in tree.expressions:
                if projection.alias and projection.alias.lower() == value.name.lower():
                    return projection.this
        return value
    for node in graph.nodes:
        if node.schema_candidates and not any(candidate in table_names or candidate in column_names for candidate in node.schema_candidates):
            errors.append(f"graph_binding_missing_from_sql: {node.node_id}")
    graph_tables = {candidate.split(".")[0] for node in graph.nodes for candidate in node.schema_candidates}
    errors.extend(f"table_not_in_intent_graph: {table}" for table in table_names - graph_tables)
    literals = {str(item.this).lower() for item in tree.find_all(exp.Literal)}
    functions = {item.key.lower() for item in tree.find_all(exp.Func)}
    selected_kinds = {item["kind"] for item in chosen.values()}
    for name, kind in (("where", "filter"), ("having", "having"), ("group", "group"), ("order", "order"), ("limit", "limit")):
        if tree.args.get(name) is not None and kind not in selected_kinds and not (kind == "having" and "filter" in selected_kinds):
            errors.append(f"clause_not_supported_by_selected_fragments: {name}")
    for relation_id, candidate in chosen.items():
        relation = relationships[relation_id]
        source, target = nodes[relation["source"]], nodes[relation["target"]]
        kind = candidate["kind"]
        template = candidate["template_sql"].upper()
        if kind in {"aggregate", "projection"}:
            expected_functions = [name for name in ("COUNT", "SUM", "AVG", "MIN", "MAX") if name + "(" in template.replace(" ", "")]
            for name in expected_functions:
                if name.lower() not in functions:
                    errors.append(f"selected_function_missing: {relation_id}/{name}")
                op_node = source if source.kind == "operation" else target
                measured = measured_columns(op_node)
                aggregates = [item for item in tree.find_all(exp.AggFunc) if item.key.lower() == name.lower()]
                if kind == "projection" and not any(item.key.lower() == name.lower() for projection in tree.expressions for item in projection.find_all(exp.AggFunc)):
                    errors.append(f"selected_output_calculation_missing: {relation_id}/{name}")
                if measured and not any(columns_in(item) & measured for item in aggregates):
                    errors.append(f"aggregate_measure_binding_mismatch: {relation_id}")
                if "DISTINCT" in template and not any(isinstance(item.this, exp.Distinct) for item in aggregates):
                    errors.append(f"distinct_aggregate_missing: {relation_id}")
                if "COUNT(*)" in template.replace(" ", "") and not any(isinstance(item.this, exp.Star) for item in aggregates):
                    errors.append(f"count_all_shape_mismatch: {relation_id}")
            if kind == "projection" and "DISTINCT" in template and not expected_functions and not tree.args.get("distinct"):
                errors.append(f"distinct_projection_missing: {relation_id}")
            if kind == "projection" and not expected_functions:
                expected_columns = {candidate for candidate in target.schema_candidates if "." in candidate}
                projection_columns = set().union(*(columns_in(item) for item in tree.expressions))
                if expected_columns and not projection_columns & expected_columns:
                    errors.append(f"output_binding_mismatch: {relation_id}")
        if kind in {"filter", "having"}:
            if tree.args.get("where") is None and tree.args.get("having") is None:
                errors.append(f"selected_predicate_missing: {relation_id}")
            for node in (source, target):
                expected = node.attributes.get("value")
                if expected is None and node.kind == "value":
                    expected = node.concept
                if expected is not None and str(expected).lower() not in literals:
                    errors.append(f"predicate_value_missing: {relation_id}/{expected}")
                operator = node.attributes.get("operator")
                operator_classes = {"=": exp.EQ, "!=": exp.NEQ, "<>": exp.NEQ, ">": exp.GT, ">=": exp.GTE, "<": exp.LT, "<=": exp.LTE}
                if operator in operator_classes and not list(tree.find_all(operator_classes[operator])):
                    errors.append(f"predicate_operator_missing: {relation_id}/{operator}")
        if kind in {"group", "order", "limit"}:
            clause = tree.args.get(kind)
            if clause is None:
                errors.append(f"selected_clause_missing: {relation_id}/{kind}")
            elif kind == "group":
                expected_columns = {candidate for candidate in target.schema_candidates if "." in candidate}
                if expected_columns and not columns_in(clause) & expected_columns:
                    errors.append(f"group_binding_mismatch: {relation_id}")
            elif kind == "order":
                descending = "DESC" in template
                if not any(bool(item.args.get("desc")) == descending for item in clause.expressions):
                    errors.append(f"order_direction_mismatch: {relation_id}")
                order_expressions = [resolves_output_alias(item) for item in clause.expressions]
                order_node = target if target.kind == "operation" else source
                measure_nodes = [nodes[edge.target] for edge in graph.edges if edge.source == order_node.node_id and edge.role == "measure"]
                for measured_node in measure_nodes:
                    required_function = operation(measured_node)
                    if required_function in {"count", "sum", "avg", "min", "max"}:
                        required_columns = measured_columns(measured_node)
                        if not any(item.key.lower() == required_function and (not required_columns or columns_in(item) & required_columns) for expression in order_expressions for item in expression.find_all(exp.AggFunc)):
                            errors.append(f"order_measure_binding_mismatch: {relation_id}")
                if relation["role"] in {"order_by", "tie_breaker"}:
                    required_columns = {candidate for candidate in target.schema_candidates if "." in candidate}
                    if required_columns and not any(columns_in(expression) & required_columns for expression in order_expressions):
                        errors.append(f"order_binding_mismatch: {relation_id}")
            elif kind == "limit":
                expected = source.attributes.get("limit", target.attributes.get("limit", 1))
                if str(clause.expression.this) != str(expected):
                    errors.append(f"limit_mismatch: {relation_id}")
        if kind == "join" and not any(join.args.get("on") is not None or join.args.get("using") for join in tree.args.get("joins", [])):
            errors.append(f"selected_join_missing: {relation_id}")
        if kind not in {"aggregate", "projection", "filter", "having", "group", "order", "limit", "join", "binding"}:
            errors.append(f"unsupported_selected_fragment_kind: {relation_id}/{kind}")
    # All calculations must be represented by an operation in the graph.
    concept_aliases = {"total": "sum", "average": "avg", "minimum": "min", "maximum": "max"}
    graph_functions = {operation(node) or concept_aliases.get(node.concept.lower(), node.concept.lower()) for node in graph.nodes if node.kind == "operation"}
    for aggregate in tree.find_all(exp.AggFunc):
        if aggregate.key.lower() not in graph_functions:
            errors.append(f"calculation_not_in_intent_graph: {aggregate.key}")
    # Current catalog supports conjunctive scalar conditions. A required literal
    # appearing somewhere in an OR expression is not proof the filter was kept.
    if list(tree.find_all(exp.Or)):
        errors.append("unsupported_boolean_assembly: OR requires an explicit supported logic contract")
    condition_nodes = [node for node in graph.nodes if node.kind == "condition"]
    comparison_classes = {"=": exp.EQ, "==": exp.EQ, "!=": exp.NEQ, "<>": exp.NEQ, ">": exp.GT, ">=": exp.GTE, "<": exp.LT, "<=": exp.LTE, "LIKE": exp.Like}
    expected_predicates = []
    for condition in condition_nodes:
        expected_columns = {candidate for candidate in condition.schema_candidates if "." in candidate}
        expected_value = condition.attributes.get("value")
        for edge in graph.edges:
            if edge.source != condition.node_id:
                continue
            if edge.role == "compare":
                expected_columns.update(candidate for candidate in nodes[edge.target].schema_candidates if "." in candidate)
            elif edge.role == "value":
                value_node = nodes[edge.target]
                expected_value = value_node.attributes.get("value", value_node.concept)
        operator = str(condition.attributes.get("operator", condition.concept)).upper()
        operator = {"EQUAL": "=", "EQUALS": "=", "IS": "="}.get(operator, operator)
        if operator in comparison_classes:
            if expected_value is None or not expected_columns:
                errors.append(f"predicate_binding_incomplete: {condition.node_id}")
                continue
            comparisons = list(tree.find_all(comparison_classes[operator]))
            matching = [item for item in comparisons if columns_in(item.this) & expected_columns and isinstance(item.expression, exp.Literal) and str(item.expression.this) == str(expected_value)]
            if not matching:
                errors.append(f"predicate_binding_mismatch: {condition.node_id}")
            expected_predicates.extend(matching)
        elif operator in {"IS NULL", "IS NOT NULL"}:
            matching = [item for item in tree.find_all(exp.Is) if columns_in(item.this) & expected_columns and isinstance(item.expression, exp.Null) and isinstance(item.parent, exp.Not) == (operator == "IS NOT NULL")]
            if not matching:
                errors.append(f"predicate_binding_mismatch: {condition.node_id}")
            expected_predicates.extend(matching)
        else:
            errors.append(f"unsupported_predicate_operator: {condition.node_id}/{operator}")
    predicate_types = tuple({*comparison_classes.values(), exp.Is})
    actual_predicates = [item for clause_name in ("where", "having") if (clause := tree.args.get(clause_name)) is not None for item in clause.find_all(predicate_types)]
    if any(item not in expected_predicates for item in actual_predicates):
        errors.append("predicate_not_in_intent_graph")
    if any(not isinstance(item.this, exp.Is) for item in tree.find_all(exp.Not)):
        errors.append("unsupported_boolean_assembly: NOT requires a supported predicate contract")
    return list(dict.fromkeys(errors))
