from pathlib import Path

from .collector import collect_data
from .models import ContextDataReport


def collect_context_data(output_root: Path) -> ContextDataReport:
    """Backward-compatible wrapper around the unified data collector."""
    report = collect_data(output_root=Path(output_root), sources=("boundaries", "neotoma", "sead", "raa"))
    return ContextDataReport(
        generated_on=report.generated_on,
        output_root=report.output_root,
        neotoma_point_count=report.neotoma_point_count,
        sead_point_count=report.sead_point_count,
        raa_total_site_count=report.raa_total_site_count,
        raa_heritage_site_count=report.raa_heritage_site_count,
    )
