# SpecShift release checklist — 9 October 2026

Current status is a preview release. `release-verification.md` contains the evidence and limitations. Historical Antigravity PASS assertions are superseded by this checklist.

| Gate | Status | Evidence |
|---|---|---|
| Local setup and production builds | PASS | Pinned Python dependencies, strict TypeScript/Vite build, pip check and production npm audit |
| Fictional fixture and recorded sample | PASS | Golden assertions and complete sample-output equality in CI |
| Implemented engine regression suite | PASS | 76 tests in CI for 3a6e70a; directional scenarios, graph/ref bounds, hostile input, exact parameter source positions |
| Exhaustive policy conformance | OPEN | Broader reverse, nested and shared-context matrix is incomplete; gaps and unclassified edits require review |
| API boundaries and escaped exports | PASS | Input/work limits, memory-only uploads, throttling, kill switch and escaped HTML tests |
| Focus and responsive smoke checks | PASS | Empty-input validation, dialog focus, Shift+Tab containment, Escape restoration, 360px and 1440px checks; mobile overflow repaired |
| Full accessibility conformance | OPEN | Screen-reader and comprehensive contrast/interaction audit not completed |
| Public source | PASS | Explicitly authorized public repository at https://github.com/Lordt0m/specshift |
| Free hosting | PASS | Static Cloudflare Pages project; Render Free web service, one instance and no database/disk add-on |
| Production smoke checks | PASS | Sample, HTTPS headers, API CORS, fictional comparison and script-free HTML report |
| Provider usage/billing review | OPEN | No paid resource requested; existing Render services share workspace allowance. Account-wide overage settings not verified |
| Final finding-selection follow-up | PASS | d432e7e CI passed; hosted removed-operation comparison keeps its finding selected and displays exact evidence |
| Portfolio publication | DRAFT ONLY | Case study prepared under outputs/specshift; no portfolio write performed |
