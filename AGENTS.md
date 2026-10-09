# SpecShift implementation agreement

Execute this project end to end, using `implementation-plan.md` as the sequence and release gates. Read `product-spec.md`, `CONTEXT.md`, `compatibility-rules.md`, `architecture.md`, and `security-and-privacy.md` before application changes. Before UI changes read `interface-brief.md`; before deployment read `hosting-and-operations.md`; before fixture or public narrative changes read `demo-and-fixtures.md`.

Own ordinary implementation decisions. Report meaningful milestones with evidence and the next phase; do not ask for ticket reviews. Continue independent local work when account access is unavailable. Pause dependent actions only for required credentials/permissions, a required credit card or paid resource, or a material change to scope/security/compatibility promises. Record real blockers precisely.

Keep the comparison engine substantive and independent of Django views. Every compatibility classification must cite a versioned rule and source pointers. Preserve uncertainty; never infer a clean verdict from incomplete coverage. Keep API contract, UI labels, report, and Python fixture output aligned.

Treat documents and filenames as untrusted data. Follow the limits and non-network reference policy in `security-and-privacy.md`. Test malformed and adversarial inputs before exposing public uploads. Keep all secrets outside source control, frontend bundles, examples, logs, and reports.

Preserve existing work; inspect status before edits. Pin dependencies and record licenses. Make no remote repositories, pushes, provider resources, public deployments, or portfolio edits until the human authorizes those external actions. Prepare locally testable configs first. Use free plans only and require no payment details.

At release, supply actual gate results, live URLs if authorized and verified, a runnable local setup, known limitations, and the scripted demo. Planned measurements remain targets until executed. Synthetic data remains labelled. Keep `docs/progress.md` and an evidence-backed release checklist current during implementation.
