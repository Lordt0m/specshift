"""Pointer normalization, sentinel representation, and canonical digests."""

import hashlib
import json
from typing import Any

# Sentinel representing an absent field or attribute
class _Absent:
    def __repr__(self) -> str:
        return "<ABSENT>"
    def __str__(self) -> str:
        return "absent"

ABSENT = _Absent()


def escape_pointer_token(token: str | int) -> str:
    """Escape token for RFC 6901 JSON pointer."""
    s = str(token)
    return s.replace("~", "~0").replace("/", "~1")


def unescape_pointer_token(token: str) -> str:
    """Unescape RFC 6901 JSON pointer token."""
    return token.replace("~1", "/").replace("~0", "~")


def append_pointer(base_pointer: str, token: str | int) -> str:
    """Append a token to a base pointer, handling leading #/ if needed."""
    escaped = escape_pointer_token(token)
    if not base_pointer or base_pointer == "#":
        return f"#/{escaped}"
    return f"{base_pointer}/{escaped}"


def compute_canonical_digest(document: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 digest of normalized document."""
    def canonical(value, key=None):
        if isinstance(value, dict):
            return {k: canonical(v, k) for k, v in value.items()}
        if isinstance(value, list):
            items = [canonical(v) for v in value]
            return sorted(items, key=lambda v: json.dumps(v, sort_keys=True)) if key in {"enum", "required"} else items
        return value
    canonical_json = json.dumps(canonical(document), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def get_presence_kind(val: Any) -> str:
    """Return presence classification: 'absent', 'null', or 'present'."""
    if val is ABSENT:
        return "absent"
    if val is None:
        return "null"
    return "present"
