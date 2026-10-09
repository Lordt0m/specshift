# Interface brief: the change as the hero

The audience is a developer reviewing an API contract before a release. The first viewport should open on a real, clearly synthetic comparison, with one selected change connected to the operations it affects. The memorable element is the impact map itself, not a decorative dashboard or metric row.

## Visual direction

Treat the workspace like an annotated engineering drawing: light neutral canvas, precise but quiet grid, dark ink, and restrained semantic marks that make a changed dependency traceable. This is not a generic SaaS card grid. The map uses generous whitespace; dense textual evidence lives in an inspector.

Initial design tokens to test in-browser (not immutable brand requirements): canvas `#F7F8F7`, surface `#FFFFFF`, ink `#17212B`, secondary ink `#53616B`, structural line `#C8D0D0`, breaking `#B63F37`, review `#8B671A`, non-breaking `#236C61`. Verify WCAG contrast, including semantic chips. Typeface direction: a clear humanist sans such as Source Sans 3 for UI and a compact technical face such as IBM Plex Mono only for paths/pointers/code evidence. Host fonts locally or use reliable fallbacks; do not let font loading block use.

Desktop composition: a narrow input/action rail; a wide central impact map; a right evidence inspector. The top bar carries product identity, baseline → candidate direction, policy label and `Compare`/`Download report` actions. Below the map, a synchronized operation list offers the complete accessible alternative to graph navigation. At tablet/mobile widths, use a single primary column with segmented `Changes`, `Map`, `Details` views and an always-clear selection breadcrumb. No full-page horizontal scrolling at 360px.

The map is read-only. Lay nodes deterministically by dependency depth and context, not random physics. Use shape and labels as well as color: breaking = solid alert mark, review = outlined query mark, non-breaking = quiet check. On selecting a finding, highlight only its origin and reachable affected operations. Explain that reachability is not runtime impact. A `Fit view` action and a text equivalent list prevent graph-only comprehension. Avoid gratuitous pan/zoom tutorials or animation.

## Content and interaction

- Hero copy: `See which API changes reach your operations.` Short explanation: `Compare two OpenAPI files and trace each finding back to its source.`
- Sample badge: `Recorded example · synthetic data` plus link `How this result was made`.
- Input labels: `Baseline (current contract)` and `Candidate (proposed contract)`.
- Primary action: `Compare contracts`. Swap action explicitly changes direction and reruns only when invoked.
- Finding labels: `Breaking`, `Review required`, `Non-breaking`. The page-level conclusion must use the precise text in `compatibility-rules.md`.
- Each finding row contains rule ID, concise change, exact method/path or schema pointer, and affected operation count. Inspector shows before/after values with explicit `Absent` versus `null`, reason, assumption, source pointer and linked operations.
- Empty result: explain whether nothing changed or changes exist but no breaking rules fired. If gaps exist, never display a green all-clear.
- API warming: `The comparison service is waking up. The recorded example is still available.` Keep retry bounded and user-triggered after timeout. Uploads never silently return the sample.
- Error copy names the baseline/candidate side and how to fix it. Preserve pasted/file input where safe; never display raw server traces.
- Download labels: `Download JSON report`, `Download HTML report`. Exports contain all findings, even when the view is filtered.

Keyboard focus order follows visual reading order. Make the list, inspector, dialogs and tabs keyboard-operable with visible focus. Announce compare completion and errors through a polite live region; avoid noisy announcements during graph hover. Honor reduced motion. Show distinct loading, stale, offline, empty and limit-reached states. Test with a screen reader and without mouse.

## Design critique gate

Before coding, compare this direction to the actual synthetic fixture: if the hero could be transplanted unchanged into a generic analytics dashboard, replace that treatment with a more literal contract-change trace. After implementation, inspect 360, 768 and 1440px screenshots and remove any ornament that obscures the causal path from change to affected operation.
