# Product specification

## Problem and intended user

A backend developer reviewing an OpenAPI change needs to know what changed, where existing clients may be affected, and why. A raw text diff is noisy; an unexplained red badge hides assumptions. SpecShift connects semantic findings to exact contract fragments and a dependency graph. This is an independent portfolio tool, not evidence of a real customer's usage.

## First release

One public studio with a meaningful synthetic example already open. Users can select a finding, follow dependencies, inspect baseline/candidate values, and download a report. They can replace the example with two local files or pasted documents and run the Python API comparison. The browser checks size for convenience; the server enforces it.

Supported: OpenAPI 3.0.0-3.0.3 documents, UTF-8 JSON or restricted YAML, JSON media-type schemas, operation/parameter/request/response semantics described by the rule set, internal references and bounded cyclic graphs. Restrict to this explicit version allowlist; other 3.0 patch versions require verification and tests before addition.

The baseline-to-candidate direction is visible beside both inputs, all results, and exports. Swapping inputs recomputes; it is not a visual toggle. Validation failures name the side and pointer and leave inputs available to correct. A previous successful result is marked stale after an input edit and cannot masquerade as the edited comparison.

## User journey

1. Open the studio: recorded synthetic result and its policy are available without API startup.
2. Select a breaking finding: graph highlights affected operations and the inspector shows exact old/new values and rule reasoning.
3. Switch to the operations list or follow a dependency: selection stays synchronized, including browser history within the current result.
4. Load two files or paste input; compare after explicit notice that content is sent to the API and not intentionally retained.
5. Inspect all finding classes and coverage gaps; download JSON or self-contained escaped HTML for the entire comparison.

## Non-goals

No API execution, endpoint health checks, generated SDKs, GitHub app, remote URL import, external reference fetching, OpenAPI 2/3.1/3.2, complete JSON Schema equivalence, automated rename guessing, collaborative comments, arbitrary graph editor, LLM verdicts, public sign-up, saved uploads, PDF rendering service, or production SLA.

No implementation of optional persistence in this release. Filesystem/database/cloud archives are unnecessary for the stated journey. Download and rerun are the persistence contract.

## Acceptance

- The Python engine alone produces findings, graph, inspection evidence, and reports. Frontend does not independently decide compatibility.
- Every finding has a rule ID or explicit unsupported code, source pointers, affected operations, and an explanation. Coverage gaps prevent an unqualified clean conclusion.
- Repeated comparisons with identical canonical inputs/policy produce identical stable result payloads; presentation timestamps are separate.
- Exactly one operation identity is method + literal path. Changes in operationId are not operation removal; changing a path is removal/addition, not guessed rename.
- Bundled example remains useful during API cold start/outage; live uploads never quietly fall back to fabricated sample results.
- Keyboard/list users can reach every finding, dependency and inspector action; responsive layout passes 360, 768, and 1440px checks without whole-page horizontal overflow.
- Adversarial fixtures prove limits, safe parsing, no reference-network access, escaped output, and controlled failure. Large-input timeouts release resources.
- Exports include full findings regardless of current UI filters, policy/engine versions, input digests, warnings, and absent-versus-null evidence.
- Automated release gates pass and measured limitations are public. No claims of perfect detection or guaranteed uptime.

## Scope-change policy

Minor implementation choices can change with recorded reasons. OpenAPI 3.1 support, saving private data, authentication, paid infrastructure, remote ingestion, or changing the compatibility policy requires a major-outcome decision. Ayotomiwa need not review individual tasks.
