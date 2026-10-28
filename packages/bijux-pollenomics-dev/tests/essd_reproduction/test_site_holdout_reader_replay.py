"""Authenticate generated prose without relaxing the four-product byte contract."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    Account,
    Route,
    authored_reader,
    render_route,
)

ROOT = Path(__file__).resolve().parents[4]
FAMILY = ROOT / "docs/report/pollen-reconstruction/author-example-site-mean-holdout"


@pytest.fixture
def replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load only the guarded reader; all four retained products below are own bytes."""
    spec = importlib.util.spec_from_file_location(
        "author_pollen_reader_replay",
        ROOT
        / "docs/report/pollen-reconstruction/author-example-site-mean-holdout/replay.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repository = tmp_path / "repository"
    relative = (
        "docs/report/pollen-reconstruction/author-example-site-mean-holdout/REPORT.md"
    )
    family = repository / Path(relative).parent
    family.mkdir(parents=True)
    route = Route(
        reader_path=relative,
        accounts=(Account(report_path="reports/science/own-custody.md"),),
        scope_reason="Own guarded reader fixture, without a scientific qualification claim.",
    )
    own = {
        "REPORT.md": render_route(
            b"# Own retained reader\n\nDeclared own units: 177.\n", route
        ),
        "report.json": b'{"own_value":0.5}\n',
        "scores.csv": b"own_id,loss\na,0.25\n",
        "predictions.csv": b"own_id,fraction\na,0.5\n",
    }
    for name, raw in own.items():
        (family / name).write_bytes(raw)
    monkeypatch.setattr(module, "REPOSITORY", repository)
    monkeypatch.setattr(module, "FAMILY", family)
    monkeypatch.setattr(module, "load_routes", lambda: {relative: route})
    monkeypatch.setitem(globals(), "FAMILY", family)
    return module


@pytest.fixture
def products(tmp_path: Path, replay: ModuleType) -> Path:
    """Keep own generated products separate from their retained fixture directory."""
    output = tmp_path / "products"
    output.mkdir()
    for name in ("REPORT.md", "report.json", "scores.csv", "predictions.csv"):
        (output / name).write_bytes((FAMILY / name).read_bytes())
    return output


def test_generated_authored_body_becomes_exact_governed_reader(
    replay: ModuleType, products: Path
) -> None:
    tracked = (FAMILY / "REPORT.md").read_bytes()
    (products / "REPORT.md").write_bytes(authored_reader(tracked))
    replay._render_report(products)
    assert (products / "REPORT.md").read_bytes() == tracked
    replay._check_output(products)


def test_current_rendered_reader_is_idempotent(
    replay: ModuleType, products: Path
) -> None:
    expected = (products / "REPORT.md").read_bytes()
    replay._render_report(products)
    assert (products / "REPORT.md").read_bytes() == expected


def test_changed_scientific_prose_is_refused(
    replay: ModuleType, products: Path
) -> None:
    original = authored_reader((products / "REPORT.md").read_bytes())
    (products / "REPORT.md").write_bytes(original.replace(b"177", b"178", 1))
    with pytest.raises(ValueError):
        replay._render_report(products)


def test_changed_generated_footer_is_refused(
    replay: ModuleType, products: Path
) -> None:
    raw = (products / "REPORT.md").read_bytes()
    (products / "REPORT.md").write_bytes(
        raw.replace(
            b"Scientific verification and limits", b"Altered verification and limits", 1
        )
    )
    with pytest.raises(ValueError, match="route differs"):
        replay._render_report(products)


def test_changed_tracked_footer_is_refused(
    replay: ModuleType, products: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    retained = tmp_path / "retained"
    retained.mkdir()
    raw = (FAMILY / "REPORT.md").read_bytes()
    (retained / "REPORT.md").write_bytes(
        raw.replace(
            b"Scientific verification and limits", b"Altered verification and limits", 1
        )
    )
    monkeypatch.setattr(replay, "REPOSITORY", tmp_path)
    monkeypatch.setattr(replay, "FAMILY", retained)
    original_routes = replay.load_routes()
    monkeypatch.setattr(
        replay,
        "load_routes",
        lambda: {
            "retained/REPORT.md": original_routes[
                "docs/report/pollen-reconstruction/author-example-site-mean-holdout/REPORT.md"
            ]
        },
    )
    with pytest.raises(ValueError, match="route differs"):
        replay._render_report(products)


@pytest.mark.parametrize("name", ["report.json", "scores.csv", "predictions.csv"])
def test_numeric_product_bytes_stay_exact(
    replay: ModuleType, products: Path, name: str
) -> None:
    path = products / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="bytes differ"):
        replay._check_output(products)


def test_extra_output_is_refused(replay: ModuleType, products: Path) -> None:
    (products / "extra").write_bytes(b"unowned")
    with pytest.raises(ValueError, match="file set"):
        replay._check_output(products)


def test_linked_output_is_refused(replay: ModuleType, products: Path) -> None:
    path = products / "report.json"
    path.unlink()
    path.symlink_to(FAMILY / "report.json")
    with pytest.raises(ValueError, match="file set"):
        replay._check_output(products)


def test_all_distributions_use_same_source_root(replay: ModuleType) -> None:
    assert (
        tuple(
            ROOT / "packages" / name / "src"
            for name in (
                "bijux-pollenomics",
                "bijux-pollenomics-dev",
                "bijux-pollenomics-lra",
                "pollenomics",
            )
        )
        == replay.SOURCE_ROOTS
    )


@pytest.mark.parametrize("kind", ["missing", "symlink"])
def test_generated_reader_requires_an_ordinary_owned_file(
    replay: ModuleType,
    products: Path,
    kind: str,
) -> None:
    """Missing or linked Markdown refuses before canonical rendering or writes."""
    path = products / "REPORT.md"
    path.unlink()
    if kind == "symlink":
        path.symlink_to(FAMILY / "REPORT.md")
    with pytest.raises(ValueError, match="regular file"):
        replay._render_report(products)
