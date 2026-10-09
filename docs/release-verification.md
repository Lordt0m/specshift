# Independent release verification — 9 October 2026

Codex took over deployment following Ayotomiwa's authorization. The original Antigravity phase statuses are historical assertions, not sufficient evidence for release. This record supersedes those assertions where they conflict.

## Completed checks and corrections

- Initial 30-test baseline reproduced. Expanded backend suite: 74 tests passed in the latest completed run, including 26 directional schema scenarios, unchanged controls, recursive refs, dangling unused refs, nonfinite values, unknown constraints, exact escaped pointers, stable-ID collisions, canonical enum ordering, public throttling, input types, kill switch and deadline failure.
- Production frontend TypeScript/Vite build passed after fixing API-origin configuration, escaped sample HTML export, backend regeneration of live HTML exports, dirty-input marking, upload keyboard access, responsive dialog columns, modal focus handling and read-only graph refresh when the result/selection changes.
- Parser rejects non-JSON scalars and checks all reference targets. YAML dates remain strings. Graph traversal has visited sets and node/edge limits; comparison work has a deadline and findings budget.
- Exact before/after values now come from source pointers. Unclassified edits remain review-required; metadata edits remain visible. The regenerated fictional sample has 5 breaking, 3 review-required and 3 non-breaking findings, 5 operations and 1 coverage gap. Three operations depend on the unsupported discount composition, so only 2 operations are fully covered.
- No tracked environment secret files found; targeted credential-pattern scan of 104 historical blobs and tracked working files found no matches. This is a bounded scan, not a universal guarantee.
- `pip check` passed; npm production dependency audit found zero vulnerabilities. GitHub CI passed for public release commit `b8ad936af3193a0c0a2ad8c638621d67ea3ebffa`.
- Local frontend and API health returned HTTP 200. Browser accessibility tree displayed the sample, graph and exact inspector evidence. Browser interaction commands repeatedly timed out; responsive screenshots, interactive end-to-end and screen-reader checks remain unverified, not passed.

## Pending gates

- Verify CI again for subsequent release changes.
- Browser interaction/responsive QA and all-rule reverse/nested/shared-context coverage beyond the current suite.
- Public deployment and production smoke checks. Cloudflare CLI still reports an expired token after the user's sign-in; verify the correct CLI configuration scope before asking the user to repeat sign-in.
- Render Free service `specshift-api` was provisioned on 9 October 2026 at `https://specshift-api.onrender.com`. Deployment of b8ad936 is live; production `/api/health/` returned 200 and `/api/compare/` returned the expected 503. `PUBLIC_COMPARE_ENABLED=false` keeps live comparisons disabled while release gates remain open.
- Provider billing/usage check: explicit Free resource selection is necessary but does not prove the account has no overage billing risk. Existing Render free services share the 750-hour workspace allowance.

## Operational controls

Wire cap is 4 MiB, including multipart/JSON overhead; individual input content stays 1 MiB. Inputs remain memory-only, admission is one active comparison per process, and the bounded in-memory throttle permits 10 calls/minute per observed peer. It resets on restart; shared proxies can throttle multiple visitors together. `PUBLIC_COMPARE_ENABLED=false` disables live comparisons while retaining the static example.

Render WSGI startup generates a cryptographically random instance-local Django key only when no configured key exists. This is suitable only while the app has no sessions or persisted signatures. An authentication/history release must supply a persistent secret.
