from __future__ import annotations

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bijux_pollenomics_dev.docs.badge_sync import (
    BadgeTarget,
    load_badge_catalog,
    render_badge_block,
    synchronize_badges,
)

GENERATED_BLOCK_RE = re.compile(
    r"<!-- bijux-pollenomics-badges:generated:start -->.*?<!-- bijux-pollenomics-badges:generated:end -->",
    re.DOTALL,
)


def test_badge_catalog_exposes_expected_templates() -> None:
    catalog = load_badge_catalog()
    assert set(catalog) == {
        "family-docs-badge",
        "family-ghcr-badge",
        "family-pypi-badge",
        "maintainer-summary",
        "package-summary",
        "repository-summary",
    }


def test_repository_badge_block_renders_public_badge_groups() -> None:
    rendered = render_badge_block(
        BadgeTarget(path=Path("README.md"), kind="repository")
    )
    assert rendered.count("https://img.shields.io/pypi/v/") == 2
    assert rendered.count("/pkgs/container/") == 2
    assert rendered.count("https://bijux.io/bijux-pollenomics/bijux-pollenomics/") == 2
    assert "https://github.com/bijux?tab=packages" in rendered
    assert (
        "https://github.com/orgs/bijux/packages?repo_name=bijux-pollenomics"
        not in rendered
    )


def test_package_badge_block_prioritizes_the_public_distribution() -> None:
    rendered = render_badge_block(
        BadgeTarget(
            path=Path("packages/bijux-pollenomics/README.md"),
            kind="package",
            package_slug="bijux-pollenomics",
        )
    )
    assert (
        "\n[![bijux-pollenomics](https://img.shields.io/pypi/v/bijux-pollenomics"
        in rendered
    )
    assert (
        "\n[![bijux-pollenomics](https://img.shields.io/badge/bijux--pollenomics-ghcr"
        in rendered
    )
    assert (
        "\n[![bijux-pollenomics docs](https://img.shields.io/badge/docs-bijux--pollenomics"
        in rendered
    )


def test_alias_package_badge_block_prioritizes_the_alias_distribution() -> None:
    rendered = render_badge_block(
        BadgeTarget(
            path=Path("packages/pollenomics/README.md"),
            kind="package",
            package_slug="pollenomics",
        )
    )
    assert "\n[![pollenomics](https://img.shields.io/pypi/v/pollenomics" in rendered
    assert "\n[![pollenomics](https://img.shields.io/badge/pollenomics-ghcr" in rendered
    assert (
        "\n[![pollenomics docs](https://img.shields.io/badge/docs-pollenomics"
        in rendered
    )


def test_badge_surfaces_are_synchronized() -> None:
    assert synchronize_badges(check=True) == []


def test_managed_surfaces_only_use_generated_badges() -> None:
    targets = [
        Path("README.md"),
        Path("docs/index.md"),
        Path("packages/bijux-pollenomics/README.md"),
        Path("packages/pollenomics/README.md"),
        Path("packages/bijux-pollenomics-dev/README.md"),
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        stripped = GENERATED_BLOCK_RE.sub("", text)
        assert "[![" not in stripped, (
            f"{path} contains inline badges outside the generated block"
        )
