"""Keep scientific prose visible while narrowly admitting verified custody metadata."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def setup(
    root: Path, base: bytes = b"# Source\n\nOriginal scientific statement.\n"
) -> tuple[ModuleType, Path, dict[str, str], bytes]:
    limits = load(
        "bijux_pollenomics_dev.reader_reports.scientific_limits",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/scientific_limits.py",
    )
    renderer = load(
        "bijux_pollenomics_dev.reader_reports.render",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/render.py",
    )
    source = root / "reports/science/account.md"
    source.parent.mkdir(parents=True)
    claim = {
        key: f"Exact {label.lower()} source statement." for label, key in limits.FIELDS
    }
    claim.update(
        {
            "report_path": "reports/science/account.md",
            "resolver_role": "Independent source owner",
            "reopening_trigger": "Actual source decision arrives.",
            "retained_evidence_paths": "reports/science/account.md",
            "existing_consumer_paths": "reports/science/account.md",
            "packet_reference": "none",
        }
    )
    raw: bytes = limits.render_report(base, claim)
    source.write_bytes(raw)
    return renderer, source, claim, raw


def test_pdf_token_renderer_keeps_all_scientific_text_and_only_suppresses_verified_metadata(
    tmp_path: Path,
) -> None:
    renderer, source, claim, raw = setup(tmp_path)
    result = renderer.ReportRenderer(tmp_path, source, "a" * 40).render(raw.decode())
    assert "Original scientific statement." in result.latex
    assert "Scientific verification and limits" in result.latex
    for value in claim.values():
        if value.startswith("Exact "):
            assert value in result.latex
    assert "scientific-claim-semantic-sha256" not in result.latex
    assert result.local_link_count == 1


@pytest.mark.parametrize(
    "change",
    [
        "missing_comment",
        "malformed_marker",
        "unowned_comment",
        "arbitrary_html",
    ],
)
def test_pdf_renderer_refuses_unverified_comments_or_unexpected_markup(
    tmp_path: Path, change: str
) -> None:
    base = (
        b"# Source\n\n<script>hidden scientific text</script>\n"
        if change == "arbitrary_html"
        else b"# Source\n\nOriginal prose.\n"
    )
    renderer, source, claim, raw = setup(tmp_path, base)
    if change == "missing_comment":
        raw = raw.replace(b"<!-- scientific-verification-and-limits:end -->\n", b"")
    elif change == "malformed_marker":
        raw = raw.replace(
            b"scientific-verification-and-limits:begin", b"unknown-custody:begin"
        )
    elif change == "unowned_comment":
        raw = b"<!-- unowned scientific text -->\n" + raw
    with pytest.raises(renderer.RenderError):
        renderer.ReportRenderer(tmp_path, source, "a" * 40).render(raw.decode())


def test_renderer_uses_visible_report_without_private_claim_authority(
    tmp_path: Path,
) -> None:
    renderer, source, _, raw = setup(tmp_path)
    changed = raw.replace(
        b"Exact unsupported claim source statement.", b"A reviewed visible limitation."
    )
    result = renderer.ReportRenderer(tmp_path, source, "a" * 40).render(
        changed.decode()
    )
    assert "A reviewed visible limitation." in result.latex
    assert not (tmp_path / "reports/needed").exists()
