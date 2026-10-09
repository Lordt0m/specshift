"""SpecShift comparison engine package."""

from .engine import compare_specifications
from .rules import RULE_REGISTRY, POLICY_VERSION
from .report import generate_html_report, generate_json_report

__version__ = "1.0.0"

__all__ = [
    "compare_specifications",
    "RULE_REGISTRY",
    "POLICY_VERSION",
    "generate_html_report",
    "generate_json_report",
    "__version__",
]
