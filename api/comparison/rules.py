"""Authoritative Rule Registry for Compatibility Policy v1.

Derived directly from compatibility-rules.md.
"""

from dataclasses import dataclass
from typing import Optional

POLICY_VERSION = "v1"


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    request_classification: str  # "breaking", "non_breaking", "review_required", "na"
    response_classification: str  # "breaking", "non_breaking", "review_required", "na", "same"
    description: str
    assumptions: str


RULE_REGISTRY: dict[str, Rule] = {
    "OP-01": Rule(
        id="OP-01",
        title="Remove method/path",
        request_classification="breaking",
        response_classification="breaking",
        description="Operation method and literal path was removed from the contract.",
        assumptions="Clients expecting this operation will fail."
    ),
    "OP-02": Rule(
        id="OP-02",
        title="Add method/path",
        request_classification="non_breaking",
        response_classification="non_breaking",
        description="New operation method and literal path was added.",
        assumptions="Existing clients can continue calling existing operations."
    ),
    "PA-01": Rule(
        id="PA-01",
        title="Add required query/header/cookie parameter or make optional parameter required",
        request_classification="breaking",
        response_classification="na",
        description="A required request parameter was added or an optional parameter was made required.",
        assumptions="Existing requests omitting this parameter will be rejected."
    ),
    "PA-02": Rule(
        id="PA-02",
        title="Add optional parameter or make required optional",
        request_classification="non_breaking",
        response_classification="na",
        description="An optional parameter was added or an existing parameter was made optional.",
        assumptions="Existing clients sending or omitting the parameter continue to be accepted."
    ),
    "PA-03": Rule(
        id="PA-03",
        title="Remove parameter",
        request_classification="review_required",
        response_classification="na",
        description="A parameter was removed from the operation.",
        assumptions="Server handling of unknown/extraneous parameters is unspecified."
    ),
    "RB-01": Rule(
        id="RB-01",
        title="Add required body or optional to required",
        request_classification="breaking",
        response_classification="na",
        description="A required request body was added or made required.",
        assumptions="Clients not providing a request body will be rejected."
    ),
    "RB-02": Rule(
        id="RB-02",
        title="Required to optional body",
        request_classification="non_breaking",
        response_classification="na",
        description="Request body requirement was changed from required to optional.",
        assumptions="Clients providing or omitting the body remain accepted."
    ),
    "MD-01": Rule(
        id="MD-01",
        title="Remove accepted request media type",
        request_classification="breaking",
        response_classification="na",
        description="An accepted request Content-Type was removed.",
        assumptions="Clients sending the removed media type will receive 415 Unsupported Media Type."
    ),
    "MD-02": Rule(
        id="MD-02",
        title="Add accepted request media type",
        request_classification="non_breaking",
        response_classification="na",
        description="A newly accepted request Content-Type was added.",
        assumptions="Existing clients sending previously accepted media types continue unaffected."
    ),
    "RS-01": Rule(
        id="RS-01",
        title="Remove a documented response status/media type",
        request_classification="na",
        response_classification="review_required",
        description="A documented response status code or media type was removed.",
        assumptions="Runtime response status selection intent is unknown."
    ),
    "RS-02": Rule(
        id="RS-02",
        title="Add response status/media type",
        request_classification="na",
        response_classification="review_required",
        description="A new response status code or media type was documented.",
        assumptions="Clients may receive previously unseen response possibilities."
    ),
    "SC-01": Rule(
        id="SC-01",
        title="Change explicit type",
        request_classification="review_required",
        response_classification="review_required",
        description="Explicit schema data type was changed.",
        assumptions="No subtyping inference is made; review required unless strictly identical."
    ),
    "SC-02": Rule(
        id="SC-02",
        title="Remove enum members",
        request_classification="breaking",
        response_classification="non_breaking",
        description="One or more enum values were removed.",
        assumptions="In requests: clients sending the removed value will be rejected. In responses: server returns a narrower subset."
    ),
    "SC-03": Rule(
        id="SC-03",
        title="Add enum members",
        request_classification="non_breaking",
        response_classification="breaking",
        description="One or more enum values were added.",
        assumptions="Under exhaustive-enum-client policy, newly returned response enum values break existing clients."
    ),
    "SC-04": Rule(
        id="SC-04",
        title="Add required property / optional to required",
        request_classification="breaking",
        response_classification="non_breaking",
        description="Property was added as required or an existing optional property was made required.",
        assumptions="In requests: old payloads omitting this property fail. In responses: guarantee is added (non-breaking if object already open or existed)."
    ),
    "SC-05": Rule(
        id="SC-05",
        title="Required to optional",
        request_classification="non_breaking",
        response_classification="breaking",
        description="Property was changed from required to optional.",
        assumptions="In requests: clients can now omit it. In responses: guaranteed field is no longer promised."
    ),
    "SC-06": Rule(
        id="SC-06",
        title="Remove property",
        request_classification="review_required",
        response_classification="breaking",
        description="Property was removed from schema.",
        assumptions="In requests: server handling of old input is unknown. In responses: breaking if previously required; review required if previously optional."
    ),
    "SC-07": Rule(
        id="SC-07",
        title="Add optional property",
        request_classification="non_breaking",
        response_classification="non_breaking",
        description="Optional property was added to schema.",
        assumptions="Non-breaking for open baseline object; breaking in responses if baseline was explicitly closed (additionalProperties: false)."
    ),
    "SC-08": Rule(
        id="SC-08",
        title="Allow null where formerly forbidden",
        request_classification="non_breaking",
        response_classification="breaking",
        description="Nullable set to true where previously false or unspecified.",
        assumptions="In requests: clients may now send null. In responses: clients expecting non-null values may crash."
    ),
    "SC-09": Rule(
        id="SC-09",
        title="Forbid null where formerly allowed",
        request_classification="breaking",
        response_classification="non_breaking",
        description="Nullable set to false where previously true.",
        assumptions="In requests: clients sending null will fail. In responses: server guarantees non-null value."
    ),
    "SC-10": Rule(
        id="SC-10",
        title="Tighten same-type numeric/length/item bound",
        request_classification="breaking",
        response_classification="non_breaking",
        description="A validation constraint was made more restrictive (higher min, lower max).",
        assumptions="In requests: previously valid input is rejected. In responses: narrower output set."
    ),
    "SC-11": Rule(
        id="SC-11",
        title="Loosen same-type numeric/length/item bound",
        request_classification="non_breaking",
        response_classification="breaking",
        description="A validation constraint was made less restrictive (lower min, higher max).",
        assumptions="In requests: wider input accepted. In responses: clients may receive values outside previous assumptions."
    ),
    "SC-12": Rule(
        id="SC-12",
        title="additionalProperties true/default to false",
        request_classification="breaking",
        response_classification="non_breaking",
        description="Schema object was closed to additional properties.",
        assumptions="In requests: extraneous properties will be rejected. In responses: non-breaking if no property-set conflict."
    ),
    "SC-13": Rule(
        id="SC-13",
        title="additionalProperties false to true/default",
        request_classification="non_breaking",
        response_classification="breaking",
        description="Schema object was opened to additional properties.",
        assumptions="In requests: non-breaking. In responses: clients expecting closed schema may receive unexpected properties."
    ),
    "MT-01": Rule(
        id="MT-01",
        title="Description/summary/example/tag edit only",
        request_classification="non_breaking",
        response_classification="non_breaking",
        description="Metadata only changed without modifying contract structure.",
        assumptions="Documentation edits do not affect runtime message compatibility."
    ),
    "MT-02": Rule(
        id="MT-02",
        title="operationId edit only",
        request_classification="review_required",
        response_classification="review_required",
        description="operationId changed.",
        assumptions="Client code generator method and interface names may change."
    ),
    "UN-01": Rule(
        id="UN-01",
        title="Changed unsupported semantic construct",
        request_classification="review_required",
        response_classification="review_required",
        description="Contract change in construct outside supported simple schema policy.",
        assumptions="Compatibility cannot be determined automatically under policy v1."
    ),
}
