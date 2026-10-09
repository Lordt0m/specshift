# API change review

Language for reviewing how an API contract changed between two snapshots.

## Language

**Snapshot**: A specific API contract document at one point in its evolution.
_Avoid_: Version when referring to the document rather than its advertised version string.

**Baseline**: The earlier snapshot against which changes are assessed.
_Avoid_: Left file, original.

**Candidate**: The proposed later snapshot.
_Avoid_: Right file, new API.

**Comparison**: The review of one baseline and one candidate under a specific compatibility policy.

**Operation**: An API action identified by its HTTP method and path.
_Avoid_: Endpoint when a precise operation is meant.

**Schema**: A contract describing the structure and constraints of a value.

**Finding**: An evidence-backed observation about a change, with its compatibility classification.
_Avoid_: Bug, violation.

**Dependency**: A relationship through which an operation or schema uses another contract element.

**Affected operation**: An operation whose contract depends on an element involved in a finding. Dependency alone does not prove a client will fail.
_Avoid_: Broken endpoint.

**Compatibility policy**: The stated assumptions and rules used to judge whether existing clients can continue using the candidate.

**Breaking**: A change that violates an explicit compatibility rule under that policy.

**Non-breaking**: A change accepted by an explicit rule under that policy, with that rule's assumptions.
_Avoid_: Safe, guaranteed compatible.

**Review required**: A change whose compatibility cannot be established by the supported policy.
_Avoid_: Probably safe.

**Coverage gap**: A contract construct or relationship outside the supported analysis.

**Report**: A portable record of a comparison's evidence, policy, findings, and coverage gaps.
