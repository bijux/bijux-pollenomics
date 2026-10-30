"""Keep opt-in historical arithmetic inside its finite source correspondence."""

from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.controlled_numerical import (
    author_evaluations as author,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    numerical_precision as source,
)

PLAIN_HEADER = b'''def hellinger_distance(
    predicted: Mapping[str, float], observed: Mapping[str, float]
) -> float:
    """Distance between two closed compositions on the same named taxon axis."""
'''
PROFILE_HEADER = b'''def hellinger_distance(
    predicted: Mapping[str, float],
    observed: Mapping[str, float],
    *,
    arithmetic_profile: HellingerArithmeticProfile = "stable",
) -> float:
    """Distance on a shared taxon axis with explicit arithmetic provenance.

    The stable default preserves small representable distances. The source-compatible
    profile retains the arithmetic order of the named historical source, including
    its cancellation and underflow limitations; it supplies no tolerance allowance.
    """
    if arithmetic_profile not in ("stable", "source-compatible-22c6e480"):
        raise ValueError("Unknown Hellinger arithmetic profile")
'''
PROFILE_ALIAS = b'HellingerArithmeticProfile = Literal["stable", "source-compatible-22c6e480"]\n\n\n'
HISTORICAL_BRANCH = b"""    if arithmetic_profile == "source-compatible-22c6e480":
        # The source used Python 3.11's left-to-right float sum. Accumulate
        # explicitly because newer Python versions compensate builtin sum.
        total = 0.0
        for taxon in prediction:
            total += (sqrt(prediction[taxon]) - sqrt(observation[taxon])) ** 2
        return sqrt(0.5 * total)
"""
Case = tuple[Path, dict[str, Any], str, Any, Path]


def _texts() -> tuple[bytes, bytes, bytes]:
    """Assemble own module context around independently declared public profile spans."""
    imports = b"from collections.abc import Mapping\nfrom math import hypot, sqrt\n"
    globals_body = b"OWN_SCALE = 1\n\n"
    prelude = b"    prediction = predicted\n    observation = observed\n"
    tail = b"\n\ndef score_pollen(value):\n    return OWN_SCALE * value\n"
    old = imports + globals_body + PLAIN_HEADER + prelude + source._OLD_RETURN + tail
    stable = imports + globals_body + PLAIN_HEADER + prelude + source._NEW_RETURN + tail
    profile = (
        imports
        + b"from typing import Literal\n"
        + globals_body
        + PROFILE_ALIAS
        + PROFILE_HEADER
        + prelude
        + HISTORICAL_BRANCH
        + source._NEW_RETURN
        + tail
    )
    return old, stable, profile


def _own_history(monkeypatch: pytest.MonkeyPatch, old: bytes) -> None:
    """Bind invented old bytes without changing any real captured source record."""
    monkeypatch.setattr(source, "_HISTORICAL_SHA256", hashlib.sha256(old).hexdigest())
    monkeypatch.setattr(source, "_HISTORICAL_BYTES", len(old))


def test_explicit_profile_normalizes_to_the_exact_stable_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check both inverse levels and the declared keyword-only stable default."""
    old, stable, profile = _texts()
    _own_history(monkeypatch, old)
    assert source.stable_hellinger_profile_basis(stable) == stable
    assert source.stable_hellinger_profile_basis(profile) == stable
    assert source.hellinger_precision_extension_matches(old, stable)
    assert source.hellinger_precision_extension_matches(old, profile)
    tree = ast.parse(profile.decode())
    function = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "hellinger_distance"
    )
    assert [argument.arg for argument in function.args.kwonlyargs] == [
        "arithmetic_profile"
    ]
    assert len(function.args.kw_defaults) == 1
    default = function.args.kw_defaults[0]
    assert isinstance(default, ast.Constant) and default.value == "stable"
    author._prove_delta(author.METRICS, old, profile)


def _damaged(profile: bytes, damage: str) -> bytes:
    """Change one independent semantic or provenance obligation in own source text."""
    if damage == "default":
        return profile.replace(b'= "stable",', b'= "source-compatible-22c6e480",', 1)
    if damage == "profile_alias":
        return profile.replace(b'Literal["stable",', b'Literal["unreviewed",', 1)
    if damage == "helper_import":
        return profile.replace(
            b"from typing import Literal", b"from foreign import Literal", 1
        )
    if damage == "missing_alias":
        return profile.replace(PROFILE_ALIAS, b"", 1)
    if damage == "missing_branch":
        return profile.replace(HISTORICAL_BRANCH, b"", 1)
    if damage == "duplicate_branch":
        return profile.replace(HISTORICAL_BRANCH, HISTORICAL_BRANCH * 2, 1)
    if damage == "historical_loop":
        return profile.replace(b"total +=", b"total -=", 1)
    if damage == "historical_condition":
        return profile.replace(
            b'if arithmetic_profile == "source-compatible-22c6e480":',
            b'if arithmetic_profile != "source-compatible-22c6e480":',
            1,
        )
    if damage == "historical_comment":
        return profile.replace(b"left-to-right float sum", b"unreviewed sum", 1)
    if damage == "profile_validation":
        return profile.replace(
            b"if arithmetic_profile not in", b"if arithmetic_profile in", 1
        )
    if damage == "definition_decorator":
        return profile.replace(
            b"def hellinger_distance(", b"@unreviewed\ndef hellinger_distance(", 1
        )
    if damage == "extra_global":
        return profile + b"UNREVIEWED_GLOBAL = 1\n"
    if damage == "extra_import":
        return b"import foreign\n" + profile
    if damage == "consumed_score":
        return profile.replace(
            b"return OWN_SCALE * value", b"return OWN_SCALE + value", 1
        )
    if damage == "stable_body":
        return profile.replace(b") / sqrt(2.0)", b") / sqrt(3.0)", 1)
    assert damage == "unrelated_comment"
    return profile + b"# Own unrelated prose is not an Author AST postimage gate.\n"


@pytest.mark.parametrize(
    "damage",
    [
        "default",
        "profile_alias",
        "helper_import",
        "missing_alias",
        "missing_branch",
        "duplicate_branch",
        "historical_loop",
        "historical_condition",
        "historical_comment",
        "profile_validation",
        "definition_decorator",
        "extra_global",
        "extra_import",
        "consumed_score",
        "stable_body",
        "unrelated_comment",
    ],
)
def test_finite_profile_preserves_both_scientific_scope_boundaries(
    monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Refuse all undeclared bytes while preserving the Author unconsumed-body limit."""
    old, stable, profile = _texts()
    _own_history(monkeypatch, old)
    assert source.stable_hellinger_profile_basis(profile) == stable
    assert source.hellinger_precision_extension_matches(old, profile)
    author._prove_delta(author.METRICS, old, profile)
    changed = _damaged(profile, damage)
    assert changed != profile
    assert not source.hellinger_precision_extension_matches(old, changed)
    if damage in {"stable_body", "unrelated_comment"}:
        # Author's frozen consumer does not call Hellinger; its existing AST
        # boundary does not claim whole-source or unconsumed-body equality.
        author._prove_delta(author.METRICS, old, changed)
    else:
        with pytest.raises(ReportRebuildError):
            author._prove_delta(author.METRICS, old, changed)


@pytest.mark.parametrize("body", [b"", b"x" * (16 * 1024 + 1)])
def test_profile_normalization_preserves_input_bounds(body: bytes) -> None:
    """Neither an empty nor oversized current module supplies a stable basis."""
    assert source.stable_hellinger_profile_basis(body) is None


@pytest.fixture(params=tuple(source._QUALIFIED_CAPTURES))
def bound_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Case:
    """Bind own profile bytes to each unchanged exact capture coordinate."""
    old, _, profile = _texts()
    _own_history(monkeypatch, old)
    prefix = str(request.param)
    capture_sha, logical_prefix = source._QUALIFIED_CAPTURES[prefix]
    logical = logical_prefix + source.METRICS_SOURCE
    identity = {"sha256": hashlib.sha256(old).hexdigest(), "bytes": len(old)}
    descriptor = SimpleNamespace(
        capture={"sha256": capture_sha},
        members={logical: identity},
        groups=[{"resolved_paths": [(logical, source.METRICS_SOURCE)]}],
    )

    def read(selected: str) -> bytes:
        assert selected == logical
        return old

    resolver = SimpleNamespace(
        repository=tmp_path,
        prefix=prefix,
        descriptor=descriptor,
        detached=frozenset({logical}),
        read_source=read,
        fresh=lambda: None,
    )
    path = tmp_path / source.METRICS_SOURCE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(profile)
    return (
        tmp_path,
        {"path": source.METRICS_SOURCE, **identity},
        logical,
        resolver,
        path,
    )


def _check(case: Case) -> dict[str, Any]:
    """Use the actual custody entrypoint, not an extracted or substituted function."""
    root, identity, logical, resolver, _ = case
    return source.validated_hellinger_precision_source(
        root, identity, logical, resolver
    )


def test_profile_keeps_exact_binding_and_dated_output_limits(
    bound_profile: Case,
) -> None:
    """A declared profile remains opt-in and cannot relabel old native results."""
    result = _check(bound_profile)
    assert result["default_arithmetic_profile"] == "stable"
    assert result["explicit_historical_profile_available"] is True
    assert result["historical_profile_requires_explicit_selection"] is True
    assert result["whole_old_module_reconstructed"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["historical_numeric_outputs_regenerated"] is False
    assert result["historical_native_software_equal_current_claimed"] is False
    assert result["saved_output_equality_from_source_law_claimed"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "capture",
        "capture_sha",
        "logical",
        "detached",
        "member",
        "duplicate_mapping",
        "repository",
        "boolean_bytes",
        "old_body",
        "current_default",
        "symlink",
        "ancestor_symlink",
        "hardlink",
        "freshness",
    ],
)
def test_profile_cannot_weaken_existing_source_custody(
    bound_profile: Case, tmp_path: Path, damage: str
) -> None:
    """Apply unchanged binding and current-file refusals to the newly profiled source."""
    root, identity, logical, resolver, path = bound_profile
    _check(bound_profile)
    if damage == "capture":
        resolver.prefix = "data/unqualified"
    elif damage == "capture_sha":
        resolver.descriptor.capture["sha256"] = "0" * 64
    elif damage == "logical":
        logical += "/other"
    elif damage == "detached":
        resolver.detached = frozenset()
    elif damage == "member":
        resolver.descriptor.members[logical] = {"bytes": 0, "sha256": "0" * 64}
    elif damage == "duplicate_mapping":
        resolver.descriptor.groups.append(resolver.descriptor.groups[0])
    elif damage == "repository":
        resolver.repository = tmp_path / "other"
    elif damage == "boolean_bytes":
        identity["bytes"] = True
    elif damage == "old_body":
        resolver.read_source = lambda _: b"Changed own historical source\n"
    elif damage == "current_default":
        path.write_bytes(_damaged(path.read_bytes(), "default"))
    elif damage == "symlink":
        outside = tmp_path / "outside.py"
        path.rename(outside)
        path.symlink_to(outside)
    elif damage == "ancestor_symlink":
        outside = path.parent.with_name(path.parent.name + "-outside")
        path.parent.rename(outside)
        path.parent.symlink_to(outside, target_is_directory=True)
    elif damage == "hardlink":
        os.link(path, tmp_path / "linked.py")
    else:
        calls = 0

        def changing() -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                path.write_bytes(path.read_bytes() + b"# concurrent own change\n")

        resolver.fresh = changing
    expected = (
        ReportOwnershipError
        if damage in {"symlink", "ancestor_symlink"}
        else ReportRebuildError
    )
    with pytest.raises(expected):
        source.validated_hellinger_precision_source(root, identity, logical, resolver)
