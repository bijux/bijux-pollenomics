"""Independent, content-bound verification for published atlas documents."""

from .contracts import (
    AtlasBrowserContractError,
    AtlasCandidate,
    AtlasScope,
    BrowserVerificationPlan,
    JsonObject,
)
from .static_integrity import audit_static_atlas
from .verdict import evaluate_browser_report


def run_browser_verification(plan: BrowserVerificationPlan) -> JsonObject:
    """Load the runner lazily so its module CLI executes without import ambiguity."""
    from .runner import run_browser_verification as run

    return run(plan)


__all__ = [
    "AtlasBrowserContractError",
    "AtlasCandidate",
    "AtlasScope",
    "BrowserVerificationPlan",
    "audit_static_atlas",
    "evaluate_browser_report",
    "run_browser_verification",
]
