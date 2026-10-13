# SpecShift release checklist — updated 12 October 2026

Current status is a preview release. `release-verification.md` contains the evidence and limitations. Historical Antigravity PASS assertions are superseded by this checklist.

| Gate | Status | Evidence |
|---|---|---|
| Local setup and production builds | PASS | Pinned Python dependencies, strict TypeScript/Vite build, pip check and production npm audit |
| Fictional fixture and recorded sample | PASS | Golden assertions and complete sample-output equality in CI |
| Implemented engine regression suite | PASS | 76 tests in CI for 3a6e70a; directional scenarios, graph/ref bounds, hostile input, exact parameter source positions |
| Local engine 1.0.1 follow-up | PASS | 168 local backend tests; 92 new reverse/nested/shared/bound/cycle and operation-contract cases; CLI sample equality |
| Exhaustive policy conformance | OPEN | Selected SC-01–SC-13 and operation-contract matrices pass; not all combinations, constraints or unsupported constructs are proved |
| API boundaries and escaped exports | PASS | Input/work limits, memory-only uploads, throttling, kill switch and escaped HTML tests |
| Focus and responsive smoke checks | PASS | Empty-input validation, dialog focus, Shift+Tab containment, Escape restoration, 360px and 1440px checks; mobile overflow repaired |
| Local accessibility follow-up | PASS, BOUNDED | 12 DOM/interaction tests; three axe jsdom states excluding contrast/map; browser focus, validation, real map activation and 320px dialog checks |
| Full accessibility conformance | OPEN | Actual screen-reader, comprehensive rendered contrast, forced colors, reduced motion, zoom and full interaction coverage not completed |
| Follow-up deployment | NOT PERFORMED | Local engine 1.0.1 and UI changes were not pushed/deployed; production rows below are 9 October historical evidence |
| Public source | PASS | Explicitly authorized public repository at https://github.com/Lordt0m/specshift |
| Free hosting | PASS | Static Cloudflare Pages project; Render Free web service, one instance and no database/disk add-on |
| Production smoke checks | PASS | Sample, HTTPS headers, API CORS, fictional comparison and script-free HTML report |
| Provider usage/billing review | OPEN | No paid resource requested; existing Render services share workspace allowance. Account-wide overage settings not verified |
| Final finding-selection follow-up | PASS | d432e7e CI passed; hosted removed-operation comparison keeps its finding selected and displays exact evidence |
| Portfolio publication | DRAFT ONLY | Case study prepared under outputs/specshift; no portfolio write performed |
