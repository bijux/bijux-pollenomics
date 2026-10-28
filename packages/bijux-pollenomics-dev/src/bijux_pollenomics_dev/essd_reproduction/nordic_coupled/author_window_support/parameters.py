"""Bind literal author lookup assignments to one coherent full parameter axis."""

from __future__ import annotations

from copy import deepcopy
import csv
from decimal import Decimal, InvalidOperation
import io
from typing import Any, cast

from ...physical_forward.inputs import require


def lookup_rows(raw: bytes, contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Retain consistent duplicate assignments and their literal file lines."""
    reader = csv.DictReader(io.StringIO(raw.decode("latin-1")))
    require(
        reader.fieldnames == contract["source_fields"], "Author lookup fields differ"
    )
    rows = []
    assignments: dict[str, str] = {}
    for number, row in enumerate(reader, 2):
        source, target = row.get("oldvar"), row.get("RPP.LANDCLIMII")
        require(
            set(row) == set(contract["source_fields"])
            and type(source) is str
            and bool(source)
            and type(target) is str
            and bool(target),
            "Literal author lookup assignment required",
        )
        source, target = cast(str, source), cast(str, target)
        require(
            source not in assignments or assignments[source] == target,
            "Conflicting duplicate author lookup assignment",
        )
        assignments[source] = target
        rows.append({"row_number": number, "oldvar": source, "author_target": target})
    targets = set(assignments.values()) - set(contract["excluded_targets"])
    require(
        len(rows) == contract["data_rows"]
        and len(assignments) == contract["unique_source_names"]
        and len(targets) == contract["parameter_targets"],
        "Complete author lookup population differs",
    )
    return rows


def decimal(value: object) -> Decimal:
    """Validate source numeric strings without rounding them through binary64."""
    require(type(value) is str and bool(value), "Literal parameter number required")
    try:
        result = Decimal(cast(str, value))
    except InvalidOperation as exc:
        raise ValueError("Invalid author parameter number") from exc
    require(result.is_finite(), "Nonfinite author parameter number")
    return result


def bind_parameters(
    mean: bytes,
    covariance: bytes,
    rows: list[dict[str, Any]],
    protocol: dict[str, Any],
    binding: dict[str, Any],
) -> dict[str, Any]:
    """Validate all 31 ordered rows before selecting the declared two-target block."""
    means = list(csv.DictReader(io.StringIO(mean.decode("utf-8"))))
    covariances = list(csv.DictReader(io.StringIO(covariance.decode("utf-8"))))
    names = [r.get("A.series") for r in means]
    expected_targets = {r["author_target"] for r in rows} - set(
        protocol["author_lookup_contract"]["excluded_targets"]
    )
    require(
        len(names) == 31
        and all(type(n) is str and n for n in names)
        and len(set(names)) == 31
        and set(names) == expected_targets
        and names == [r.get("A.series") for r in covariances]
        and list(covariances[0]) == ["A.series", *names]
        and all(set(r) == {"A.series", "alpha", "vg"} for r in means)
        and all(list(r) == ["A.series", *names] for r in covariances),
        "Full coherent author mean/covariance axes differ",
    )
    nonzero_offdiagonal = 0
    expected = []
    for i, (name, row) in enumerate(zip(names, means, strict=True)):
        require(
            decimal(row["alpha"]) > 0 and decimal(row["vg"]) > 0,
            "Positive author mean and fall speed required",
        )
        require(
            decimal(covariances[i][name]) >= 0, "Negative author covariance diagonal"
        )
        for j, other in enumerate(names):
            value = decimal(covariances[i][other])
            require(
                value == decimal(covariances[j][name]), "Asymmetric author covariance"
            )
            nonzero_offdiagonal += int(i != j and value != 0)
        expected.append(
            {
                "author_target": name,
                "alpha_source_text": row["alpha"],
                "fall_speed_source_text": row["vg"],
                "alpha_variance_source_text": covariances[i][name],
            }
        )
    require(
        binding["schema_version"] == "swedish-landclim-author-parameter-binding.v1"
        and binding["author_target_count"] == 31
        and binding["covariance_nonzero_offdiagonal_cells"] == nonzero_offdiagonal == 0
        and binding["scientific_admission_allowed"] is False
        and [{k: r[k] for k in expected[0]} for r in binding["parameters"]] == expected,
        "Qualified full author parameter binding differs",
    )
    selected_names = protocol["taxa"]
    indices = [names.index(name) for name in selected_names]
    selected = {
        "taxa": deepcopy(selected_names),
        "alpha_text": [means[i]["alpha"] for i in indices],
        "fall_speed_m_s_text": [means[i]["vg"] for i in indices],
        "covariance_text": [
            [covariances[i][name] for name in selected_names] for i in indices
        ],
        "literal_file_line_numbers": [i + 2 for i in indices],
    }
    require(
        selected
        == {
            "taxa": protocol["parameters"]["targets"],
            **{k: protocol["parameters"][k] for k in selected if k != "taxa"},
        },
        "Selected author parameter source strings differ",
    )
    assignment = {r["oldvar"]: r["author_target"] for r in rows}
    return {
        "schema_version": "nordic-author-parameters.v1",
        "axis": names,
        "source_pins": deepcopy(protocol["author_sources"]),
        "lookup": {
            "rows": len(rows),
            "unique_source_names": len(assignment),
            "parameter_targets": len(expected_targets),
            "excluded_targets": deepcopy(
                protocol["author_lookup_contract"]["excluded_targets"]
            ),
        },
        "mean_rows": means,
        "covariance_rows": covariances,
        "selected": selected,
    }
