"""Refuse unclassified readers and stale or fabricated canonical account routes."""

import hashlib
import importlib
import importlib.util
import json
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


def modules() -> tuple[ModuleType, ModuleType]:
    importlib.import_module("bijux_pollenomics.reporting.presentation.report_portal")
    product = load(
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.py",
    )
    validator = load(
        "bijux_pollenomics_dev.reader_reports.scientific_routes",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/scientific_routes.py",
    )
    return product, validator


def setup(
    root: Path,
) -> tuple[ModuleType, ModuleType, dict[str, object], list[dict[str, str]]]:
    product, validator = modules()
    primary = root / "reports/science/account.md"
    primary.parent.mkdir(parents=True)
    primary.write_text("# Qualified source account\n")
    digest = hashlib.sha256(primary.read_bytes()).hexdigest()
    source = {
        "schema_version": 1,
        "routes": [
            {
                "reader_path": "docs/report/source/README.md",
                "canonical_accounts": [
                    {
                        "report_path": "reports/science/account.md",
                        "source_sha256": digest,
                    }
                ],
                "scope_reason": "This source census does not establish an ecological event.",
            }
        ],
    }
    routes = product.parse_routes(json.dumps(source))
    reader = root / "docs/report/source/README.md"
    reader.parent.mkdir(parents=True)
    reader.write_bytes(
        product.render_route(
            b"# Native source\n\nOwn denominator: twelve native rows.\n",
            routes["docs/report/source/README.md"],
        )
    )
    authority = root / "reports/needed/scientific-reader-sources.json"
    authority.parent.mkdir(parents=True)
    authority.write_text(
        json.dumps({"schema_version": 1, "non_scientific_readers": []})
    )
    return (
        product,
        validator,
        routes,
        [{"report_path": "reports/science/account.md", "source_report_sha256": digest}],
    )


def test_exact_links_retain_authored_prose_and_all_nine_field_names(
    tmp_path: Path,
) -> None:
    product, validator, routes, claims = setup(tmp_path)
    raw = (tmp_path / "docs/report/source/README.md").read_bytes()
    assert (
        product.authored_reader(raw)
        == b"# Native source\n\nOwn denominator: twelve native rows.\n"
    )
    assert (
        b"https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/account.md"
        in raw
    )
    for field in [
        b"supported and unsupported claim",
        b"actual verification performed",
        b"remaining input or review",
        b"cause category",
        b"consequence",
        b"precise next acceptance route",
        b"negative or refused result",
        b"matched denominator",
    ]:
        assert field in raw
    result = validator.validate_reader_routes(tmp_path, claims, routes)
    assert result == {
        "primary_accounts": 1,
        "scientific_wrappers": 1,
        "non_scientific_readers": 0,
        "physical_docs_report_markdown": 1,
    }
    assert product.render_route(raw, routes["docs/report/source/README.md"]) == raw


@pytest.mark.parametrize(
    "change",
    [
        "new_reader",
        "missing_reader",
        "account_bytes",
        "account_authority",
        "route_text",
        "route_missing",
        "route_duplicate",
        "excluded_overlap",
        "empty_exclusion",
        "reader_symlink",
    ],
)
def test_reading_routes_refuse_incomplete_or_changed_sources(
    tmp_path: Path, change: str
) -> None:
    product, validator, routes, claims = setup(tmp_path)
    reader = tmp_path / "docs/report/source/README.md"
    authority = tmp_path / "reports/needed/scientific-reader-sources.json"
    if change == "new_reader":
        (reader.parent / "new.md").write_text("Unclassified scientific reader")
    elif change == "missing_reader":
        reader.unlink()
    elif change == "account_bytes":
        (tmp_path / "reports/science/account.md").write_text("Changed scientific claim")
    elif change == "account_authority":
        claims[0]["source_report_sha256"] = "0" * 64
    elif change == "route_text":
        reader.write_bytes(
            reader.read_bytes().replace(b"does not establish", b"establishes")
        )
    elif change == "route_missing":
        reader.write_bytes(product.authored_reader(reader.read_bytes()))
    elif change == "route_duplicate":
        reader.write_bytes(reader.read_bytes() * 2)
    elif change in {"excluded_overlap", "empty_exclusion"}:
        authority.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "non_scientific_readers": [
                        {
                            "reader_path": "docs/report/source/README.md",
                            "classification": "engineering_reader",
                            "scope_reason": "UI control scope"
                            if change == "excluded_overlap"
                            else "",
                        }
                    ],
                }
            )
        )
    else:
        source = tmp_path / "other.md"
        source.write_bytes(reader.read_bytes())
        reader.unlink()
        reader.symlink_to(source)
    with pytest.raises(ValueError):
        validator.validate_reader_routes(tmp_path, claims, routes)


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "escape_reader",
        "escape_account",
        "bad_hash",
        "self_link",
        "no_account",
    ],
)
def test_packaged_route_authority_refuses_ambiguous_scope(change: str) -> None:
    product, _ = modules()
    account = {"report_path": "reports/science/account.md", "source_sha256": "a" * 64}
    route = {
        "reader_path": "docs/report/source/README.md",
        "canonical_accounts": [account],
        "scope_reason": "No ecological validation.",
    }
    routes = [route]
    if change == "duplicate":
        routes.append(route)
    elif change == "escape_reader":
        route["reader_path"] = "docs/report/../../outside.md"
    elif change == "escape_account":
        account["report_path"] = "/outside.md"
    elif change == "bad_hash":
        account["source_sha256"] = "unbound"
    elif change == "self_link":
        account["report_path"] = "docs/report/source/README.md"
    else:
        route["canonical_accounts"] = []
    with pytest.raises(ValueError):
        product.parse_routes(json.dumps({"schema_version": 1, "routes": routes}))


def test_actual_portal_producer_indexes_routes_after_writing_scoped_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, _, routes, _ = setup(tmp_path)
    monkeypatch.setattr(product, "load_routes", lambda: routes)
    publication = load(
        "bijux_pollenomics.reporting.presentation.report_portal.publication",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/publication.py",
    )
    reader = tmp_path / "docs/report/source/README.md"
    reader.write_bytes(product.authored_reader(reader.read_bytes()))
    publication.publish_report_portal(tmp_path / "docs/report")
    raw = reader.read_bytes()
    assert b"## Scientific verification and limits" in raw
    registry = json.loads(
        (tmp_path / "docs/report/report_surface_registry.json").read_text()
    )
    governed = next(
        r
        for r in registry["rows"]
        if r["repository_path"] == "docs/report/source/README.md"
    )
    assert governed["content_sha256"] == hashlib.sha256(raw).hexdigest()
    publication.publish_report_portal(tmp_path / "docs/report")
    assert reader.read_bytes() == raw


def test_doc_account_routes_remain_local_and_root_accounts_use_portable_repository_sources() -> (
    None
):
    product, _ = modules()
    route = product.Route(
        "docs/report/source/README.md",
        (
            product.Account("docs/report/qualified/README.md", "a" * 64),
            product.Account("reports/science/account.md", "b" * 64),
        ),
        "Distinct source scope.",
    )
    rendered = product.render_route(b"# Source\n", route)
    assert b"](../qualified/README.md)" in rendered
    assert (
        b"](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/account.md)"
        in rendered
    )
    for invalid in [
        "docs/report/../outside.md",
        "docs//report/reader.md",
        "docs/report/back\\slash.md",
        "docs/report/control\n.md",
    ]:
        with pytest.raises(ValueError):
            product._path(invalid, reader=True)
