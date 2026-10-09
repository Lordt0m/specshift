# Independent release verification — 9 October 2026

Codex took over deployment following Ayotomiwa's authorization. The original Antigravity phase statuses are historical assertions, not sufficient evidence for release. This record supersedes those assertions where they conflict.

## Completed checks and corrections

- Initial 30-test baseline reproduced. Expanded backend suite: 76 tests pass in GitHub CI for commit 3a6e70a, including 26 directional schema scenarios, inherited and reordered parameter evidence, unchanged controls, recursive refs, dangling unused refs, nonfinite values, unknown constraints, exact escaped pointers, stable-ID collisions, canonical enum ordering, public throttling, input types, kill switch and deadline failure.
- Production frontend TypeScript/Vite build passed after fixing API-origin configuration, escaped sample HTML export, backend regeneration of live HTML exports, dirty-input marking, upload keyboard access, responsive dialog columns, modal focus handling and read-only graph refresh when the result/selection changes.
- Parser rejects non-JSON scalars and checks all reference targets. YAML dates remain strings. Graph traversal has visited sets and node/edge limits; comparison work has a deadline and findings budget.
- Exact before/after values now come from source pointers. Unclassified edits remain review-required; metadata edits remain visible. The regenerated fictional sample has 5 breaking, 3 review-required and 3 non-breaking findings, 5 operations and 1 coverage gap. Three operations depend on the unsupported discount composition, so only 2 operations are fully covered.
- No tracked environment secret files found; targeted credential-pattern scan of 104 historical blobs and tracked working files found no matches. This is a bounded scan, not a universal guarantee.
- `pip check` passed; npm production dependency audit found zero vulnerabilities. GitHub CI passed for public release commit `b8ad936af3193a0c0a2ad8c638621d67ea3ebffa`.
- Local frontend and API health returned HTTP 200. After initial browser connection failures, interactive checks succeeded: unchanged local comparison, hosted removed-operation comparison, empty-input validation, dialog initial focus, Shift+Tab containment, Escape focus restoration, and 360px/1440px visual checks. A mobile file-input overflow was fixed and verified deployed. These checks do not establish screen-reader or full accessibility conformance.
- Public studio: https://specshift.pages.dev/ . Direct Pages deployment, static assets only. Production sample and CSP/nosniff headers verified over HTTPS. API CORS permits that origin. Render Free API is live at https://specshift-api.onrender.com; PUBLIC_COMPARE_ENABLED=true. Fictional order comparison returned the expected 11 findings and one gap; HTML export returned 200, included evidence and contained no script.

## Pending gates

- Final application commit d432e7e passed CI and is live on Pages/Render. Hosted removed-operation comparison retained automatic selection and exact evidence after the selection fix.
- Broader all-rule reverse/nested/shared-context conformance and screen-reader testing remain incomplete. This is a preview release, not a certification of exhaustive OpenAPI compatibility or accessibility.
- The report API returned valid escaped HTML, but browser automation timed out waiting for the downloaded file and showed no visible error. File-download capture is unverified.
- Provider billing/usage check: explicit Free resource selection is necessary but does not prove the account has no overage billing risk. Existing Render free services share the 750-hour workspace allowance.

## Operational controls

Wire cap is 4 MiB, including multipart/JSON overhead; individual input content stays 1 MiB. Inputs remain memory-only, admission is one active comparison per process, and the bounded in-memory throttle permits 10 calls/minute per observed peer. It resets on restart; shared proxies can throttle multiple visitors together. `PUBLIC_COMPARE_ENABLED=false` disables live comparisons while retaining the static example.

Render WSGI startup generates a cryptographically random instance-local Django key only when no configured key exists. This is suitable only while the app has no sessions or persisted signatures. An authentication/history release must supply a persistent secret.
