# Sources and decisions

Checked 9 October 2026. External terms and software versions may change; recheck before installation and deployment. Planning documents are design decisions, not claims that implementation exists.

## Primary sources

- [OpenAPI Specification 3.0.3](https://spec.openapis.org/oas/v3.0.3.html): normative interpretation of OpenAPI documents, references, parameters and schemas. The project intentionally supports only an explicit 3.0.0–3.0.3 range; this is an implementation boundary, not an OpenAPI limitation.
- [Django 5.2 release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/) and [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/): planned LTS backend and deployment verification.
- [Django REST Framework](https://www.django-rest-framework.org/): API serialization and request handling.
- [React Flow documentation](https://reactflow.dev/learn) and [xyflow open-source terms](https://xyflow.com/open-source): graph UI and license check.
- [Cloudflare Pages React deployment](https://developers.cloudflare.com/pages/framework-guides/deploy-a-react-site/) and [limits](https://developers.cloudflare.com/pages/platform/limits/): static frontend target.
- [Render Free](https://render.com/docs/free/) and [Django deployment](https://render.com/docs/deploy-django/): conditional stateless API target and cold-start/ephemeral-storage constraints.

## Consequential choices

1. **Stateless v1**: the intended reviewer can get an immediate sample, run a comparison and download evidence without an account. Durable saved history would add security, privacy and hosting cost/complexity; defer it. This also avoids an expiring free database.
2. **Bounded, conservative policy**: accurate claims for a documented OpenAPI 3.0 subset are more credible than a sweeping compatibility promise. Unsupported semantics become review-required gaps.
3. **Pure Python engine**: the recruiter-visible backend substance is testable outside HTTP/UI and generates the static sample, eliminating a second verdict implementation in the frontend.
4. **Static sample + live API**: the first impression stays useful through Render cold starts; live comparison remains honestly dependent on Django.
5. **Dependency graph plus evidence list**: graph communicates reachability; text provides precise, accessible proof. Neither alone is the whole product.
6. **No required spending**: provider selection is conditional. If a card, paid plan or meaningful quota risk is unavoidable at publication, stop and request a user decision, preserving local functionality.

These decisions are reversible design choices except the public privacy promise: adding persistence or remote URL retrieval requires a new consent/threat-model review before implementation.
