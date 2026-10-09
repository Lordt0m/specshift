# SpecShift Demo Script (60–90 Seconds)

A recruiter-facing, evidence-backed demonstration of SpecShift: visual API change review for OpenAPI contracts.

---

## 1. Opening: Immediate Value Without Cold Starts (0:00 – 0:20)

> "When developers review breaking changes across microservices or shared API contracts, raw git diffs are overwhelming, and naive breaking-change badges don't explain *why* or *where* existing consumers might fail.
>
> SpecShift solves this by connecting semantic contract changes directly to dependent operations and concrete evidence.
>
> When opening the studio, an engine-generated synthetic comparison is rendered instantly from local precomputed fixtures—meaning reviewers get immediate value even if backend hosting services are waking up."

---

## 2. Tracing a Breaking Shared Schema Finding (0:20 – 0:45)

> "By default, SpecShift highlights **SC-03**, a breaking response enum addition in the shared `Order` schema.
>
> In the evidence inspector on the right, you can see the exact contract difference: the candidate added `'refunded'` to the `status` enum. Under our explicit exhaustive-client assumption, an existing client with a strict switch-case statement would encounter an unhandled status.
>
> In the central Impact Map, notice that both `GET /orders` and `GET /orders/{orderId}` are highlighted. Because the schema is shared, the engine aggregates affected operations without inflating finding counts."

---

## 3. Directionality and Explicit Uncertainty (0:45 – 1:10)

> "Directionality matters: adding an enum in a request is non-breaking (the server accepts more), but in a response, it is breaking. SpecShift enforces this directional asymmetry rigorously.
>
> Next, look at the **Coverage Gap**: `Order.discount` contains a `oneOf` composition construct. SpecShift never guesses or emits a false all-clear when encountering unsupported constructs. The gap contaminates the analysis, qualifying the audit conclusion to `Breaking changes found (1 coverage gap present)`."

---

## 4. Live Comparison and Exports (1:10 – 1:30)

> "Reviewers can click **Compare contracts** to paste or upload arbitrary OpenAPI 3.0.0–3.0.3 files. The stateless Django backend processes inputs entirely in memory under strict 1 MiB limits and duplicate-key rejection, retaining no uploaded data.
>
> Finally, reviewers can export either the raw JSON payload or a self-contained, escaped HTML report featuring no external JavaScript, full CSP compliance, and zero network calls."

---

## How to Replay This Demo Locally

1. **Start the Django Backend:**
   ```bash
   .\.venv\Scripts\python manage.py runserver 8000
   ```
2. **Start the React Frontend:**
   ```bash
   cd web
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser. The default demo view will appear immediately.
4. Run the automated test suite:
   ```bash
   .\.venv\Scripts\pytest api/tests
   ```
