"""Keep complete-cohort diagnostics distinct from source-seed location selection."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict

from .numerical import ORDER, matrix
from .source import PollenSample, number


class ClassRecord(TypedDict):
    """Describe only the classes needed for dominant agreement and filtering."""

    prediction: str
    dominant: str


class AgreementRecord(ClassRecord):
    """Add the reference alternative needed for composite agreement."""

    subdominant: str


class EntityRecord(AgreementRecord):
    """Retain native sample membership with independently selected modal classes."""

    entity_name: str
    sample_ids: list[str]


def entities(
    samples: dict[str, PollenSample],
    labels: dict[str, dict[str, str]],
    predictions: dict[str, str],
    selected: set[str],
) -> list[EntityRecord]:
    """Group eligible samples by opaque entity tokens and independent modes."""
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for sid in sorted(selected):
        row = samples[sid]
        lat, lon = (
            number(row["metadata"]["latitude"]),
            number(row["metadata"]["longitude"]),
        )
        if (
            sid not in labels
            or labels[sid]["Dominant"] not in ORDER
            or not (-90 <= lat <= 90 and -180 <= lon <= 180)
        ):
            continue
        groups[row["metadata"]["entity_name"]].append(
            {
                "sample_id": sid,
                "prediction": predictions[sid],
                "dominant": labels[sid]["Dominant"],
                "subdominant": labels[sid]["Subdominant"],
            }
        )
    result: list[EntityRecord] = []
    for name, group in sorted(groups.items()):

        def mode(field: str, *, row_group: list[dict[str, str]] = group) -> str:
            counts = Counter(r[field] for r in row_group)
            return min(counts, key=lambda value: (-counts[value], value))

        result.append(
            {
                "entity_name": name,
                "sample_ids": [r["sample_id"] for r in group],
                "prediction": mode("prediction"),
                "dominant": mode("dominant"),
                "subdominant": mode("subdominant"),
            }
        )
    return result


def rates(rows: Sequence[AgreementRecord]) -> dict[str, object]:
    """Count dominant and composite agreement against the retained row population."""
    denominator = len(rows)
    dominant = sum(r["prediction"] == r["dominant"] for r in rows)
    composite = sum(r["prediction"] in (r["dominant"], r["subdominant"]) for r in rows)
    return {
        "denominator": denominator,
        "dominant_correct": dominant,
        "composite_correct": composite,
        "dominant_agreement": dominant / denominator if denominator else None,
        "composite_agreement": composite / denominator if denominator else None,
    }


def profiles(
    samples: dict[str, PollenSample],
    labels: dict[str, dict[str, str]],
    predictions: dict[str, str],
) -> dict[str, object]:
    """Keep coordinate selections and filtered denominators separate."""
    coordinates = {
        sid: (number(r["metadata"]["latitude"]), number(r["metadata"]["longitude"]))
        for sid, r in samples.items()
    }
    selections = {
        "complete_curated_cohort": set(samples),
        "emb_complete_declared_coordinate_window": {
            s
            for s, (lat, lon) in coordinates.items()
            if 28 < lat < 49.25 and 20 < lon < 62
        },
        "northern_europe_coordinate_screen": {
            s
            for s, (lat, lon) in coordinates.items()
            if 54 <= lat <= 72 and -25 <= lon <= 32
        },
    }
    result: dict[str, object] = {}
    for name, selection in selections.items():
        rows = entities(samples, labels, predictions, selection)
        eligible_samples = sum(len(r["sample_ids"]) for r in rows)
        filtered = [
            r
            for r in rows
            if r["prediction"] not in ("TUND", "CENF")
            and r["dominant"] not in ("TUND", "CENF")
        ]
        result[name] = {
            "source_samples": len(selection),
            "eligible_label_samples": eligible_samples,
            "excluded_samples": len(selection) - eligible_samples,
            "all_entity_classes": rates(rows),
            "source_metrics_TUND_CENF_exclusion": rates(filtered),
            "TUND_CENF_excluded_entities": len(rows) - len(filtered),
            "modal_tie_rule": "lexicographically first class after counts; source entity names are opaque byte tokens",
            "independent_field_accuracy": False,
        }
    return result


def original_matrices(
    directory: Path, rows: list[EntityRecord]
) -> dict[str, dict[str, object]]:
    """Compare every reconstructed cell with the saved source matrix."""
    import csv

    result: dict[str, dict[str, object]] = {}
    for kind in ("Dominant", "Composit", "Subdominant"):
        current = matrix(
            [
                {
                    "prediction": row["prediction"],
                    "dominant": row["dominant"],
                    "subdominant": row["subdominant"],
                }
                for row in rows
            ],
            kind,
        )
        with (directory / f"EC4c_f_ep0.5_EMB_{kind}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            reader = csv.reader(stream)
            columns = next(reader)[1:]
            original = {
                (row[0], col): int(value)
                for row in reader
                for col, value in zip(columns, row[1:], strict=True)
            }
        differences = [
            {
                "reference_row": ref,
                "prediction_column": pred,
                "original": original.get((ref, pred), 0),
                "reconstructed": current.get((ref, pred), 0),
            }
            for ref, pred in sorted(set(original) | set(current))
            if original.get((ref, pred), 0) != current.get((ref, pred), 0)
        ]
        total = sum(current.values())
        trace = sum(n for (ref, pred), n in current.items() if ref == pred)
        result[kind] = {
            "original_total": sum(original.values()),
            "reconstructed_total": total,
            "reconstructed_trace": trace,
            "trace_fraction": trace / total if total else None,
            "orientation": "reference rows/prediction columns: MLmetrics table(y_true,y_pred)",
            "all_cells_exact": not differences,
            "cell_differences": differences,
        }
    return result
