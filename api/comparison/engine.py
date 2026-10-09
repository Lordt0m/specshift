"""Pure Python comparison engine for OpenAPI 3.0 specifications.

Implements directional compatibility analysis under Compatibility Policy v1.
"""

from dataclasses import dataclass, field
import hashlib
import time
from typing import Any, Optional

from .graph import DependencyGraph, GraphNode, GraphEdge
from .normalize import (
    ABSENT,
    append_pointer,
    compute_canonical_digest,
    escape_pointer_token,
    get_presence_kind,
)
from .parse import parse_specification, resolve_pointer
from .rules import RULE_REGISTRY, POLICY_VERSION, Rule

SCHEMA_VERSION = "1.0.0"
ENGINE_VERSION = "1.0.0"


class ComparisonTimeoutError(ValueError):
    pass


@dataclass
class Finding:
    id: str
    rule_id: str
    classification: str  # "breaking", "review_required", "non_breaking"
    context: str  # "operation", "request", "response", "metadata"
    origin_pointer: Optional[str]
    candidate_pointer: Optional[str]
    before: Any
    before_presence: str  # "present", "absent", "null"
    after: Any
    after_presence: str  # "present", "absent", "null"
    explanation: str
    policy_rule: str
    affected_operations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "classification": self.classification,
            "context": self.context,
            "origin_pointer": self.origin_pointer,
            "candidate_pointer": self.candidate_pointer,
            "before": None if self.before is ABSENT else self.before,
            "before_presence": self.before_presence,
            "after": None if self.after is ABSENT else self.after,
            "after_presence": self.after_presence,
            "explanation": self.explanation,
            "policy_rule": self.policy_rule,
            "affected_operations": sorted(list(set(self.affected_operations))),
        }


@dataclass
class CoverageGap:
    id: str
    pointer: str
    construct: str
    reason: str
    affected_operations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pointer": self.pointer,
            "construct": self.construct,
            "reason": self.reason,
            "affected_operations": sorted(list(set(self.affected_operations))),
        }


def _make_stable_id(prefix: str, *parts: Any) -> str:
    cleaned = [str(p).lower().replace(" ", "-").replace("/", "-").replace("~", "-").strip("-_#") for p in parts if p]
    base = f"{prefix}-" + "-".join(filter(None, cleaned))
    # sanitize characters
    readable = "".join(c if c.isalnum() or c == "-" else "_" for c in base)
    import json
    digest = hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()[:16]
    return readable[:120] + "-" + digest


class ComparisonEngine:
    def __init__(self, baseline_doc: dict[str, Any], candidate_doc: dict[str, Any]):
        self.baseline = baseline_doc
        self.candidate = candidate_doc
        self.graph = DependencyGraph()
        self.findings_map: dict[str, Finding] = {}
        self.coverage_gaps_map: dict[str, CoverageGap] = {}
        self.warnings: list[str] = []
        self.visited_schema_pairs: set[tuple[str, str, str]] = set()
        self.graph_visited: set[tuple[int, str, str]] = set()
        self.deadline = time.monotonic() + 8

    def _check_budget(self):
        from .parse import DocumentSizeLimitError
        if time.monotonic() > self.deadline:
            raise ComparisonTimeoutError("Comparison exceeded its work deadline. Use smaller documents.")
        if len(self.findings_map) + len(self.coverage_gaps_map) > 10000:
            raise DocumentSizeLimitError("Comparison exceeds the 10,000-finding/gap limit.")

    def run(self) -> dict[str, Any]:
        # 1. Build graph for both specs
        self._build_dependency_graph(self.baseline, is_baseline=True)
        self._build_dependency_graph(self.candidate, is_baseline=False)

        # 2. Extract and index operations
        base_ops = self._index_operations(self.baseline, "#")
        cand_ops = self._index_operations(self.candidate, "#")

        all_op_keys = sorted(list(set(base_ops.keys()) | set(cand_ops.keys())))

        # Referenced parameter/body/response/path objects are not yet indexed
        # semantically. Surface that limitation even in an unchanged document.
        all_labels = [f"{method} {path}" for method, path in all_op_keys]
        for document in (self.baseline, self.candidate):
            pending = [(document, "#")]
            while pending:
                value, pointer = pending.pop()
                self._check_budget()
                if isinstance(value, dict):
                    ref = value.get("$ref")
                    if ref and not ref.startswith("#/components/schemas/"):
                        self._record_gap(CoverageGap(
                            id=_make_stable_id("gap", "reference-scope", pointer), pointer=pointer,
                            construct="referenced-contract-object",
                            reason="Non-schema reference semantics are outside the implemented index. Review required.",
                            affected_operations=all_labels,
                        ))
                    pending.extend((child, append_pointer(pointer, key)) for key, child in value.items())
                elif isinstance(value, list):
                    pending.extend((child, append_pointer(pointer, index)) for index, child in enumerate(value))

        for op_key in all_op_keys:
            base_op = base_ops.get(op_key)
            cand_op = cand_ops.get(op_key)
            method, path = op_key
            op_label = f"{method} {path}"

            if base_op is not None and cand_op is None:
                # OP-01: Remove method/path
                rule = RULE_REGISTRY["OP-01"]
                fid = _make_stable_id("finding", "op-01", method, path)
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.request_classification,
                        context="operation",
                        origin_pointer=base_op["pointer"],
                        candidate_pointer=None,
                        before=op_label,
                        before_presence="present",
                        after=None,
                        after_presence="absent",
                        explanation=f"Operation '{op_label}' was removed in candidate.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
            elif base_op is None and cand_op is not None:
                # OP-02: Add method/path
                rule = RULE_REGISTRY["OP-02"]
                fid = _make_stable_id("finding", "op-02", method, path)
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.request_classification,
                        context="operation",
                        origin_pointer=None,
                        candidate_pointer=cand_op["pointer"],
                        before=None,
                        before_presence="absent",
                        after=op_label,
                        after_presence="present",
                        explanation=f"Operation '{op_label}' was added in candidate.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
            else:
                # Both exist: compare operation details
                assert base_op is not None and cand_op is not None
                self._compare_retained_operation(base_op, cand_op, op_label)

        # Preserve changed semantics not yet covered by a precise rule.
        self._audit_unclassified_changes(base_ops, cand_ops)

        # 3. Compute summary and conclusion
        findings_list = sorted(self.findings_map.values(), key=lambda f: f.id)
        gaps_list = sorted(self.coverage_gaps_map.values(), key=lambda g: g.id)

        breaking_count = sum(1 for f in findings_list if f.classification == "breaking")
        review_count = sum(1 for f in findings_list if f.classification == "review_required")
        non_breaking_count = sum(1 for f in findings_list if f.classification == "non_breaking")
        gap_count = len(gaps_list)

        if breaking_count > 0:
            if gap_count > 0:
                conclusion = f"Breaking changes found ({gap_count} coverage gap{'s' if gap_count > 1 else ''} present)"
            else:
                conclusion = "Breaking changes found"
        elif review_count > 0 or gap_count > 0:
            conclusion = "Review required; compatibility not established"
        else:
            conclusion = "No breaking changes detected by policy v1"

        total_ops = len(all_op_keys)
        # Covered operations = operations without gaps
        gap_affected_ops = {op for g in gaps_list for op in g.affected_operations}
        covered_ops = len([k for k in all_op_keys if f"{k[0]} {k[1]}" not in gap_affected_ops])

        return {
            "schema_version": SCHEMA_VERSION,
            "engine_version": ENGINE_VERSION,
            "policy_version": POLICY_VERSION,
            "input_digests": {
                "baseline": compute_canonical_digest(self.baseline),
                "candidate": compute_canonical_digest(self.candidate),
            },
            "summary": {
                "breaking_count": breaking_count,
                "review_count": review_count,
                "non_breaking_count": non_breaking_count,
                "total_findings": len(findings_list),
                "coverage_gap_count": gap_count,
                "total_operations": total_ops,
                "covered_operations": covered_ops,
                "conclusion": conclusion,
            },
            "operations": [
                {
                    "method": k[0],
                    "path": k[1],
                    "status": "removed" if k in base_ops and k not in cand_ops
                    else "added" if k in cand_ops and k not in base_ops
                    else "retained"
                }
                for k in all_op_keys
            ],
            "findings": [f.to_dict() for f in findings_list],
            "coverage_gaps": [g.to_dict() for g in gaps_list],
            "graph": self.graph.to_dict(),
            "warnings": self.warnings,
        }

    def _record_finding(self, finding: Finding) -> None:
        self._check_budget()
        # Evidence is the exact value at the pointer, not a derived boolean or
        # subset which could be mistaken for the original source fragment.
        for side, document, pointer in (("before", self.baseline, finding.origin_pointer), ("after", self.candidate, finding.candidate_pointer)):
            from .parse import MissingInternalReferenceError
            try:
                value = resolve_pointer(document, pointer) if pointer else ABSENT
            except MissingInternalReferenceError:
                value = ABSENT
            setattr(finding, side, value)
            setattr(finding, side + "_presence", get_presence_kind(value))
        if finding.id in self.findings_map:
            # Aggregate affected operations without duplicating finding
            existing = self.findings_map[finding.id]
            for op in finding.affected_operations:
                if op not in existing.affected_operations:
                    existing.affected_operations.append(op)
        else:
            self.findings_map[finding.id] = finding

    def _audit_unclassified_changes(self, base_ops, cand_ops):
        """Conservatively expose edits outside the precise rule branches."""
        known = {p for f in self.findings_map.values() for p in (f.origin_pointer, f.candidate_pointer) if p}
        operations = sorted({f"{method} {path}" for method, path in set(base_ops) | set(cand_ops)})

        def walk(before, after, pointer):
            self._check_budget()
            if before == after:
                return
            if pointer in known:
                return
            if pointer.rsplit("/", 1)[-1] in {"enum", "required"} and isinstance(before, list) and isinstance(after, list):
                import json
                if {json.dumps(x, sort_keys=True) for x in before} == {json.dumps(x, sort_keys=True) for x in after}:
                    return
            if (isinstance(before, dict) or before is ABSENT) and (isinstance(after, dict) or after is ABSENT):
                b_map = {} if before is ABSENT else before
                c_map = {} if after is ABSENT else after
                for key in sorted(set(b_map) | set(c_map)):
                    walk(b_map.get(key, ABSENT), c_map.get(key, ABSENT), append_pointer(pointer, key))
                return
            metadata = pointer.rsplit("/", 1)[-1] in {"description", "summary", "example", "tags", "title"} or pointer == "#/info/version"
            # Existing precise findings cover child changes such as enum members.
            if any(pointer.startswith(p + "/") for p in known):
                return
            rule = RULE_REGISTRY["MT-01" if metadata else "UN-01"]
            self._record_finding(Finding(
                id=_make_stable_id("finding", rule.id, pointer), rule_id=rule.id,
                classification="non_breaking" if metadata else "review_required",
                context="metadata" if metadata else "operation",
                origin_pointer=None if before is ABSENT else pointer,
                candidate_pointer=None if after is ABSENT else pointer,
                before=before, after=after,
                before_presence=get_presence_kind(before), after_presence=get_presence_kind(after),
                explanation="Metadata changed." if metadata else "This edit is not fully classified by the implemented rules; review its exact evidence.",
                policy_rule=rule.title, affected_operations=operations,
            ))

        walk(self.baseline, self.candidate, "#")

    def _record_gap(self, gap: CoverageGap) -> None:
        self._check_budget()
        if gap.id in self.coverage_gaps_map:
            existing = self.coverage_gaps_map[gap.id]
            for op in gap.affected_operations:
                if op not in existing.affected_operations:
                    existing.affected_operations.append(op)
        else:
            self.coverage_gaps_map[gap.id] = gap

    def _build_dependency_graph(self, doc: dict[str, Any], is_baseline: bool) -> None:
        paths = doc.get("paths", {})
        if not isinstance(paths, dict):
            return

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op_data in path_item.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch", "options", "head", "trace"}:
                    continue
                if not isinstance(op_data, dict):
                    continue

                method_upper = method.upper()
                op_label = f"{method_upper} {path}"
                op_node_id = f"op:{method_upper}_{path}"
                self.graph.add_node(
                    GraphNode(
                        id=op_node_id,
                        type="operation",
                        label=op_label,
                        method=method_upper,
                        path=path,
                    )
                )

                # Request body schema edges
                req_body = op_data.get("requestBody", {})
                if isinstance(req_body, dict):
                    content = req_body.get("content", {})
                    if isinstance(content, dict):
                        for mt, mt_data in content.items():
                            if isinstance(mt_data, dict) and "schema" in mt_data:
                                self._link_graph_schema(op_node_id, mt_data["schema"], doc, "request", f"request: {mt}")

                # Response schema edges
                responses = op_data.get("responses", {})
                if isinstance(responses, dict):
                    for status, resp_data in responses.items():
                        if isinstance(resp_data, dict):
                            content = resp_data.get("content", {})
                            if isinstance(content, dict):
                                for mt, mt_data in content.items():
                                    if isinstance(mt_data, dict) and "schema" in mt_data:
                                        self._link_graph_schema(
                                            op_node_id, mt_data["schema"], doc, "response", f"response: {status}"
                                        )

    def _link_graph_schema(
        self, parent_node_id: str, schema_obj: Any, doc: dict[str, Any], context: str, edge_label: str
    ) -> None:
        self._check_budget()
        if not isinstance(schema_obj, dict):
            return

        ref = schema_obj.get("$ref")
        if ref and isinstance(ref, str):
            schema_name = ref.split("/")[-1]
            node_id = f"schema:{schema_name}"
            self.graph.add_node(
                GraphNode(
                    id=node_id,
                    type="schema",
                    label=schema_name,
                    pointer=ref,
                )
            )
            edge_id = f"edge:{parent_node_id}->{node_id}:{context}"
            self.graph.add_edge(GraphEdge(id=edge_id, source=parent_node_id, target=node_id, label=edge_label, context=context))
            # Recurse into referenced schema if inside components
            key = (id(doc), ref, context)
            if key not in self.graph_visited:
                self.graph_visited.add(key)
                resolved = resolve_pointer(doc, ref)
                self._trace_schema_dependencies(node_id, resolved, doc, context)
        elif schema_obj.get("type") == "array" and "items" in schema_obj:
            self._link_graph_schema(parent_node_id, schema_obj["items"], doc, context, edge_label)
        elif "properties" in schema_obj and isinstance(schema_obj["properties"], dict):
            for prop_name, prop_data in schema_obj["properties"].items():
                self._link_graph_schema(parent_node_id, prop_data, doc, context, f"property: {prop_name}")

    def _trace_schema_dependencies(self, schema_node_id: str, schema_data: Any, doc: dict[str, Any], context: str) -> None:
        if not isinstance(schema_data, dict):
            return

        # Check items
        if schema_data.get("type") == "array" and "items" in schema_data:
            self._link_graph_schema(schema_node_id, schema_data["items"], doc, context, "items")

        # Check properties
        props = schema_data.get("properties", {})
        if isinstance(props, dict):
            for p_name, p_schema in props.items():
                if isinstance(p_schema, dict):
                    if "$ref" in p_schema:
                        self._link_graph_schema(schema_node_id, p_schema, doc, context, f"prop: {p_name}")
                    elif p_schema.get("type") == "array" and "items" in p_schema:
                        self._link_graph_schema(schema_node_id, p_schema["items"], doc, context, f"prop: {p_name}[]")

    def _index_operations(self, doc: dict[str, Any], doc_pointer: str) -> dict[tuple[str, str], dict[str, Any]]:
        ops: dict[tuple[str, str], dict[str, Any]] = {}
        paths = doc.get("paths", {})
        if not isinstance(paths, dict):
            return ops

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            path_pointer = append_pointer(f"{doc_pointer}/paths", path)
            path_params = path_item.get("parameters", [])
            if not isinstance(path_params, list):
                path_params = []

            for method, op_data in path_item.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch", "options", "head", "trace"}:
                    continue
                if not isinstance(op_data, dict):
                    continue

                method_upper = method.upper()
                op_pointer = append_pointer(path_pointer, method.lower())

                # Resolve effective parameters (operation params override path params)
                eff_params: dict[tuple[str, str], dict[str, Any]] = {}
                param_pointers: dict[tuple[str, str], str] = {}
                for index, p in enumerate(path_params):
                    if isinstance(p, dict) and "name" in p and "in" in p:
                        key = (p["in"], p["name"].lower() if p["in"] == "header" else p["name"])
                        eff_params[key] = p
                        param_pointers[key] = append_pointer(append_pointer(path_pointer, "parameters"), index)
                
                op_params = op_data.get("parameters", [])
                if isinstance(op_params, list):
                    for index, p in enumerate(op_params):
                        if isinstance(p, dict) and "name" in p and "in" in p:
                            key = (p["in"], p["name"].lower() if p["in"] == "header" else p["name"])
                            eff_params[key] = p
                            param_pointers[key] = append_pointer(append_pointer(op_pointer, "parameters"), index)

                ops[(method_upper, path)] = {
                    "method": method_upper,
                    "path": path,
                    "pointer": op_pointer,
                    "data": op_data,
                    "parameters": eff_params,
                    "parameter_pointers": param_pointers,
                }
        return ops

    def _compare_retained_operation(
        self, base_op: dict[str, Any], cand_op: dict[str, Any], op_label: str
    ) -> None:
        base_data = base_op["data"]
        cand_data = cand_op["data"]

        # 1. operationId
        base_op_id = base_data.get("operationId")
        cand_op_id = cand_data.get("operationId")
        if base_op_id != cand_op_id:
            rule = RULE_REGISTRY["MT-02"]
            fid = _make_stable_id("finding", "mt-02", op_label, "opid")
            self._record_finding(
                Finding(
                    id=fid,
                    rule_id=rule.id,
                    classification=rule.request_classification,
                    context="operation",
                    origin_pointer=append_pointer(base_op["pointer"], "operationId"),
                    candidate_pointer=append_pointer(cand_op["pointer"], "operationId"),
                    before=base_op_id,
                    before_presence=get_presence_kind(base_op_id),
                    after=cand_op_id,
                    after_presence=get_presence_kind(cand_op_id),
                    explanation=f"operationId changed from '{base_op_id}' to '{cand_op_id}'. Generated SDK or client methods may change name.",
                    policy_rule=rule.title,
                    affected_operations=[op_label],
                )
            )

        # 2. Parameters
        base_params = base_op["parameters"]
        cand_params = cand_op["parameters"]
        all_param_keys = set(base_params.keys()) | set(cand_params.keys())

        for p_key in sorted(all_param_keys):
            bp = base_params.get(p_key)
            cp = cand_params.get(p_key)
            p_in, p_name = p_key
            bp_pointer = base_op["parameter_pointers"].get(p_key)
            cp_pointer = cand_op["parameter_pointers"].get(p_key)

            if bp is not None and cp is None:
                # PA-03: Remove parameter
                rule = RULE_REGISTRY["PA-03"]
                fid = _make_stable_id("finding", "pa-03", op_label, p_in, p_name)
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.request_classification,
                        context="request",
                        origin_pointer=bp_pointer,
                        candidate_pointer=None,
                        before=bp,
                        before_presence="present",
                        after=None,
                        after_presence="absent",
                        explanation=f"Parameter '{p_name}' in {p_in} was removed.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
            elif bp is None and cp is not None:
                is_req = cp.get("required", False) or p_in == "path"
                if is_req:
                    # PA-01: Add required parameter
                    rule = RULE_REGISTRY["PA-01"]
                    fid = _make_stable_id("finding", "pa-01", op_label, p_in, p_name)
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=rule.request_classification,
                            context="request",
                            origin_pointer=None,
                            candidate_pointer=cp_pointer,
                            before=None,
                            before_presence="absent",
                            after=cp,
                            after_presence="present",
                            explanation=f"Required parameter '{p_name}' in {p_in} was added.",
                            policy_rule=rule.title,
                            affected_operations=[op_label],
                        )
                    )
                else:
                    # PA-02: Add optional parameter
                    rule = RULE_REGISTRY["PA-02"]
                    fid = _make_stable_id("finding", "pa-02", op_label, p_in, p_name)
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=rule.request_classification,
                            context="request",
                            origin_pointer=None,
                            candidate_pointer=cp_pointer,
                            before=None,
                            before_presence="absent",
                            after=cp,
                            after_presence="present",
                            explanation=f"Optional parameter '{p_name}' in {p_in} was added.",
                            policy_rule=rule.title,
                            affected_operations=[op_label],
                        )
                    )
            else:
                assert bp is not None and cp is not None
                b_req = bp.get("required", False) or p_in == "path"
                c_req = cp.get("required", False) or p_in == "path"
                if not b_req and c_req:
                    # PA-01: Optional to required
                    rule = RULE_REGISTRY["PA-01"]
                    fid = _make_stable_id("finding", "pa-01", op_label, p_in, p_name, "req")
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=rule.request_classification,
                            context="request",
                            origin_pointer=append_pointer(bp_pointer, "required"),
                            candidate_pointer=append_pointer(cp_pointer, "required"),
                            before=False,
                            before_presence="present",
                            after=True,
                            after_presence="present",
                            explanation=f"Parameter '{p_name}' in {p_in} made required.",
                            policy_rule=rule.title,
                            affected_operations=[op_label],
                        )
                    )
                elif b_req and not c_req:
                    # PA-02: Required to optional
                    rule = RULE_REGISTRY["PA-02"]
                    fid = _make_stable_id("finding", "pa-02", op_label, p_in, p_name, "opt")
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=rule.request_classification,
                            context="request",
                            origin_pointer=append_pointer(bp_pointer, "required"),
                            candidate_pointer=append_pointer(cp_pointer, "required"),
                            before=True,
                            before_presence="present",
                            after=False,
                            after_presence="present",
                            explanation=f"Parameter '{p_name}' in {p_in} made optional.",
                            policy_rule=rule.title,
                            affected_operations=[op_label],
                        )
                    )

                # Compare parameter schemas
                b_schema = bp.get("schema")
                c_schema = cp.get("schema")
                if b_schema and c_schema:
                    self._compare_schemas(
                        b_schema,
                        c_schema,
                        append_pointer(bp_pointer, "schema"),
                        append_pointer(cp_pointer, "schema"),
                        context="request",
                        fallback_affected_ops=[op_label],
                    )

        # 3. Request Body
        b_body = base_data.get("requestBody")
        c_body = cand_data.get("requestBody")

        if b_body is None and c_body is not None:
            c_req = c_body.get("required", False) if isinstance(c_body, dict) else False
            if c_req:
                rule = RULE_REGISTRY["RB-01"]
                fid = _make_stable_id("finding", "rb-01", op_label)
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.request_classification,
                        context="request",
                        origin_pointer=None,
                        candidate_pointer=append_pointer(cand_op["pointer"], "requestBody"),
                        before=None,
                        before_presence="absent",
                        after=True,
                        after_presence="present",
                        explanation=f"Required request body added for '{op_label}'.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
            else:
                rule = RULE_REGISTRY["RB-02"]
                fid = _make_stable_id("finding", "rb-02", op_label)
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.request_classification,
                        context="request",
                        origin_pointer=None,
                        candidate_pointer=append_pointer(cand_op["pointer"], "requestBody"),
                        before=None,
                        before_presence="absent",
                        after=False,
                        after_presence="present",
                        explanation=f"Optional request body added for '{op_label}'.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
        elif b_body is not None and c_body is not None:
            b_req = b_body.get("required", False) if isinstance(b_body, dict) else False
            c_req = c_body.get("required", False) if isinstance(c_body, dict) else False
            if not b_req and c_req:
                rule = RULE_REGISTRY["RB-01"]
                fid = _make_stable_id("finding", "rb-01", op_label, "req")
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.request_classification,
                        context="request",
                        origin_pointer=append_pointer(append_pointer(base_op["pointer"], "requestBody"), "required"),
                        candidate_pointer=append_pointer(append_pointer(cand_op["pointer"], "requestBody"), "required"),
                        before=False,
                        before_presence="present",
                        after=True,
                        after_presence="present",
                        explanation=f"Request body made required for '{op_label}'.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
            elif b_req and not c_req:
                rule = RULE_REGISTRY["RB-02"]
                fid = _make_stable_id("finding", "rb-02", op_label, "opt")
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.request_classification,
                        context="request",
                        origin_pointer=append_pointer(append_pointer(base_op["pointer"], "requestBody"), "required"),
                        candidate_pointer=append_pointer(append_pointer(cand_op["pointer"], "requestBody"), "required"),
                        before=True,
                        before_presence="present",
                        after=False,
                        after_presence="present",
                        explanation=f"Request body made optional for '{op_label}'.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )

            # Compare media types and schemas
            b_content = b_body.get("content", {}) if isinstance(b_body, dict) else {}
            c_content = c_body.get("content", {}) if isinstance(c_body, dict) else {}

            all_req_mt = set(b_content.keys()) | set(c_content.keys())
            for mt in sorted(all_req_mt):
                if mt in b_content and mt not in c_content:
                    rule = RULE_REGISTRY["MD-01"]
                    fid = _make_stable_id("finding", "md-01", op_label, mt)
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=rule.request_classification,
                            context="request",
                            origin_pointer=append_pointer(append_pointer(append_pointer(base_op["pointer"], "requestBody"), "content"), mt),
                            candidate_pointer=None,
                            before=mt,
                            before_presence="present",
                            after=None,
                            after_presence="absent",
                            explanation=f"Accepted request media type '{mt}' was removed.",
                            policy_rule=rule.title,
                            affected_operations=[op_label],
                        )
                    )
                elif mt not in b_content and mt in c_content:
                    rule = RULE_REGISTRY["MD-02"]
                    fid = _make_stable_id("finding", "md-02", op_label, mt)
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=rule.request_classification,
                            context="request",
                            origin_pointer=None,
                            candidate_pointer=append_pointer(append_pointer(append_pointer(cand_op["pointer"], "requestBody"), "content"), mt),
                            before=None,
                            before_presence="absent",
                            after=mt,
                            after_presence="present",
                            explanation=f"Accepted request media type '{mt}' was added.",
                            policy_rule=rule.title,
                            affected_operations=[op_label],
                        )
                    )
                else:
                    bs = b_content[mt].get("schema") if isinstance(b_content[mt], dict) else None
                    cs = c_content[mt].get("schema") if isinstance(c_content[mt], dict) else None
                    if bs and cs:
                        self._compare_schemas(
                            bs,
                            cs,
                            append_pointer(append_pointer(append_pointer(append_pointer(base_op["pointer"], "requestBody"), "content"), mt), "schema"),
                            append_pointer(append_pointer(append_pointer(append_pointer(cand_op["pointer"], "requestBody"), "content"), mt), "schema"),
                            context="request",
                            fallback_affected_ops=[op_label],
                        )

        # 4. Responses
        b_resps = base_data.get("responses", {}) if isinstance(base_data, dict) else {}
        c_resps = cand_data.get("responses", {}) if isinstance(cand_data, dict) else {}
        all_status = set(b_resps.keys()) | set(c_resps.keys())

        for st in sorted(all_status):
            if st in b_resps and st not in c_resps:
                rule = RULE_REGISTRY["RS-01"]
                fid = _make_stable_id("finding", "rs-01", op_label, st)
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.response_classification,
                        context="response",
                        origin_pointer=append_pointer(append_pointer(base_op["pointer"], "responses"), st),
                        candidate_pointer=None,
                        before=str(st),
                        before_presence="present",
                        after=None,
                        after_presence="absent",
                        explanation=f"Documented response status code '{st}' was removed.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
            elif st not in b_resps and st in c_resps:
                rule = RULE_REGISTRY["RS-02"]
                fid = _make_stable_id("finding", "rs-02", op_label, st)
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=rule.response_classification,
                        context="response",
                        origin_pointer=None,
                        candidate_pointer=append_pointer(append_pointer(cand_op["pointer"], "responses"), st),
                        before=None,
                        before_presence="absent",
                        after=str(st),
                        after_presence="present",
                        explanation=f"Added response status code '{st}'. Clients may encounter an unhandled status code.",
                        policy_rule=rule.title,
                        affected_operations=[op_label],
                    )
                )
            else:
                br_val = b_resps[st]
                cr_val = c_resps[st]
                b_content = br_val.get("content", {}) if isinstance(br_val, dict) else {}
                c_content = cr_val.get("content", {}) if isinstance(cr_val, dict) else {}
                all_resp_mt = set(b_content.keys()) | set(c_content.keys())

                for mt in sorted(all_resp_mt):
                    if mt in b_content and mt not in c_content:
                        rule = RULE_REGISTRY["RS-01"]
                        fid = _make_stable_id("finding", "rs-01", op_label, st, mt)
                        self._record_finding(
                            Finding(
                                id=fid,
                                rule_id=rule.id,
                                classification=rule.response_classification,
                                context="response",
                                origin_pointer=append_pointer(append_pointer(append_pointer(append_pointer(base_op["pointer"], "responses"), st), "content"), mt),
                                candidate_pointer=None,
                                before=mt,
                                before_presence="present",
                                after=None,
                                after_presence="absent",
                                explanation=f"Documented response media type '{mt}' under status '{st}' was removed.",
                                policy_rule=rule.title,
                                affected_operations=[op_label],
                            )
                        )
                    elif mt not in b_content and mt in c_content:
                        rule = RULE_REGISTRY["RS-02"]
                        fid = _make_stable_id("finding", "rs-02", op_label, st, mt)
                        self._record_finding(
                            Finding(
                                id=fid,
                                rule_id=rule.id,
                                classification=rule.response_classification,
                                context="response",
                                origin_pointer=None,
                                candidate_pointer=append_pointer(append_pointer(append_pointer(append_pointer(cand_op["pointer"], "responses"), st), "content"), mt),
                                before=None,
                                before_presence="absent",
                                after=mt,
                                after_presence="present",
                                explanation=f"Documented response media type '{mt}' under status '{st}' was added.",
                                policy_rule=rule.title,
                                affected_operations=[op_label],
                            )
                        )
                    else:
                        bs = b_content[mt].get("schema") if isinstance(b_content[mt], dict) else None
                        cs = c_content[mt].get("schema") if isinstance(c_content[mt], dict) else None
                        if bs and cs:
                            self._compare_schemas(
                                bs,
                                cs,
                                append_pointer(append_pointer(append_pointer(append_pointer(append_pointer(base_op["pointer"], "responses"), st), "content"), mt), "schema"),
                                append_pointer(append_pointer(append_pointer(append_pointer(append_pointer(cand_op["pointer"], "responses"), st), "content"), mt), "schema"),
                                context="response",
                                fallback_affected_ops=[op_label],
                            )

    def _get_affected_ops_for_pointer(self, pointer: Optional[str], fallback_ops: list[str]) -> list[str]:
        if not pointer:
            return sorted(fallback_ops)
        
        # Check if pointer points to components/schemas/<name>
        if "#/components/schemas/" in pointer:
            parts = pointer.split("#/components/schemas/")[1].split("/")
            schema_name = parts[0]
            node_id = f"schema:{schema_name}"
            ancestors = self.graph.get_ancestor_operations(node_id)
            if ancestors:
                return sorted(ancestors)
        return sorted(fallback_ops)

    def _compare_schemas(
        self,
        b_schema: dict[str, Any],
        c_schema: dict[str, Any],
        b_ptr: str,
        c_ptr: str,
        context: str,  # "request" or "response"
        fallback_affected_ops: list[str],
    ) -> None:
        # Resolve $ref if present
        b_ref = b_schema.get("$ref")
        c_ref = c_schema.get("$ref")

        eff_b_ptr = b_ref if (b_ref and isinstance(b_ref, str)) else b_ptr
        eff_c_ptr = c_ref if (c_ref and isinstance(c_ref, str)) else c_ptr

        pair_key = (eff_b_ptr, eff_c_ptr, context)
        if pair_key in self.visited_schema_pairs:
            for finding in self.findings_map.values():
                if finding.context == context and finding.origin_pointer and (
                    finding.origin_pointer == eff_b_ptr or finding.origin_pointer.startswith(eff_b_ptr + "/")
                ):
                    finding.affected_operations.extend(fallback_affected_ops)
            return
        self.visited_schema_pairs.add(pair_key)

        # Dereference for property comparison
        resolved_b = resolve_pointer(self.baseline, b_ref) if b_ref else b_schema
        resolved_c = resolve_pointer(self.candidate, c_ref) if c_ref else c_schema

        if not isinstance(resolved_b, dict) or not isinstance(resolved_c, dict):
            return

        affected_ops = fallback_affected_ops
        # Contextual aggregation follows actual visits, not the union graph's
        # request/response ancestors. A shared ref may have different verdicts.
        for finding in self.findings_map.values():
            if finding.context == context and finding.origin_pointer and (
                finding.origin_pointer == eff_b_ptr or finding.origin_pointer.startswith(eff_b_ptr + "/")
            ):
                finding.affected_operations.extend(affected_ops)

        # Check coverage gaps (composition: oneOf, allOf, anyOf, not, discriminator)
        supported = {"type", "properties", "required", "items", "enum", "nullable", "minimum", "maximum", "minLength", "maxLength", "minItems", "maxItems", "additionalProperties", "description", "title", "example", "default", "$ref"}
        unsupported = (set(resolved_b) | set(resolved_c)) - supported
        if (not resolved_b.get("type") or not resolved_c.get("type")) and not unsupported.intersection({"oneOf", "allOf", "anyOf", "not"}):
            unsupported.add("implicit-type")
        if any(isinstance(schema.get("additionalProperties"), dict) for schema in (resolved_b, resolved_c)):
            unsupported.add("additionalProperties")
        for comp_kw in sorted(unsupported):
            if comp_kw in resolved_b or comp_kw in resolved_c or comp_kw == "implicit-type":
                gap_id = _make_stable_id("gap", comp_kw, eff_b_ptr)
                self._record_gap(
                    CoverageGap(
                        id=gap_id,
                        pointer=eff_b_ptr if comp_kw in resolved_b else eff_c_ptr,
                        construct=comp_kw,
                        reason=f"Schema composition construct '{comp_kw}' is unsupported by policy v1.",
                        affected_operations=affected_ops,
                    )
                )

        # SC-01: Change explicit type
        b_type = resolved_b.get("type")
        c_type = resolved_c.get("type")
        if b_type != c_type and b_type is not None and c_type is not None:
            rule = RULE_REGISTRY["SC-01"]
            fid = _make_stable_id("finding", "sc-01", context, eff_b_ptr, "type")
            self._record_finding(
                Finding(
                    id=fid,
                    rule_id=rule.id,
                    classification=rule.request_classification if context == "request" else rule.response_classification,
                    context=context,
                    origin_pointer=append_pointer(eff_b_ptr, "type"),
                    candidate_pointer=append_pointer(eff_c_ptr, "type"),
                    before=b_type,
                    before_presence="present",
                    after=c_type,
                    after_presence="present",
                    explanation=f"Explicit type changed from '{b_type}' to '{c_type}'.",
                    policy_rule=rule.title,
                    affected_operations=affected_ops,
                )
            )

        # SC-02 / SC-03: Enum members
        b_enum = resolved_b.get("enum")
        c_enum = resolved_c.get("enum")
        if isinstance(b_enum, list) and isinstance(c_enum, list):
            import json
            b_set = {json.dumps(value, sort_keys=True) for value in b_enum}
            c_set = {json.dumps(value, sort_keys=True) for value in c_enum}
            removed_enums = [json.loads(value) for value in sorted(b_set - c_set)]
            added_enums = [json.loads(value) for value in sorted(c_set - b_set)]

            if removed_enums:
                rule = RULE_REGISTRY["SC-02"]
                fid = _make_stable_id("finding", "sc-02", context, eff_b_ptr, "enum-rem")
                cls = rule.request_classification if context == "request" else rule.response_classification
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=cls,
                        context=context,
                        origin_pointer=append_pointer(eff_b_ptr, "enum"),
                        candidate_pointer=append_pointer(eff_c_ptr, "enum"),
                        before=b_enum,
                        before_presence="present",
                        after=c_enum,
                        after_presence="present",
                        explanation=f"Removed enum member(s): {', '.join(map(str, removed_enums))}.",
                        policy_rule=rule.title,
                        affected_operations=affected_ops,
                    )
                )

            if added_enums:
                rule = RULE_REGISTRY["SC-03"]
                fid = _make_stable_id("finding", "sc-03", context, eff_b_ptr, "enum-add")
                cls = rule.request_classification if context == "request" else rule.response_classification
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=cls,
                        context=context,
                        origin_pointer=append_pointer(eff_b_ptr, "enum"),
                        candidate_pointer=append_pointer(eff_c_ptr, "enum"),
                        before=b_enum,
                        before_presence="present",
                        after=c_enum,
                        after_presence="present",
                        explanation=f"Added enum member '{added_enums[0]}' in {context}. Breaking under exhaustive-client assumption."
                        if context == "response" else f"Added enum member(s): {', '.join(map(str, added_enums))}.",
                        policy_rule=rule.title,
                        affected_operations=affected_ops,
                    )
                )

        # SC-08 / SC-09: Nullable
        b_null = resolved_b.get("nullable", False)
        c_null = resolved_c.get("nullable", False)
        if not b_null and c_null:
            # SC-08: Allow null where formerly forbidden
            rule = RULE_REGISTRY["SC-08"]
            fid = _make_stable_id("finding", "sc-08", context, eff_b_ptr, "nullable")
            cls = rule.request_classification if context == "request" else rule.response_classification
            self._record_finding(
                Finding(
                    id=fid,
                    rule_id=rule.id,
                    classification=cls,
                    context=context,
                    origin_pointer=append_pointer(eff_b_ptr, "nullable"),
                    candidate_pointer=append_pointer(eff_c_ptr, "nullable"),
                    before=False,
                    before_presence="present",
                    after=True,
                    after_presence="present",
                    explanation="Allowed null where formerly forbidden.",
                    policy_rule=rule.title,
                    affected_operations=affected_ops,
                )
            )
        elif b_null and not c_null:
            # SC-09: Forbid null where formerly allowed
            rule = RULE_REGISTRY["SC-09"]
            fid = _make_stable_id("finding", "sc-09", context, eff_b_ptr, "nullable")
            cls = rule.request_classification if context == "request" else rule.response_classification
            self._record_finding(
                Finding(
                    id=fid,
                    rule_id=rule.id,
                    classification=cls,
                    context=context,
                    origin_pointer=append_pointer(eff_b_ptr, "nullable"),
                    candidate_pointer=append_pointer(eff_c_ptr, "nullable"),
                    before=True,
                    before_presence="present",
                    after=False,
                    after_presence="present",
                    explanation="Forbade null where formerly allowed.",
                    policy_rule=rule.title,
                    affected_operations=affected_ops,
                )
            )

        # SC-10 / SC-11: Bounds (minimum, maximum, minLength, maxLength, minItems, maxItems)
        bound_pairs = [
            ("minimum", True),  # higher is tighter
            ("minLength", True),
            ("minItems", True),
            ("maximum", False),  # lower is tighter
            ("maxLength", False),
            ("maxItems", False),
        ]
        for bound_key, higher_is_tighter in bound_pairs:
            b_val = resolved_b.get(bound_key)
            c_val = resolved_c.get(bound_key)
            if b_val is not None and c_val is not None and b_val != c_val:
                is_tightened = (c_val > b_val) if higher_is_tighter else (c_val < b_val)
                if is_tightened:
                    rule = RULE_REGISTRY["SC-10"]
                    fid = _make_stable_id("finding", "sc-10", context, eff_b_ptr, bound_key)
                    cls = rule.request_classification if context == "request" else rule.response_classification
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=cls,
                            context=context,
                            origin_pointer=append_pointer(eff_b_ptr, bound_key),
                            candidate_pointer=append_pointer(eff_c_ptr, bound_key),
                            before=b_val,
                            before_presence="present",
                            after=c_val,
                            after_presence="present",
                            explanation=f"{context.capitalize()} bound '{bound_key}' was tightened from {b_val} to {c_val}.",
                            policy_rule=rule.title,
                            affected_operations=affected_ops,
                        )
                    )
                else:
                    rule = RULE_REGISTRY["SC-11"]
                    fid = _make_stable_id("finding", "sc-11", context, eff_b_ptr, bound_key)
                    cls = rule.request_classification if context == "request" else rule.response_classification
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=cls,
                            context=context,
                            origin_pointer=append_pointer(eff_b_ptr, bound_key),
                            candidate_pointer=append_pointer(eff_c_ptr, bound_key),
                            before=b_val,
                            before_presence="present",
                            after=c_val,
                            after_presence="present",
                            explanation=f"{context.capitalize()} bound '{bound_key}' was loosened from {b_val} to {c_val}.",
                            policy_rule=rule.title,
                            affected_operations=affected_ops,
                        )
                    )

        # SC-12 / SC-13: additionalProperties
        b_add_prop = resolved_b.get("additionalProperties", True)
        c_add_prop = resolved_c.get("additionalProperties", True)
        if isinstance(b_add_prop, bool) and isinstance(c_add_prop, bool):
            if b_add_prop and not c_add_prop:
                # SC-12: true/default to false
                rule = RULE_REGISTRY["SC-12"]
                fid = _make_stable_id("finding", "sc-12", context, eff_b_ptr)
                cls = rule.request_classification if context == "request" else rule.response_classification
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=cls,
                        context=context,
                        origin_pointer=append_pointer(eff_b_ptr, "additionalProperties"),
                        candidate_pointer=append_pointer(eff_c_ptr, "additionalProperties"),
                        before=True,
                        before_presence="present",
                        after=False,
                        after_presence="present",
                        explanation="additionalProperties changed from true to false (schema closed).",
                        policy_rule=rule.title,
                        affected_operations=affected_ops,
                    )
                )
            elif not b_add_prop and c_add_prop:
                # SC-13: false to true/default
                rule = RULE_REGISTRY["SC-13"]
                fid = _make_stable_id("finding", "sc-13", context, eff_b_ptr)
                cls = rule.request_classification if context == "request" else rule.response_classification
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=cls,
                        context=context,
                        origin_pointer=append_pointer(eff_b_ptr, "additionalProperties"),
                        candidate_pointer=append_pointer(eff_c_ptr, "additionalProperties"),
                        before=False,
                        before_presence="present",
                        after=True,
                        after_presence="present",
                        explanation="additionalProperties changed from false to true (schema opened).",
                        policy_rule=rule.title,
                        affected_operations=affected_ops,
                    )
                )

        # Properties & Required evaluation
        b_props = resolved_b.get("properties", {}) if isinstance(resolved_b.get("properties"), dict) else {}
        c_props = resolved_c.get("properties", {}) if isinstance(resolved_c.get("properties"), dict) else {}
        b_req_list = set(resolved_b.get("required", [])) if isinstance(resolved_b.get("required"), list) else set()
        c_req_list = set(resolved_c.get("required", [])) if isinstance(resolved_c.get("required"), list) else set()

        all_prop_keys = set(b_props.keys()) | set(c_props.keys())

        for p_name in sorted(all_prop_keys):
            bp = b_props.get(p_name)
            cp = c_props.get(p_name)
            b_is_req = p_name in b_req_list
            c_is_req = p_name in c_req_list

            # These directional fields are intentionally conservative until
            # the contextual projection is fully implemented and tested.
            if any(isinstance(prop, dict) and (prop.get("readOnly") or prop.get("writeOnly")) for prop in (bp, cp)):
                self._record_gap(CoverageGap(
                    id=_make_stable_id("gap", "directional-field", context, eff_b_ptr, p_name),
                    pointer=append_pointer(append_pointer(eff_b_ptr, "properties"), p_name),
                    construct="readOnly/writeOnly",
                    reason="Directional property projection requires review; no property compatibility verdict is asserted.",
                    affected_operations=affected_ops,
                ))
                continue

            if bp is None and cp is not None:
                # Added property
                if c_is_req:
                    # SC-04: Add required property
                    rule = RULE_REGISTRY["SC-04"]
                    fid = _make_stable_id("finding", "sc-04", context, eff_c_ptr, p_name)
                    # For request: breaking. For response: non-breaking if open, breaking if closed baseline object
                    cls = "breaking" if context == "request" else ("breaking" if not b_add_prop else "non_breaking")
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=cls,
                            context=context,
                            origin_pointer=append_pointer(eff_b_ptr, "required") if "required" in resolved_b else eff_b_ptr,
                            candidate_pointer=append_pointer(eff_c_ptr, "required"),
                            before=False,
                            before_presence="present",
                            after=True,
                            after_presence="present",
                            explanation=f"{context.capitalize()} property '{p_name}' was made required or added as required.",
                            policy_rule=rule.title,
                            affected_operations=affected_ops,
                        )
                    )
                else:
                    # SC-07: Add optional property
                    rule = RULE_REGISTRY["SC-07"]
                    fid = _make_stable_id("finding", "sc-07", context, eff_c_ptr, p_name)
                    cls = "non_breaking" if context == "request" else ("breaking" if not b_add_prop else "non_breaking")
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=cls,
                            context=context,
                            origin_pointer=None,
                            candidate_pointer=append_pointer(append_pointer(eff_c_ptr, "properties"), p_name),
                            before=None,
                            before_presence="absent",
                            after=cp,
                            after_presence="present",
                            explanation=f"Optional property '{p_name}' was added to schema.",
                            policy_rule=rule.title,
                            affected_operations=affected_ops,
                        )
                    )
            elif bp is not None and cp is None:
                # Removed property: SC-06
                rule = RULE_REGISTRY["SC-06"]
                fid = _make_stable_id("finding", "sc-06", context, eff_b_ptr, p_name)
                cls = "review_required" if context == "request" else ("breaking" if b_is_req else "review_required")
                self._record_finding(
                    Finding(
                        id=fid,
                        rule_id=rule.id,
                        classification=cls,
                        context=context,
                        origin_pointer=append_pointer(append_pointer(eff_b_ptr, "properties"), p_name),
                        candidate_pointer=None,
                        before=bp,
                        before_presence="present",
                        after=None,
                        after_presence="absent",
                        explanation=f"Property '{p_name}' was removed from schema.",
                        policy_rule=rule.title,
                        affected_operations=affected_ops,
                    )
                )
            else:
                assert bp is not None and cp is not None
                # Check required status change
                if not b_is_req and c_is_req:
                    # SC-04: Optional to required
                    rule = RULE_REGISTRY["SC-04"]
                    fid = _make_stable_id("finding", "sc-04", context, eff_b_ptr, p_name)
                    cls = "breaking" if context == "request" else "non_breaking"
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=cls,
                            context=context,
                            origin_pointer=append_pointer(eff_b_ptr, "required"),
                            candidate_pointer=append_pointer(eff_c_ptr, "required"),
                            before=False,
                            before_presence="present",
                            after=True,
                            after_presence="present",
                            explanation=f"{context.capitalize()} property '{p_name}' was made required or added as required.",
                            policy_rule=rule.title,
                            affected_operations=affected_ops,
                        )
                    )
                elif b_is_req and not c_is_req:
                    # SC-05: Required to optional
                    rule = RULE_REGISTRY["SC-05"]
                    fid = _make_stable_id("finding", "sc-05", context, eff_b_ptr, p_name)
                    cls = "non_breaking" if context == "request" else "breaking"
                    self._record_finding(
                        Finding(
                            id=fid,
                            rule_id=rule.id,
                            classification=cls,
                            context=context,
                            origin_pointer=append_pointer(eff_b_ptr, "required"),
                            candidate_pointer=append_pointer(eff_c_ptr, "required"),
                            before=True,
                            before_presence="present",
                            after=False,
                            after_presence="present",
                            explanation=f"{context.capitalize()} property '{p_name}' changed from required to optional, removing a guarantee."
                            if context == "response" else f"Request property '{p_name}' made optional.",
                            policy_rule=rule.title,
                            affected_operations=affected_ops,
                        )
                    )

                # Recurse into property schemas
                self._compare_schemas(
                    bp,
                    cp,
                    append_pointer(append_pointer(eff_b_ptr, "properties"), p_name),
                    append_pointer(append_pointer(eff_c_ptr, "properties"), p_name),
                    context=context,
                    fallback_affected_ops=affected_ops,
                )

        # Array items recursion
        if resolved_b.get("type") == "array" and resolved_c.get("type") == "array":
            b_items = resolved_b.get("items")
            c_items = resolved_c.get("items")
            if isinstance(b_items, dict) and isinstance(c_items, dict):
                self._compare_schemas(
                    b_items,
                    c_items,
                    append_pointer(eff_b_ptr, "items"),
                    append_pointer(eff_c_ptr, "items"),
                    context=context,
                    fallback_affected_ops=affected_ops,
                )


def compare_specifications(baseline_content: str | bytes, candidate_content: str | bytes) -> dict[str, Any]:
    """Top-level entrypoint for comparing baseline and candidate OpenAPI contracts."""
    baseline_doc = parse_specification(baseline_content, name="baseline")
    candidate_doc = parse_specification(candidate_content, name="candidate")
    engine = ComparisonEngine(baseline_doc, candidate_doc)
    return engine.run()
