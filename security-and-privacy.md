# Security and privacy boundary

Two API specifications may contain private paths, schema names, examples or tokens. Treat them as confidential and untrusted even though v1 is a public, no-account demo.

## Required controls before public upload

- State plainly before submission: both inputs are sent to the API for in-memory comparison; the service does not intentionally save them. Do not imply end-to-end encryption or guaranteed erasure from hosting infrastructure.
- Enforce initial caps of 1 MiB per document, 2 MiB combined, nesting depth 64, 2,000 operations, 5,000 schema nodes and 20,000 graph/traversal edges. These are implementation targets; tune downward after load tests on free-class hardware. Return a useful limit error, never a partial clean verdict.
- Accept UTF-8 JSON and a restricted YAML subset. Use a safe YAML loader with duplicate-key detection; reject anchors, aliases, arbitrary tags, multi-document streams and excessive depth before materializing large objects. Reject non-finite JSON numbers. Never evaluate code or construct arbitrary Python objects from input.
- Resolve only internal `#/...` references. Never fetch `http`, `https`, `file`, relative paths or other external targets. Bound traversal with visited sets and counters. A missing internal reference is an input error.
- Use request body limits at the reverse proxy/server and Django layers; set worker request timeout and memory budgets. Unit-test the bounds, then load-test near them. A timeout is an error, not `review required` or `no breaking`.
- Escape every input-derived string in React and downloaded HTML. Use text nodes, not raw HTML. Content Security Policy should prohibit inline execution for the hosted UI; self-contained HTML report should use no JavaScript and escape labels, snippets and URLs. Protect against CSV/formula injection if CSV is later added.
- Narrow CORS to the approved frontend origin(s); disallow wildcard origins. The public API needs no cookie/session authentication. Disable CSRF only on the explicitly stateless comparison endpoint if framework configuration requires it; retain secure defaults elsewhere. Set allowed hosts, HTTPS and production debug settings explicitly.
- Do not log request bodies, source snippets, file names, report contents or tokens. Log status, stable error code, duration bucket and approximate size bucket only. Keep any telemetry optional and privacy-preserving.
- Enforce a per-origin/IP best-effort throttle with bounded concurrency at the host or proxy where available. In-memory throttles reset on restart and are not a strong abuse defense; document this and preserve the ability to disable public compare if abuse threatens the free tier.
- Run dependency audit, secret scan and adversarial fixtures in CI. Pin direct dependencies and review licenses before publishing.

## Test attacks

Malformed UTF-8; duplicate keys; YAML alias expansion; deep nesting; huge lists; recursive and dangling refs; external refs; over-limit body; deliberately long identifiers; HTML/script strings in names, descriptions and examples; Unicode edge cases; repeated concurrent requests; and deliberately worst-case graph fan-out. Assert controlled errors, resource bounds and zero outbound fetch attempts.

## Operational promise

No application-level persistence in v1. Do not retain uploads or reports in local disk, DB, object storage, error reporting or analytics. Provider access logs may still exist under provider policies; mention that in privacy copy. If future saved history is requested, revisit consent, access control, retention and deletion as a new release, not a hidden extension of this one.
