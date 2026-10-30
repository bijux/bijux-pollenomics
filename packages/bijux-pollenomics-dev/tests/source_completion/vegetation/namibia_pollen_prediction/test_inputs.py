"""Controlled source tables preserve native identities, labels and quantities."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction import (
    inputs,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_source_join import (
    REPLAY,
)

COLUMNS = ("Aca [#]", "Dichrostachys [#]", "Grewia [#]", "Poac [#]", "Comeae [#]")
AREAS = tuple(taxon + " [m**2]" for taxon in inputs.TAXA)
AXIS = tuple(zip(inputs.TAXA, COLUMNS, AREAS, strict=True))


def source_tables() -> tuple[
    list[dict[str, str]], list[dict[str, str]], dict[str, tuple[str, str]]
]:
    pollen = []
    vegetation = []
    coordinates = {}
    for index, site in enumerate(inputs.SITES):
        lon = 3.01 if site == "Namibia_T5" else float(index)
        coordinates[site] = ("0.000000", f"{lon:.6f}")
        common = {"Event": site, "Latitude": "0.0000", "Longitude": f"{lon:.4f}"}
        counts = dict.fromkeys(COLUMNS, "100")
        if site == "Namibia_T10":
            counts[COLUMNS[-1]] = "1994"
        pollen.append({**common, **counts})
        for radius in inputs.RADII:
            vegetation.append(
                {
                    **common,
                    "Ring sect radius [m]": str(radius),
                    **dict.fromkeys(AREAS, "1.0000000000000001"),
                }
            )
    return pollen, vegetation, coordinates


def test_native_tokens_and_decimal_values_are_separate_from_normalized_compositions() -> (
    None
):
    pollen, vegetation, coordinates = source_tables()
    before = deepcopy((pollen, vegetation, coordinates))
    result = inputs.assemble(pollen, vegetation, coordinates, AXIS)
    assert before == (pollen, vegetation, coordinates)
    assert sum(map(sum, result.counts.values())) == 6894
    assert result.areas[("Namibia_T1", 100)] == (1.0,) * 5
    assert result.area_tokens[("Namibia_T1", 100)] == ("1.0000000000000001",) * 5
    assert len(result.areas) == 150 and len(result.counts) == 10


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "Infinity", "1e1000", "1_000", ""])
def test_unsupported_area_is_not_zero_or_a_silently_accepted_native_token(
    value: str,
) -> None:
    pollen, vegetation, coordinates = source_tables()
    vegetation[0][AREAS[0]] = value
    with pytest.raises(ValueError, match="area"):
        inputs.assemble(pollen, vegetation, coordinates, AXIS)


@pytest.mark.parametrize("value", ["0", "-1", "1.5", "True", "1_000", ""])
def test_native_positive_integer_counts_have_an_exact_lexical_contract(
    value: str,
) -> None:
    pollen, vegetation, coordinates = source_tables()
    pollen[0][COLUMNS[0]] = value
    with pytest.raises(ValueError, match="count"):
        inputs.assemble(pollen, vegetation, coordinates, AXIS)


@pytest.mark.parametrize(
    "kind",
    ["duplicate", "missing_radius", "foreign_event", "display_coordinate", "groups"],
)
def test_relational_or_group_changes_refuse(kind: str) -> None:
    pollen, vegetation, coordinates = source_tables()
    if kind == "duplicate":
        vegetation[1] = vegetation[0].copy()
    elif kind == "missing_radius":
        vegetation.pop()
    elif kind == "foreign_event":
        vegetation[0]["Event"] = "unknown"
    elif kind == "display_coordinate":
        vegetation[0]["Latitude"] = "1.0000"
    else:
        coordinates["Namibia_T5"] = ("0.000000", "14.000000")
    with pytest.raises(ValueError, match="population|join|overlap"):
        inputs.assemble(pollen, vegetation, coordinates, AXIS)


def test_original_event_metadata_precision_and_uniqueness_are_explicit() -> None:
    text = (
        "Event(s):\t"
        + "\n\t".join(
            f"{site} * LATITUDE: -19.123456 * LONGITUDE: 17.123456 * LOCATION: Namibia"
            for site in inputs.SITES
        )
        + "\n*/\n"
    )
    result = inputs.event_coordinates(text)
    assert result["Namibia_T4"] == ("-19.123456", "17.123456")
    with pytest.raises(ValueError, match="identities"):
        inputs.event_coordinates(
            text.replace(
                "*/\n",
                "\tNamibia_T4 * LATITUDE: -19.123456 * LONGITUDE: 17.123456 *\n*/\n",
            )
        )


def test_declared_spherical_distance_is_symmetric_and_uses_metre_scale() -> None:
    first, second = (0.0, 0.0), (0.0, 1.0)
    assert inputs.distance(first, second) == inputs.distance(second, first)
    assert inputs.distance(first, second) == pytest.approx(math.pi * 6_371_000 / 180)
    assert inputs.distance(first, first) == 0


def test_loader_refuses_symlinked_current_join_reader_before_execution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    from types import SimpleNamespace

    original = tmp_path / "original.py"
    original.write_text("raise AssertionError('must not run')")
    path = tmp_path / REPLAY
    path.parent.mkdir(parents=True)
    path.symlink_to(original)
    monkeypatch.setattr(
        inputs,
        "validated_external_report_sources",
        lambda *_: SimpleNamespace(directory=tmp_path),
    )
    with pytest.raises(ReportRebuildError, match="regular file"):
        inputs.load(tmp_path, tmp_path)
