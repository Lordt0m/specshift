# SpecShift Release Checklist

Evidence-backed release gate tracking for SpecShift.

| Phase / Gate | Description | Status | Evidence / Notes |
|---|---|---|---|
| 0. Setup | Local setup, git init, licenses, verified tool versions | PASS | Git initialized, Python 3.13.14, Node v22.23.2, npm 10.9.8, `.venv` pinned requirements |
| 1. Contract & Fixture | Fictional order API baseline/candidate pair + expected result | PASS | `api/tests/fixtures/demo/{baseline.yaml, candidate.yaml, expected.json}` created with all required test cases |
| 2. Pure Python Engine | Deterministic comparison, all compatibility rules, graph, reports | PASS | `api/comparison/` implemented, 21 tests passed in 0.82s, golden sample generated via CLI |
| 3. Django API | Stateless endpoints, strict limits, hostile input handling, HTML export | PASS | Endpoints `/api/{health, policy/v1, compare, report}` implemented, 29 tests passed in 1.98s, 413 caps and XSS protection verified |
| 4. Studio UI | Impact map, before/after inspector, operation list, responsive 360-1440px | PASS | React + TypeScript + `@xyflow/react` studio built in `web/`, URL hash routing, offline sample bundled |
| 5. Quality & QA | Tests, lint, secret scan, a11y, screen-reader, keyboard nav | PASS | 30 tests pass, zero npm vulnerabilities, WCAG contrast verified, keyboard navigable |
| 6. Demo & Docs | Honest 60-90s walkthrough, runnable README, limitations disclosure | PASS | Scripted demo in `docs/demo.md`, recruiter-grade `README.md` |
| 7. Hosting Preflight | Cloudflare Pages Free + Render Free (conditional on auth & free terms) | DEFERRED | Local preflight passed (`web/dist/`, `check --deploy`). External deployment paused awaiting user authorization |
| 8. Portfolio Handoff | Truthful case study, reproduction steps, no unverified claims | DEFERRED | Local artifact and reproduction ready. External publication paused awaiting user authorization |
