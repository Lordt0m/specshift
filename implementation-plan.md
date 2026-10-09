# End-to-end implementation plan

This is one continuous build brief for Antigravity and Codex, not a ticket queue. Work through phases in order, close each automated gate with evidence in `docs/progress.md`, and keep moving without routine approval. The acceptance contract is `product-spec.md`; rule truth is `compatibility-rules.md`. If a phase exposes a factual conflict, update the relevant authority and record why before continuing.

## 0. Establish the implementation project

Use the portable project folder as the working root. Check its file status, initialize Git locally if not already initialized, add a minimal README, license choice, `.gitignore`, environment examples, dependency lockfiles and CI. Keep planning files at root. Implement `api/` and `web/` in one repository. Inspect existing local skills and use them only when they apply; they do not replace this product contract. Verify Python, Node and package versions available on the machine before pinning; Python 3.13 and Django 5.2 LTS are planned targets, not an excuse to install unsupported combinations blindly.

Gate: clean local setup instructions from a fresh checkout; no secret committed; `docs/progress.md` records versions, dates and any justified substitutions.

## 1. Freeze a demonstrable contract and fixture

Write one small baseline/candidate OpenAPI 3.0.3 pair for a fictional order API. Ensure it exercises operation addition/removal, request/response enum direction, required/optional property changes, shared schema dependency, review-required status/security change and at least one unsupported composition gap. Label fictional names and sample data. Define expected findings, rule IDs, pointers, graph edges and summary in fixture assertions before implementing the engine.

Gate: a human can read the two specs and expected result and explain every intended finding; fixture contains no real personal/customer data.

## 2. Build the pure Python comparison engine

Implement bounded parsing and version validation, canonical normalization with source pointers, indexing/matching, contextual rule evaluation, dependency graph, result conclusion and stable serialization. Let `compatibility-rules.md` and a machine-readable rule registry drive wording. Handle absent versus null, cycles, path parameter overrides, shared request/response schema uses and mixed classifications. Add a CLI that compares local fixture files and emits the result JSON. Regenerate the recorded sample through this CLI; never hand-edit a result snapshot to satisfy the UI.

Gate: every policy rule has positive, negative, reverse-direction and unchanged tests as specified in the policy. Golden fixture output is deterministic across repeated runs and key order/whitespace changes. Unsupported/unknown semantics produce explicit gaps, never silently vanish. Full engine coverage and known omissions are reported, not hidden by an arbitrary percentage target.

## 3. Expose the Django API safely

Wire the pure engine into Django REST Framework. Implement health, policy, compare and report routes with versioned response types. Enforce the limits and controls in `security-and-privacy.md`; use in-memory processing only. Return stable structured errors and validate the generated HTML report. Configure production hosts, CORS and TLS expectations. Test both pasted JSON and file upload paths.

Gate: integration and adversarial test suite passes; no outbound reference fetch can occur; logs contain no uploaded content; report escaping works with hostile fixture strings; a bounded concurrent-load run on free-class hardware has controlled failures rather than process exhaustion.

## 4. Build the studio UI

Implement the visual direction in `interface-brief.md` around the recorded synthetic sample. Start with selected finding, impact map, inspector and synchronized operation list; add input modes, compare, error/warming/stale states and downloads. React Flow supplies read-only graph interactions; the Python result alone supplies verdicts. Type-check against the API schema. Keep the sample view functional without backend connectivity, and make the live data boundary unmistakable.

Gate: every finding is navigable by mouse and keyboard; selection remains synchronized and browser history works. 360/768/1440px browser checks pass. Reduced-motion and screen-reader checks pass. An API outage leaves the sample available but produces an honest live-compare failure. JSON and HTML exports include all findings, not just filtered view.

## 5. Make quality visible and repeatable

CI runs Python formatting/lint/type checks as adopted, engine and API tests, frontend lint/type/test/build, contract fixture check, secret scan and dependency audit. Add focused browser end-to-end flows: initial sample, selected finding path, upload success, validation error, stale state, cold API simulation and export. Run accessibility checks plus manual keyboard/screen-reader pass. Document test commands, result counts, coverage gaps and limitations. Keep dependency lockfiles and attribution current.

Gate: fresh local clone can run both services and regenerate sample; CI passes; browser paths pass; no unreviewed critical dependency/license issue; evidence recorded in `docs/progress.md` and release checklist.

## 6. Prepare a recruiter-grade demo

Write an honest `docs/demo.md`: 60–90 second walkthrough, expected selected finding, why it matters, engine architecture, one uncertainty example and how to reproduce. Add clear README with local run, sample screenshots or short clip if produced, supported scope, privacy, and methodology. Write a small explanation of directional compatibility and its limitations. The project shows engineering judgement and visual craft without claiming real users or measured outcomes not observed.

Gate: a reviewer can understand the product from the first viewport and README, replay the sample locally, inspect tests and trace one finding from source pointer to affected operation to report.

## 7. Deploy only after the free-plan gate

Recheck provider terms immediately before deployment. With Ayotomiwa's authorization for external account/repository/deployment actions, use Cloudflare Pages Free for static UI and Render Free web service for stateless Django API, only if no payment details or chargeable resources are required. Configure API URL, allowed hosts/CORS and health endpoint. Do not deploy a database. Verify actual URL, cold start, sample availability, live comparison, HTML download and CORS in production. See `hosting-and-operations.md`.

Gate: live public URLs and all production smoke checks recorded. If account, card, quota or permission blocks hosting, finish every local gate and report the precise remaining human action. Do not substitute a paid service or present a local build as live.

## 8. Publish the portfolio case study and hand over

Only after live verification and permission to edit the portfolio, add a concise case study linking demo and source. Explain the problem, bounded rules, graph, safe parsing, test approach and free-tier cold-start caveat. Include real screenshots. Complete `docs/release-checklist.md` with actual evidence and any failed/deferred gates. Tag a local release and optionally publish it only with authorization. Keep the local run path usable if hosting later disappears.

Gate: README, live demo and portfolio tell the same truthful story; no synthetic example is represented as customer data; current limitations are explicit.

## Stop conditions

Stop only the dependent action if external authorization, credentials, a required card/payment, or a material change to compatibility/security/scope is needed. Continue all independent work. For an ordinary implementation choice, decide, document the reason briefly, and proceed. A failed gate triggers repair and rerun; it is not waived by a plausible-looking screenshot. Do not ask Ayotomiwa to approve individual tickets.
