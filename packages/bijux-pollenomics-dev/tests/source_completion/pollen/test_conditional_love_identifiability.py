"""Closed affine-mixture support and structural non-identifiability controls."""

from dataclasses import replace
import math
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.identifiability.algebra import (
    affine_family,
    forward_and_jacobian,
)


def test_bounded_family_and_null_direction_without_fit() -> None:
    f = affine_family((0.75, 0.25), (1.0, 1.0), (0.1, 0.9))
    assert f.intercept == (0.75, 0.25)
    assert f.slope == pytest.approx((0.65, -0.65))
    assert f.upper_ratio is not None
    assert f.upper_ratio == pytest.approx(0.25 / 0.65)
    for ratio in [0.0, 0.1, 0.2, float(f.upper_ratio)]:
        q, J = forward_and_jacobian(f, ratio)
        assert q == pytest.approx((0.75, 0.25), abs=2e-15)
        assert J[0][0] * f.slope[0] + J[0][1] == pytest.approx(0, abs=2e-15)
        assert J[0][0] * J[1][1] - J[0][1] * J[1][0] == 0
    assert f.evaluate(1)[1] < 0


def test_aligned_background_has_unbounded_ratio_domain() -> None:
    f = affine_family((0.5, 0.5), (1.0, 1.0), (0.5, 0.5))
    assert f.slope == (0.0, 0.0)
    assert f.upper_ratio is None
    for ratio in [0.0, 0.5, 1.0, 100.0]:
        assert f.evaluate(ratio) == (0.5, 0.5)
        assert forward_and_jacobian(f, ratio)[0] == (0.5, 0.5)


def test_explicit_zero_taxon_can_leave_only_zero_ratio_limit() -> None:
    f = affine_family((1.0, 0.0), (1.0, 1.0), (0.5, 0.5))
    assert f.upper_ratio == 0
    assert f.evaluate(0) == (1.0, 0.0)
    assert f.evaluate(0.01)[1] < 0


def test_zero_observed_and_zero_background_taxon_keeps_unbounded_domain() -> None:
    f = affine_family((1.0, 0.0), (1.0, 1.0), (0.5, 0.0))
    assert f.upper_ratio is None
    assert f.slope == (0.0, 0.0)


@pytest.mark.parametrize("ratio", [-1.0, math.inf, math.nan, True])
def test_invalid_ratio_refuses(ratio: float) -> None:
    f = affine_family((0.5, 0.5), (1.0, 1.0), (0.1, 0.9))
    with pytest.raises(ValueError):
        f.evaluate(ratio)


@pytest.mark.parametrize(
    "pollen", [(0.6, 0.6), (-0.1, 1.1), (math.inf, 0.0), (True, False)]
)
def test_invalid_observation_refuses(pollen: tuple[float, float]) -> None:
    with pytest.raises(ValueError):
        affine_family(pollen, (1.0, 1.0), (0.1, 0.9))


@pytest.mark.parametrize(
    "local,background",
    [
        ((0.0, 1.0), (0.1, 0.9)),
        ((-1.0, 1.0), (0.1, 0.9)),
        ((math.inf, 1.0), (0.1, 0.9)),
        ((1.0, 1.0), (-0.1, 0.9)),
        ((1.0, 1.0), (math.nan, 0.9)),
        ((1e-320, 1.0), (0.1, 0.9)),
    ],
)
def test_invalid_or_unrepresentable_response_refuses(
    local: tuple[float, float], background: tuple[float, float]
) -> None:
    with pytest.raises(ValueError):
        affine_family((0.5, 0.5), local, background)


def test_clipping_an_infeasible_cover_changes_the_forward_composition() -> None:
    f = affine_family((0.75, 0.25), (1.0, 1.0), (0.1, 0.9))
    assert f.evaluate(1.0) == (1.4, -0.4)
    # The clipped vector(1,0) gives a different pollen composition at ratio1.
    clipped = (1.1 / (1.1 + 0.9), 0.9 / (1.1 + 0.9))
    assert clipped != pytest.approx(f.pollen)


def test_nonpositive_forward_denominator_is_a_named_refusal() -> None:
    f = affine_family((0.5, 0.5), (1.0, 1.0), (0.1, 0.9))
    invalid = replace(f, local_response=(-1.0, -1.0))
    with pytest.raises(ValueError, match="denominator"):
        forward_and_jacobian(invalid, 0.0)


def test_finite_but_unrepresentable_ratio_endpoint_refuses() -> None:
    with pytest.raises(ValueError, match="endpoint"):
        affine_family((0.5, 0.5), (1.0, 1.0), (0.0, 1e-320))


def test_artifact_symlink_ancestor_refuses_before_source_read(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.identifiability.producer import (
        qualify,
    )

    repository = tmp_path / "repository"
    artifacts = repository / "artifacts"
    artifacts.mkdir(parents=True)
    destination = artifacts / "destination"
    destination.mkdir()
    alias = artifacts / "alias"
    alias.symlink_to(destination, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink ancestors"):
        qualify(repository, tmp_path / "missing-source", alias / "new-output")
    assert not (destination / "new-output").exists()


def test_artifact_dotdot_escape_refuses_before_source_read(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.identifiability.producer import (
        qualify,
    )

    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    with pytest.raises(ValueError, match="artifact output"):
        qualify(
            repository,
            tmp_path / "missing-source",
            repository / "artifacts" / ".." / "escaped",
        )
    assert not (repository / "escaped").exists()


def test_artifact_symlink_before_dotdot_refuses(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.identifiability.producer import (
        qualify,
    )

    repository = tmp_path / "repository"
    artifacts = repository / "artifacts"
    artifacts.mkdir(parents=True)
    destination = artifacts / "destination"
    destination.mkdir()
    alias = artifacts / "alias"
    alias.symlink_to(destination, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink ancestors"):
        qualify(repository, tmp_path / "missing-source", alias / ".." / "new-output")
    assert not (artifacts / "new-output").exists()


@pytest.mark.parametrize("changed_side", ["historical", "current"])
def test_changed_writer_identity_refuses(changed_side: str) -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.identifiability.producer import (
        require_writer_correspondence,
    )

    historical = {
        name: "old-" + name for name in ["producer.py", "sources.py", "summary.py"]
    }
    current = {name: "current-" + name for name in historical}
    changes = list(historical)
    for name in ["__init__.py", "__main__.py", "authority.py"]:
        historical[name] = current[name] = "unchanged-" + name
    contract = {
        "historical_writer_module_sha256": dict(historical),
        "qualified_current_writer_module_sha256": dict(current),
        "reviewed_deltas": [
            {
                "path": name,
                "original_sha256": historical[name],
                "reviewed_sha256": current[name],
            }
            for name in changes
        ],
    }
    require_writer_correspondence(historical, current, contract)
    target = historical if changed_side == "historical" else current
    target["sources.py"] = "unreviewed"
    with pytest.raises(ValueError, match="source identity changed"):
        require_writer_correspondence(historical, current, contract)


def test_changed_specific_writer_review_refuses() -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.identifiability.producer import (
        require_writer_correspondence,
    )

    historical = {
        name: "old-" + name for name in ["producer.py", "sources.py", "summary.py"]
    }
    current = {name: "current-" + name for name in historical}
    changes = list(historical)
    for name in ["__init__.py", "__main__.py", "authority.py"]:
        historical[name] = current[name] = "unchanged-" + name
    contract = {
        "historical_writer_module_sha256": historical,
        "qualified_current_writer_module_sha256": current,
        "reviewed_deltas": [
            {
                "path": name,
                "original_sha256": historical[name],
                "reviewed_sha256": "unreviewed",
            }
            for name in changes
        ],
    }
    with pytest.raises(ValueError, match="Specific reviewed"):
        require_writer_correspondence(historical, current, contract)
