# Synthetic demo and evidence

The demo is a fictional API contract change, not a client engagement or production incident. Use a compact order API with `GET /orders/{orderId}`, `POST /orders` and `GET /orders`; a shared `Order` schema, request `CreateOrder` schema and nested `Address` or `LineItem` dependency. Name entities generically. No actual names, emails, keys or proprietary payloads.

## Required scenario

Baseline and candidate together should include:

- A removed operation and an added operation, showing why method/path identity matters.
- A newly required request field and one tightened request bound, both traceable to an operation.
- A response enum addition under the explicit exhaustive-client assumption, plus a response required-to-optional change.
- One shared schema touched in more than one operation, to show affected-operation aggregation without duplicate findings.
- An operationId change and response-status or security change classified `Review required`.
- A reachable `oneOf`/`allOf` change or other excluded construct that creates a coverage gap and prevents an all-clear.
- An unchanged control and a formatting-only variant that produce no semantic finding.

Keep `api/tests/fixtures/demo/baseline.yaml`, `candidate.yaml` and `expected.json` as source. A fixture test asserts IDs, classifications, pointers, affected operations, graph edges, coverage count and conclusion. Generate `web/public/sample/result.json` with the engine CLI in CI; fail if the checked-in artifact differs. Add `sample/README` or an on-page explanation that the result was recorded from the engine. An optional seeded default selection should be a breaking shared-schema finding because it makes the graph's value immediately legible.

## Walkthrough

1. Open the hosted UI; the recorded synthetic comparison renders immediately.
2. Select the shared-schema finding; read its before/after evidence, policy assumption and source pointer.
3. Follow the highlighted dependency to two affected operations; point out that reachability is not proof of client failure.
4. Select the coverage gap and show why the conclusion is qualified.
5. Swap to local test files, compare through Django, then download JSON/HTML report. If the free API is waking, explain the limitation honestly rather than hiding it.

## Recruiter-facing evidence

Use a short README case study and real screenshots only after UI exists. Link tests and the versioned rule table. Any performance number needs a reproducible benchmark command, input size, environment and observed result. Do not claim users, customers, adoption or zero downtime.
