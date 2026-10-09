# Architecture and contracts

## Shape

`web/` is a static React + TypeScript + Vite studio. `api/` is Django + Django REST Framework with a pure Python `comparison/` package. The package accepts two in-memory documents and a policy version, and returns a versioned result. Django owns input transport, limits and HTTP errors; it does not decide compatibility. There is no v1 database, account, file archive, task queue or background worker.

Suggested project tree: root planning docs, `api/config/`, `api/comparison/` (`parse`, `normalize`, `match`, `rules`, `graph`, `report`), `api/tests/fixtures/`, `web/src/` (`studio`, `graph`, `inspector`, `report`, `sample`), `web/public/sample/`, and `.github/workflows/`. Keep the engine runnable from CLI for fixture generation and tests.

## Comparison pipeline

1. Enforce transport and raw byte limits. Decode UTF-8; reject malformed JSON/YAML, aliases, duplicate mapping keys, unsupported top-level OpenAPI versions, missing local references and external references.
2. Parse to a typed intermediate contract. Preserve source JSON Pointers and distinguish absent, explicit null and false. Normalize unordered maps and set-like required/enum collections; retain ordered example arrays. Produce stable canonical digests of normalized content.
3. Index operations by literal `(method, path)`, parameters by effective location/name (case-fold headers), and schemas by local reference. Resolve effective path-level parameter overrides. Walk references with visited sets and strict work budgets.
4. Match elements without rename guesses. Run the versioned rule registry in request and response contexts. Keep structural changes, findings and coverage gaps separate; link each finding to its origin and affected operations.
5. Build a directed dependency graph from operation-to-request/response-schema and schema-to-schema use. The graph encodes contract reachability, not production traffic or proof that a client breaks. Use stable node/edge IDs. Prune the visible graph around selected findings while retaining the full graph in the result.
6. Serialize a stable result and generate JSON plus escaped, self-contained HTML from that result. Presentation timestamps stay outside deterministic comparison identity.

The rule meanings and result conclusion are defined in `compatibility-rules.md`; implementation and UI must consume that shared registry rather than rephrase verdict logic.

## HTTP contract v1

- `GET /api/health/`: readiness, engine version, policy versions; no user data.
- `GET /api/policy/v1/`: public rule metadata, supported versions and limits.
- `POST /api/compare/`: `multipart/form-data` with `baseline` and `candidate` files, or `application/json` with two document strings. Never accept remote URLs. Return a JSON `ComparisonResult` on success.
- `POST /api/report/`: accept the same bounded baseline/candidate input as compare, rerun the engine server-side, and return an escaped, self-contained HTML download. Never trust a client-edited result for report generation. JSON export serializes the compare result client-side without altering it.

Response schema: `schema_version`, `engine_version`, `policy_version`, `input_digests`, `summary` (counts, conclusion, covered/total operations), `operations`, `findings`, `coverage_gaps`, `graph` (nodes, edges), and `warnings`. Each finding carries stable ID, rule ID, classification, origin pointer(s), before/after evidence including presence flags, explanation, and affected operation IDs. Errors use stable `code`, `message`, `side` when relevant, and optional pointer; omit uploaded content. Publish a checked JSON Schema or generated TypeScript types for this response and contract-test both sides.

Use `400` for malformed/unsupported documents, `413` for byte/complexity limits, `415` for disallowed media types, `422` for valid documents outside analyzable policy only if there is truly no partial result, and `503` for transient service unavailability. Coverage uncertainty within a valid document belongs in a successful result, not an HTTP error.

## Determinism and performance

Stable IDs derive from canonical paths, contexts and rule IDs, never array position, wall time or random UUID. Sort outputs by documented keys. Set finite limits on input bytes, nesting, operations, schemas, graph nodes/edges and traversal work. Measure cold/warm comparisons with representative synthetic fixtures on free-class hardware before promising timings. A documented benchmark is evidence, not an SLA.

## Frontend state

One result state drives summary, operations list, graph, inspector and downloads. Selection is encoded in URL query/fragment for navigation within that result; browser history works. Dirty inputs mark current result stale. On compare failure retain inputs and last result only if clearly labelled as the previous comparison. The recorded bundled sample uses the exact result schema produced by the Python engine in CI, with a visible sample badge and never substitutes for a live comparison.
