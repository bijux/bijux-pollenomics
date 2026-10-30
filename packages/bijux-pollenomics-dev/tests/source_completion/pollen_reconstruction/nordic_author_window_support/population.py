"""Independent author CSV arithmetic and complete native core/window expectations."""

from __future__ import annotations

from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import io
from typing import Any

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.population import (
    group_mass,
)

from .native_owners import native_owner, require, sample_account


def source_decimal(value: object) -> Decimal:
    require(type(value) is str and bool(value), "literal CSV numeric string")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Independent nonnumeric author parameter") from exc
    require(result.is_finite(), "finite author parameter")
    return result


def parameter_evidence(
    bodies: dict[str, bytes], protocol: dict[str, Any], binding: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    policy = protocol["author_lookup_contract"]
    reader = csv.DictReader(io.StringIO(bodies["lookup"].decode("latin-1")))
    require(
        reader.fieldnames == ["oldvar", "RPP.LANDCLIMII"] == policy["source_fields"],
        "literal author lookup columns",
    )
    lookup: dict[str, list[dict[str, Any]]] = {}
    count = 0
    for ordinal, row in enumerate(reader, 2):
        name, target = row.get("oldvar"), row.get("RPP.LANDCLIMII")
        require(
            set(row) == set(policy["source_fields"])
            and type(name) is str
            and bool(name)
            and type(target) is str
            and bool(target),
            "complete nonempty CSV assignment",
        )
        assert isinstance(name, str) and isinstance(target, str)
        require(
            name not in lookup or lookup[name][0]["author_target"] == target,
            "unambiguous duplicate author assignment",
        )
        lookup.setdefault(name, []).append(
            {"row_number": ordinal, "oldvar": name, "author_target": target}
        )
        count += 1
    targets = {value[0]["author_target"] for value in lookup.values()} - set(
        policy["excluded_targets"]
    )
    require(
        count == policy["data_rows"]
        and len(lookup) == policy["unique_source_names"]
        and len(targets) == policy["parameter_targets"],
        "full author lookup populations",
    )
    mean_reader = csv.DictReader(io.StringIO(bodies["mean"].decode("utf-8")))
    cov_reader = csv.DictReader(io.StringIO(bodies["covariance"].decode("utf-8")))
    means, covariance = list(mean_reader), list(cov_reader)
    names = [row.get("A.series") for row in means]
    require(
        len(names) == 31
        and all(type(name) is str and bool(name) for name in names)
        and len(set(names)) == 31
        and set(names) == targets,
        "complete unique 31-target mean axis",
    )
    require(
        mean_reader.fieldnames == ["A.series", "alpha", "vg"]
        and cov_reader.fieldnames == ["A.series", *names]
        and [row.get("A.series") for row in covariance] == names
        and all(set(row) == {"A.series", "alpha", "vg"} for row in means)
        and all(list(row) == ["A.series", *names] for row in covariance),
        "exact ordered mean and covariance axes",
    )
    qualified = []
    nonzero = 0
    for i, name in enumerate(names):
        require(
            source_decimal(means[i]["alpha"]) > 0
            and source_decimal(means[i]["vg"]) > 0
            and source_decimal(covariance[i][name]) >= 0,
            "positive mean/fall speed and nonnegative variance",
        )
        for j, other in enumerate(names):
            value = source_decimal(covariance[i][other])
            require(
                value == source_decimal(covariance[j][name]),
                "exact covariance symmetry",
            )
            nonzero += int(i != j and value != 0)
        qualified.append(
            {
                "author_target": name,
                "alpha_source_text": means[i]["alpha"],
                "fall_speed_source_text": means[i]["vg"],
                "alpha_variance_source_text": covariance[i][name],
            }
        )
    require(
        binding["schema_version"] == "swedish-landclim-author-parameter-binding.v1"
        and binding["author_target_count"] == 31
        and binding["scientific_admission_allowed"] is False
        and binding["covariance_nonzero_offdiagonal_cells"] == nonzero == 0,
        "qualified coherent parameter profile",
    )
    require(
        [{key: row[key] for key in qualified[0]} for row in binding["parameters"]]
        == qualified,
        "all qualified parameter source strings",
    )
    chosen = [names.index(name) for name in protocol["taxa"]]
    selected = {
        "taxa": protocol["taxa"],
        "alpha_text": [means[i]["alpha"] for i in chosen],
        "fall_speed_m_s_text": [means[i]["vg"] for i in chosen],
        "covariance_text": [
            [covariance[i][name] for name in protocol["taxa"]] for i in chosen
        ],
        "literal_file_line_numbers": [i + 2 for i in chosen],
    }
    require(
        selected
        == {
            "taxa": protocol["parameters"]["targets"],
            **{key: protocol["parameters"][key] for key in selected if key != "taxa"},
        },
        "selected exact source parameter block",
    )
    for core in protocol["cores"]:
        for axis in core["native_axes"]:
            require(
                axis["source_name"] in lookup
                and {row["author_target"] for row in lookup[axis["source_name"]]}
                == {axis["author_target"]},
                "every required native-to-author mapping",
            )
    return {
        "schema_version": "nordic-author-parameters.v1",
        "axis": names,
        "source_pins": protocol["author_sources"],
        "lookup": {
            "rows": count,
            "unique_source_names": len(lookup),
            "parameter_targets": len(targets),
            "excluded_targets": policy["excluded_targets"],
        },
        "mean_rows": means,
        "covariance_rows": covariance,
        "selected": selected,
    }, lookup


def expected_core(
    source: dict[str, Any],
    core: dict[str, Any],
    protocol: dict[str, Any],
    lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    require(
        protocol["schema_version"] == "nordic-author-window-support-protocol.v1"
        and protocol["taxa"] == ["Betula", "Pinus"]
        and protocol["windows"] == [[a, a + 500] for a in range(2700, 5700, 500)]
        and core in protocol["cores"],
        "explicit author/core/window contract",
    )
    chronology, metadata, owners = native_owner(source, core)
    samples = [
        sample_account(owner, index, core, protocol, lookup)
        for index, owner in enumerate(owners)
    ]
    unknown = [
        row["sample_id"]
        for row in samples
        if row["age_disposition"] == "unassignable_selected_age"
    ]
    windows = [
        {
            "window": pair,
            **group_mass([row for row in samples if row["window"] == pair], unknown),
        }
        for pair in protocol["windows"]
    ]
    totals = group_mass(samples, [])
    totals["known_valid_pollen_cell_sum"] = sum(
        row["known_valid_pollen_cell_sum"] for row in samples
    )
    states: Counter[str] = Counter()
    for row in samples:
        states.update(
            {key: value for key, value in row["datum_status_counts"].items() if value}
        )
    return {
        "schema_version": "nordic-author-core-support.v1",
        "key": core["key"],
        "status": "author_target_source_support_accounted",
        "source": core["source"],
        "identity": core["identity"],
        "country": core["country"],
        "physical_family": core["physical_family"],
        "native_axes": core["native_axes"],
        "taxon_axis": protocol["taxa"],
        "chronology": chronology,
        "native_source_metadata": metadata,
        "samples": samples,
        "windows": windows,
        "population": {
            "samples": len(samples),
            "age_disposition_counts": dict(
                Counter(row["age_disposition"] for row in samples)
            ),
            "selected_age_status_counts": dict(
                Counter(row["selected_age_status"] for row in samples)
            ),
            "panel_complete_samples": sum(row["panel_complete"] for row in samples),
            "full_mass_complete_samples": sum(
                row["pollen_N"] is not None for row in samples
            ),
        },
        "source_totals": totals,
        "support_summary": {
            "supported_windows": sum(row["status"] == "supported" for row in windows),
            "window_status_counts": dict(Counter(row["status"] for row in windows)),
            "author_target_state_counts": dict(
                Counter(axis["status"] for row in samples for axis in row["taxa"])
            ),
            "datum_status_counts": dict(states),
        },
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        **{
            key: protocol[key]
            for key in ("scope", "suppression_semantics", "rights_and_attribution")
        },
    }
