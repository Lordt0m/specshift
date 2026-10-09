# SpecShift &mdash; Visual API Change-Review Studio

SpecShift is a visual API change-review studio that connects OpenAPI contract changes directly to dependent operations and concrete compatibility evidence.

Rather than presenting noisy git diffs or unexplained badges, SpecShift evaluates directional compatibility under an authoritative, versioned rule registry and visualizes contract reachability through an interactive dependency graph.

---

## Key Capabilities

1. **Directional Compatibility Analysis (Policy v1)**
   - Distinguishes request vs. response semantics (e.g. adding an enum member is accepted in requests but breaking in responses under exhaustive-client assumptions).
   - Rules cover operations (OP-01, OP-02), parameters (PA-01&ndash;PA-03), request bodies (RB-01, RB-02), media types (MD-01, MD-02), response status codes (RS-01, RS-02), and schema constraints (SC-01&ndash;SC-13).

2. **Explicit Uncertainty & Coverage Gaps**
   - Preserves uncertainty: unsupported constructs (`oneOf`, `allOf`, `anyOf`, discriminators) produce explicit coverage gaps rather than false clean verdicts.
   - Gaps contaminate completeness for any operation depending on the construct.

3. **Multi-Operation Reachability Graph**
   - Visualizes contract dependencies between operations and shared schemas.
   - Aggregates affected operations for shared schemas without inflating finding counts.

4. **Security & Privacy by Design**
   - Stateless, in-memory processing: uploaded files are never persisted to disk, database, or cloud storage.
   - Strict bounds: 1 MiB per document, 2 MiB combined document content, 4 MiB wire-format cap including escaping/transport overhead, nesting depth 64 and finite graph/work budgets.
   - Safe parsing: rejects YAML anchors and aliases, duplicate mapping keys, and non-finite numbers.
   - Prohibits external `$ref` URLs (`http`, `https`, `file`, relative paths); only internal `#/` references resolved.
   - Self-contained HTML exports contain zero external CDNs, zero JavaScript, and full string escaping.

5. **Instant Local Sample**
   - The studio opens immediately with a precomputed synthetic comparison generated directly by the pure Python engine in CI, remaining useful during API cold starts.

---

## Tech Stack

- **Backend / Engine:** Python 3.13, Django 6.1.2 (installed implementation version), Django REST Framework, PyYAML
- **Frontend:** React 19, TypeScript, Vite, `@xyflow/react`
- **Testing:** Pytest, pytest-django

---

## Local Setup & Quickstart

### Prerequisites
- Python 3.13+
- Node.js 20+ / 22+

### 1. Clone & Set Up Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux

# Install pinned dependencies
pip install -r api/requirements.txt

# Run system checks
python manage.py check

# Start development server on port 8000
python manage.py runserver 8000
```

### 2. Set Up & Run Frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. The studio will render with the synthetic order API sample immediately.

---

## Running Tests & Verifications

```bash
# Run backend test suite (76 automated tests at the current release checkpoint)
pytest api/tests

# Regenerate sample fixture from engine CLI
python -m api.comparison.cli api/tests/fixtures/demo/baseline.yaml api/tests/fixtures/demo/candidate.yaml -o web/public/sample/result.json

# Build frontend and run TypeScript strict type check
cd web
npm run build
```

---

## Supported Scope & Limitations

- **Supported Format:** OpenAPI 3.0.0 &ndash; 3.0.3 documents in UTF-8 JSON or restricted YAML.
- **Out of Scope (v1):** OpenAPI 2.0 (Swagger) and OpenAPI 3.1+; external `$ref` fetching; arbitrary graph editing; user accounts; persistent storage.
- **Reachability Notice:** A dependency graph shows contract reachability; reachability indicates where consumers *may* be affected, not proof that a specific runtime client fails.
- **Conservative boundaries:** Non-schema referenced contract objects, readOnly/writeOnly properties, implicit schema types and unknown schema constraints produce coverage gaps. Unclassified semantic edits require review. The parser checks bounded structure and references; it is not an exhaustive OpenAPI validator.
- **Preview release:** https://specshift.pages.dev/ with a stateless API on Render Free. See `docs/release-verification.md` for verified checks and outstanding conformance/accessibility work. The free API can take about a minute to wake; unsupported or unclassified constructs still require human review.

---

## License

MIT License &copy; 2026 Ayotomiwa Ojo.
