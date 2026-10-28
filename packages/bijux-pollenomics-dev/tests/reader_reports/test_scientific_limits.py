"""Guard authored prose, claim custody and complete on-page verification fields."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[4]


def module() -> ModuleType:
    path = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/scientific_limits.py"
    )
    spec = importlib.util.spec_from_file_location(
        "bijux_pollenomics_dev.reader_reports.scientific_limits", path
    )
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def row(raw: bytes) -> dict[str, str]:
    return {
        "report_path": "reports/science/source.md",
        "supported_scoped_claim": "A conditional point estimate completed.",
        "unsupported_claim": "Independent ecological accuracy remains untested.",
        "actual_verification_performed": "Twelve declared cells agreed with the scalar oracle.",
        "concrete_reason": "An independent measured reference is absent.",
        "cause_categories": "data|comparability",
        "consequence": "Do not infer measured accuracy from numerical agreement.",
        "precise_next_acceptance_route": "Freeze compatible independent observations before predictions.",
        "negative_or_refused_result": "One of thirteen declared cells refused.",
        "matched_denominator": "Twelve scored cells and one refused cell.",
        "resolver_role": "Reference source owner",
        "reopening_trigger": "A qualified measured reference is supplied.",
        "retained_evidence_paths": "docs/report/conditional/report.json",
        "existing_consumer_paths": "reports/science/source.md",
        "packet_reference": "none",
    }


def test_render_preserves_exact_authored_bytes_and_all_nine_fields() -> None:
    api = module()
    source = (
        b"# Source account\n\nOriginal prose.  \n\n```text\nretained fixture\n```\n"
    )
    claim = row(source)
    result: bytes = api.render_report(source, claim)
    assert result.startswith(source)
    assert api.authored_bytes(result) == source
    api.validate_report(result, claim)
    for label, key in api.FIELDS:
        assert f"**{label}.**".encode() in result
        assert claim[key].encode() in result
    assert len(api.FIELDS) == 9
    assert b"../../docs/report/conditional/report.json" in result
    assert api.render_report(result, claim) == result


@pytest.mark.parametrize(
    "change",
    [
        "semantic",
        "missing",
        "truncated",
        "duplicate",
        "trailing",
        "injection",
        "empty",
    ],
)
def test_refuse_changed_or_ambiguous_scientific_custody(change: str) -> None:
    api = module()
    source = b"# Authored\n"
    claim = row(source)
    result: bytes = api.render_report(source, claim)
    with pytest.raises(ValueError):
        if change == "semantic":
            claim["matched_denominator"] = "Thirteen successful cells."
            api.validate_report(result, claim)
        elif change == "missing":
            api.validate_report(source, claim)
        elif change == "truncated":
            api.authored_bytes(result[:-10])
        elif change == "duplicate":
            api.authored_bytes(result + result)
        elif change == "trailing":
            api.authored_bytes(result + b"Unowned trailing prose\n")
        else:
            claim["negative_or_refused_result"] = (
                "<!-- scientific-verification-and-limits:begin -->"
                if change == "injection"
                else " "
            )
            api.render_report(source, claim)


def setup_repository(root: Path) -> bytes:
    (root / ".git").mkdir()
    source = b"# Source\n\nPrior prose retained.\n"
    path = root / "reports/science/source.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(source)
    register = root / "artifacts/claim-fixture/claims.csv"
    register.parent.mkdir(parents=True)
    claim = row(source)
    with register.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(claim))
        writer.writeheader()
        writer.writerow(claim)
    return source


def test_actual_render_proposal_preserves_claims_without_hash_products(
    tmp_path: Path,
) -> None:
    api = module()
    source = setup_repository(tmp_path)
    register = tmp_path / "artifacts/claim-fixture/claims.csv"
    old_bytes = register.read_bytes()
    output = tmp_path / "artifacts/report-proposal"
    assert (
        api.render_accounts(
            tmp_path, output, tmp_path / "artifacts/claim-fixture/claims.csv"
        )
        == output
    )
    assert register.read_bytes() == old_bytes
    assert (tmp_path / "reports/science/source.md").read_bytes() == source
    rendered = (output / "reports/science/source.md").read_bytes()
    assert api.authored_bytes(rendered) == source
    assert [
        p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()
    ] == ["reports/science/source.md"]


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "escape",
        "parent_traversal",
        "symlink",
        "existing",
    ],
)
def test_render_refuses_before_publishing_partial_accounts(
    tmp_path: Path, change: str
) -> None:
    api = module()
    setup_repository(tmp_path)
    output = tmp_path / "artifacts/report-proposal"
    if change == "duplicate":
        register = tmp_path / "artifacts/claim-fixture/claims.csv"
        lines = register.read_text().splitlines()
        register.write_text("\n".join([*lines, lines[1]]) + "\n")
    elif change == "escape":
        output = tmp_path / "outside"
    elif change == "parent_traversal":
        output = tmp_path / "artifacts/../escaped"
    elif change == "symlink":
        (tmp_path / "artifacts").mkdir(exist_ok=True)
        other = tmp_path / "other"
        other.mkdir()
        (tmp_path / "artifacts/redirect").symlink_to(other, target_is_directory=True)
        output = tmp_path / "artifacts/redirect/result"
    else:
        output.mkdir(parents=True)
    with pytest.raises((ValueError, FileExistsError)):
        api.render_accounts(
            tmp_path, output, tmp_path / "artifacts/claim-fixture/claims.csv"
        )
    if change != "existing":
        assert not output.exists()


def test_authored_edits_preserve_exact_managed_limits_without_hash_rebinding() -> None:
    api = module()
    source = b"# Source account\n\nReadable original prose.\n"
    claim = row(source)
    rendered = api.render_report(source, claim)
    edited = rendered.replace(b"Readable original prose.", b"Readable clarified prose.")
    api.validate_report(edited, claim)
    assert api.render_report(edited, claim) == edited
    assert b"sha256" not in edited and "source_report_sha256" not in claim


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "reordered", "empty", "evidence"]
)
def test_embedded_limits_require_complete_visible_structure(damage: str) -> None:
    api = module()
    raw = api.render_report(b"# Source\n", row(b""))
    api.validate_embedded_report(raw)
    if damage == "missing":
        raw = raw.replace(b"**Matched denominator.**", b"**Unowned field.**")
    elif damage == "duplicate":
        raw = raw.replace(b"**Matched denominator.**", b"**Supported claim.**")
    elif damage == "reordered":
        raw = (
            raw.replace(b"**Supported claim.**", b"**Unmatched claim.**")
            .replace(b"**Unsupported claim.**", b"**Supported claim.**")
            .replace(b"**Unmatched claim.**", b"**Unsupported claim.**")
        )
    elif damage == "empty":
        raw = raw.replace(row(b"")["matched_denominator"].encode(), b" ")
    else:
        raw = raw.replace(b"Retained evidence:", b"Unbound sources:")
    with pytest.raises(ValueError):
        api.validate_embedded_report(raw)


@pytest.mark.parametrize(
    "report_path,attachment_count",
    [
        (
            "docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/README.md",
            4,
        ),
        ("docs/report/synthetic-validation/recovery-evidence/README.md", 3),
        ("docs/report/vegetation-reference/pyrenees-botanical-projection/README.md", 1),
    ],
)
def test_primary_reader_evidence_uses_sealed_public_attachments(
    report_path: str, attachment_count: int
) -> None:
    """First-party source custody remains downloadable inside the documentation site."""
    api = module()
    with (ROOT / "reports/needed/report-claims.csv").open() as handle:
        claim = next(
            row for row in csv.DictReader(handle) if row["report_path"] == report_path
        )
    raw = (ROOT / report_path).read_bytes()
    api.validate_report(raw, claim)
    manifest = json.loads(
        (ROOT / "configs/docs/scientific-source-files.json").read_bytes()
    )
    sources = {row["source"] for row in manifest["files"]}
    evidence = claim["retained_evidence_paths"].split(";")
    assert not sources.intersection(evidence)
    public = {row["destination"]: row for row in manifest["files"]}
    selected = [path for path in evidence if path in public]
    assert len(selected) == attachment_count
    for path in selected:
        pin = public[path]
        attachment = (ROOT / path).read_bytes()
        assert attachment == (ROOT / pin["source"]).read_bytes()
        assert len(attachment) == pin["bytes"]
        assert hashlib.sha256(attachment).hexdigest() == pin["sha256"]
        assert (
            hashlib.sha1(
                b"blob " + str(len(attachment)).encode() + b"\0" + attachment,
                usedforsecurity=False,
            ).hexdigest()
            == pin["git_blob"]
        )
