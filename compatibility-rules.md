# Compatibility policy v1

This file is authoritative. Engine version and policy version are independent. A breaking finding means a documented rule is violated, not that every consumer is proven to fail. Non-breaking means accepted under this policy, not universal client safety.

## Direction and coverage

Assess replacing the baseline server with the candidate while preserving previously valid client requests and documented response guarantees. Requests should accept at least the old accepted set. Responses should stay within the old permitted set and keep old guaranteed fields. Clients tolerate additional response properties unless the baseline explicitly closes the object. Clients may exhaustively handle documented enum values.

Only simple JSON schemas with explicit types, properties, required, items, enum, nullable, numeric bounds, length/item bounds and boolean additionalProperties receive set-direction rules. Keep readOnly/writeOnly fields in their respective contexts. No speculative coercion or default-filling. Missing type, implicit free-form object, format/pattern changes, schema-valued additionalProperties, unsupported composition, and unknown semantic keywords are review required where used. A numeric comparison is supported only for the same explicit numeric type and unambiguous 3.0 bounds; otherwise review required.

Apply each shared schema in each usage context. A single edit can produce a request and response finding with different classifications. Preserve one origin and contextual finding IDs; do not inflate counts by repeating the same context finding for each dependent operation. Aggregate affected operations. Unused components are visible structural changes without claimed client impact.

## Rules

| ID | Change | Request assessment | Response assessment |
| --- | --- | --- | --- |
| OP-01 | Remove method/path | Breaking | Same operation-level finding |
| OP-02 | Add method/path | Non-breaking | Same operation-level finding |
| PA-01 | Add required query/header/cookie parameter or make optional parameter required | Breaking | N/A |
| PA-02 | Add optional parameter or make required optional | Non-breaking | N/A |
| PA-03 | Remove parameter | Review required: unknown-parameter handling is unspecified | N/A |
| RB-01 | Add required body or optional to required | Breaking | N/A |
| RB-02 | Required to optional | Non-breaking | N/A |
| MD-01 | Remove accepted request media type | Breaking | N/A |
| MD-02 | Add accepted request media type | Non-breaking | N/A |
| RS-01 | Remove a documented response status/media type | N/A | Review required: intent/runtime status selection is unknown |
| RS-02 | Add response status/media type | N/A | Review required: previously unseen response possibility |
| SC-01 | Change explicit type | Review required unless equal; no subtyping inference | Same |
| SC-02 | Remove enum members | Breaking | Non-breaking |
| SC-03 | Add enum members | Non-breaking | Breaking under exhaustive-enum-client policy |
| SC-04 | Add required property / optional to required | Breaking | Non-breaking if property already existed |
| SC-05 | Required to optional | Non-breaking | Breaking: guarantee removed |
| SC-06 | Remove property | Review required: server treatment of old input is unknown | Breaking if previously required; review required if optional |
| SC-07 | Add optional property | Non-breaking | Non-breaking for open baseline object; breaking for closed baseline object |
| SC-08 | Allow null where formerly forbidden | Non-breaking | Breaking |
| SC-09 | Forbid null where formerly allowed | Breaking | Non-breaking |
| SC-10 | Tighten same-type numeric/length/item bound | Breaking | Non-breaking |
| SC-11 | Loosen same-type numeric/length/item bound | Non-breaking | Breaking |
| SC-12 | additionalProperties true/default to false | Breaking | Non-breaking if no property-set conflict |
| SC-13 | additionalProperties false to true/default | Non-breaking | Breaking |
| MT-01 | Description/summary/example/tag edit only | Non-breaking, metadata only | Same |
| MT-02 | operationId edit only | Review required: generated client naming may change | Same |
| UN-01 | Changed unsupported semantic construct | Review required | Review required |

New response required property (SC-04 + new property) still checks SC-07 closed-object compatibility. Both addition and enum removal in the same edit can produce mixed findings; retain all. When one change cannot be soundly decomposed, emit review required instead of asserting a rule.

Path parameters must be required per OpenAPI. Header parameter identity is case-insensitive; other parameter names are case-sensitive. Operation parameters override matching path-item parameters. Removing/changing a path parameter normally accompanies an operation path change; never match different literal paths heuristically.

Required property addition in a request is breaking; adding a default does not erase it. Required response removal is breaking even if its old value permitted null. Arrays apply item rules in the containing request/response context. Resolve nullable defaults only within supported explicitly typed schemas; distinguish absent values from explicit JSON null in evidence.

## Explicit uncertainty

Changed security requirements/definitions, servers/base URLs, callbacks, links, XML, encodings, response headers, deprecated status, content negotiation details and vendor extensions are review required. Composition (`allOf`, `oneOf`, `anyOf`, `not`), discriminators and unknown validation keywords create coverage gaps even if unchanged when reachable from an operation. A gap contaminates that operation's completeness; supported sibling changes still receive findings.

Internal cycles are valid dependencies, not an excuse to expand forever. Analyze supported local fields once per schema/context, use visited sets for reachability. A cyclic/composite relation whose semantics cannot be decided produces a gap. External `$ref` anywhere is rejected as an unsupported input (no partial remote fetch). Missing internal refs, invalid structural shapes, duplicate keys or unsupported top-level versions reject the whole comparison.

## Result conclusion

- Any breaking findings: `Breaking changes found`, with gap count if any.
- No breaking, but review findings or coverage gaps: `Review required; compatibility not established`.
- Otherwise: `No breaking changes detected by policy v1`.

Expose covered/total operation counts and gap pointers. Pure formatting/key-order changes yield no semantic findings; enum/required lists are sets, examples arrays retain order, vendor-extension edits are not ignored. Preserve original source pointers through normalization, including escaped JSON Pointer tokens (`~0`, `~1`).

## Proof obligations

Each implemented rule needs positive, negative and reverse-direction tests; nested and shared contexts; unchanged control. Assert exact IDs, pointers, classifications and affected operations, not merely counts. Maintain a machine-readable rule registry and fixture expectations. Export and UI display the same registry wording. Unknown fields must surface as a gap or metadata under an explicit registry entry, never disappear silently.
