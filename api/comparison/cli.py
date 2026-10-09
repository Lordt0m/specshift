"""Command-line interface for the SpecShift comparison engine."""

import argparse
import json
import sys
from pathlib import Path

from .engine import compare_specifications
from .report import generate_html_report, generate_json_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SpecShift: Compare two OpenAPI 3.0 contracts and output deterministic compatibility analysis."
    )
    parser.add_argument("baseline", help="Path to baseline OpenAPI document (YAML or JSON)")
    parser.add_argument("candidate", help="Path to candidate OpenAPI document (YAML or JSON)")
    parser.add_argument(
        "--output", "-o", help="Optional path to write output file (defaults to stdout if omitted)"
    )
    parser.add_argument(
        "--format", "-f", choices=["json", "html"], default="json", help="Output format: json (default) or html"
    )

    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    candidate_path = Path(args.candidate)

    if not baseline_path.is_file():
        print(f"Error: Baseline file '{baseline_path}' does not exist.", file=sys.stderr)
        return 1
    if not candidate_path.is_file():
        print(f"Error: Candidate file '{candidate_path}' does not exist.", file=sys.stderr)
        return 1

    try:
        baseline_bytes = baseline_path.read_bytes()
        candidate_bytes = candidate_path.read_bytes()
        result = compare_specifications(baseline_bytes, candidate_bytes)

        if args.format == "html":
            output_content = generate_html_report(result)
        else:
            output_content = generate_json_report(result)

        if args.output:
            out_file = Path(args.output)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(output_content, encoding="utf-8")
            print(f"Wrote {args.format.upper()} report to {out_file}")
        else:
            print(output_content)

        return 0
    except Exception as e:
        print(f"Comparison failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
