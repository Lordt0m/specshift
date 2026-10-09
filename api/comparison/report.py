"""Self-contained HTML and JSON report generators.

Follows security-and-privacy.md requirements:
- Strictly no external network calls or CDNs.
- Strictly no JavaScript.
- Full escaping of all input-derived strings using html.escape.
"""

import html
import json
from typing import Any


def generate_json_report(comparison_result: dict[str, Any]) -> str:
    """Serialize comparison result to formatted JSON."""
    return json.dumps(comparison_result, indent=2, ensure_ascii=False, default=str)


def generate_html_report(comparison_result: dict[str, Any]) -> str:
    """Generate self-contained, escaped, accessible HTML report."""
    summary = comparison_result.get("summary", {})
    findings = comparison_result.get("findings", [])
    gaps = comparison_result.get("coverage_gaps", [])
    conclusion = html.escape(summary.get("conclusion", "No conclusion"))
    policy_ver = html.escape(str(comparison_result.get("policy_version", "v1")))
    engine_ver = html.escape(str(comparison_result.get("engine_version", "1.0.0")))

    # Theme tokens from interface-brief.md
    # canvas: #F7F8F7, surface: #FFFFFF, ink: #17212B, secondary ink: #53616B,
    # breaking: #B63F37, review: #8B671A, non-breaking: #236C61
    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
  <title>SpecShift Comparison Report - Policy {policy_ver}</title>
  <style>
    :root {{
      --canvas: #F7F8F7;
      --surface: #FFFFFF;
      --ink: #17212B;
      --secondary: #53616B;
      --border: #C8D0D0;
      --breaking: #B63F37;
      --breaking-bg: #FBEBEA;
      --review: #8B671A;
      --review-bg: #FEF8EC;
      --non-breaking: #236C61;
      --non-breaking-bg: #EAF5F3;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--canvas);
      color: var(--ink);
      line-height: 1.5;
      padding: 2rem 1.5rem;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 2.5rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }}
    header {{
      border-bottom: 2px solid var(--border);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
    }}
    h1 {{
      font-size: 1.75rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
    }}
    .meta {{
      color: var(--secondary);
      font-size: 0.9rem;
    }}
    .verdict-banner {{
      padding: 1.25rem;
      border-radius: 6px;
      margin-bottom: 2rem;
      font-size: 1.15rem;
      font-weight: 600;
      border: 1px solid var(--border);
      background: var(--canvas);
    }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 2.5rem;
    }}
    .metric-card {{
      background: var(--canvas);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem 1.25rem;
    }}
    .metric-num {{
      font-size: 1.8rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }}
    .metric-label {{
      font-size: 0.85rem;
      color: var(--secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .badge {{
      display: inline-block;
      padding: 0.25rem 0.6rem;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .badge-breaking {{ background: var(--breaking-bg); color: var(--breaking); border: 1px solid var(--breaking); }}
    .badge-review_required {{ background: var(--review-bg); color: var(--review); border: 1px solid var(--review); }}
    .badge-non_breaking {{ background: var(--non-breaking-bg); color: var(--non-breaking); border: 1px solid var(--non-breaking); }}
    h2 {{
      font-size: 1.35rem;
      margin: 2rem 0 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 2rem;
      font-size: 0.92rem;
    }}
    th, td {{
      padding: 0.85rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{
      background: var(--canvas);
      font-weight: 600;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--secondary);
    }}
    code, .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.85rem;
      background: var(--canvas);
      padding: 0.15rem 0.35rem;
      border-radius: 3px;
      border: 1px solid var(--border);
    }}
    ul.tag-list {{
      list-style: none;
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
    }}
    ul.tag-list li {{
      background: var(--canvas);
      border: 1px solid var(--border);
      border-radius: 3px;
      padding: 0.1rem 0.4rem;
      font-size: 0.8rem;
      font-family: monospace;
    }}
    .gap-card {{
      background: var(--review-bg);
      border: 1px solid var(--review);
      border-radius: 6px;
      padding: 1rem 1.25rem;
      margin-bottom: 1rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>SpecShift Compatibility Report</h1>
      <div class="meta">
        Policy: <strong>{policy_ver}</strong> &middot; Engine: <strong>{engine_ver}</strong> &middot; Stateless Deterministic Audit
      </div>
    </header>

    <div class="verdict-banner">
      Conclusion: {conclusion}
    </div>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-num" style="color: var(--breaking);">{summary.get('breaking_count', 0)}</div>
        <div class="metric-label">Breaking Findings</div>
      </div>
      <div class="metric-card">
        <div class="metric-num" style="color: var(--review);">{summary.get('review_count', 0)}</div>
        <div class="metric-label">Review Required</div>
      </div>
      <div class="metric-card">
        <div class="metric-num" style="color: var(--non-breaking);">{summary.get('non_breaking_count', 0)}</div>
        <div class="metric-label">Non-breaking Changes</div>
      </div>
      <div class="metric-card">
        <div class="metric-num">{summary.get('coverage_gap_count', 0)}</div>
        <div class="metric-label">Coverage Gaps</div>
      </div>
      <div class="metric-card">
        <div class="metric-num">{summary.get('covered_operations', 0)} / {summary.get('total_operations', 0)}</div>
        <div class="metric-label">Covered Operations</div>
      </div>
    </div>

    <h2>Findings ({len(findings)})</h2>
    <table>
      <thead>
        <tr>
          <th>Rule</th>
          <th>Classification</th>
          <th>Context</th>
          <th>Evidence &amp; Reason</th>
          <th>Origin Pointer</th>
          <th>Affected Operations</th>
        </tr>
      </thead>
      <tbody>
"""

    for f in findings:
        r_id = html.escape(str(f.get("rule_id", "")))
        cls = f.get("classification", "")
        cls_label = html.escape(cls.replace("_", " "))
        badge_cls = f"badge badge-{html.escape(cls)}"
        ctx = html.escape(str(f.get("context", "")))
        expl = html.escape(str(f.get("explanation", "")))
        origin_ptr = html.escape(str(f.get("origin_pointer") or "(Added)"))
        
        # Before / After formatting
        b_val = json.dumps(f.get("before"), default=str) if f.get("before") is not None else "(absent)"
        a_val = json.dumps(f.get("after"), default=str) if f.get("after") is not None else "(absent)"
        b_escaped = html.escape(b_val)
        a_escaped = html.escape(a_val)

        ops = f.get("affected_operations", [])
        ops_html = "".join(f"<li>{html.escape(op)}</li>" for op in ops)

        html_out += f"""        <tr>
          <td><strong>{r_id}</strong><br><small>{html.escape(str(f.get("policy_rule", "")))}</small></td>
          <td><span class="{badge_cls}">{cls_label}</span></td>
          <td>{ctx}</td>
          <td>
            <div>{expl}</div>
            <div style="margin-top: 0.4rem; font-size: 0.82rem; color: var(--secondary);">
              Baseline: <code>{b_escaped}</code> &rarr; Candidate: <code>{a_escaped}</code>
            </div>
          </td>
          <td><code>{origin_ptr}</code></td>
          <td><ul class="tag-list">{ops_html}</ul></td>
        </tr>
"""

    html_out += """      </tbody>
    </table>
"""

    if gaps:
        html_out += f"""    <h2>Coverage Gaps ({len(gaps)})</h2>
    <p style="color: var(--secondary); margin-bottom: 1rem;">
      Constructs outside policy v1 coverage. A gap contaminates completeness for any dependent operations.
    </p>
"""
        for g in gaps:
            c_kw = html.escape(str(g.get("construct", "")))
            g_ptr = html.escape(str(g.get("pointer", "")))
            g_rsn = html.escape(str(g.get("reason", "")))
            g_ops = "".join(f"<li>{html.escape(op)}</li>" for op in g.get("affected_operations", []))
            html_out += f"""    <div class="gap-card">
      <div style="font-weight: 600; margin-bottom: 0.25rem;">Construct: <code>{c_kw}</code> at <code>{g_ptr}</code></div>
      <div>{g_rsn}</div>
      <div style="margin-top: 0.5rem; font-size: 0.85rem;">Affected: <ul class="tag-list" style="display: inline-flex;">{g_ops}</ul></div>
    </div>
"""

    html_out += '<details><summary>Complete audit payload, including digests and warnings</summary><pre>' + html.escape(generate_json_report(comparison_result)) + '</pre></details>'
    html_out += """  </div>
</body>
</html>
"""
    return html_out
