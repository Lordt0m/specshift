"""Directed dependency graph for OpenAPI contracts.

Encodes contract reachability between operations, request/response bodies,
and referenced schemas with deterministic node and edge IDs.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from .parse import DocumentSizeLimitError


@dataclass
class GraphNode:
    id: str
    type: str  # "operation" or "schema"
    label: str
    pointer: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "label": self.label,
        }
        if self.pointer:
            d["pointer"] = self.pointer
        if self.method:
            d["method"] = self.method
        if self.path:
            d["path"] = self.path
        return d


@dataclass
class GraphEdge:
    id: str
    source: str
    target: str
    label: str
    context: str  # "request", "response", "reference"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "context": self.context,
        }


class DependencyGraph:
    """Manages nodes, directed edges, and reachability queries."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, GraphEdge] = {}
        # Adjacency: source -> set of target ids
        self.adjacency: dict[str, set[str]] = {}
        # Reverse adjacency: target -> set of source ids
        self.reverse_adjacency: dict[str, set[str]] = {}

    def add_node(self, node: GraphNode) -> None:
        if len(self.nodes) >= 7000 and node.id not in self.nodes:
            raise DocumentSizeLimitError("Graph node limit exceeded.")
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self.adjacency[node.id] = set()
            self.reverse_adjacency[node.id] = set()

    def add_edge(self, edge: GraphEdge) -> None:
        if len(self.edges) >= 20000 and edge.id not in self.edges:
            raise DocumentSizeLimitError("Graph edge limit exceeded.")
        if edge.id not in self.edges:
            self.edges[edge.id] = edge
            self.adjacency.setdefault(edge.source, set()).add(edge.target)
            self.reverse_adjacency.setdefault(edge.target, set()).add(edge.source)

    def get_ancestor_operations(self, start_node_id: str) -> list[str]:
        """Find all operation node display strings (e.g. 'GET /orders') that can reach start_node_id."""
        visited: set[str] = set()
        queue: list[str] = [start_node_id]
        ops: set[str] = set()

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)

            node = self.nodes.get(curr)
            if node and node.type == "operation":
                ops.add(node.label)

            for parent in self.reverse_adjacency.get(curr, set()):
                if parent not in visited:
                    queue.append(parent)

        return sorted(ops)

    def to_dict(self) -> dict[str, Any]:
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.id)
        sorted_edges = sorted(self.edges.values(), key=lambda e: e.id)
        return {
            "nodes": [n.to_dict() for n in sorted_nodes],
            "edges": [e.to_dict() for e in sorted_edges],
        }
