"""Refit and forward every supplied training-only atom without outcome arguments."""

from __future__ import annotations

from fractions import Fraction
import json
from typing import Any

from ....lra.engine.errors import LRARefusal
from ....lra.uncertainty.contracts import NUMERICAL_REASONS
from ....lra.uncertainty.statistics import summaries
from ...contracts import (
    Fold,
    SiteRecord,
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from ...metrics import closed_composition
from ...prediction import ForwardModel
from ...splits import admit_training_groups, assert_training_inputs
from ..configuration import SiteCoordinate, SpatialConfig
from ..identifiability import spatial_identifiability
from ..model import fit_spatial_model
from .contracts import (
    CONDITIONED_SOURCES,
    UPSTREAM_SOURCES,
    JointSpatialDraw,
    UnavailableSpatialDraw,
    require,
    sha256,
)

NUMERICAL_REFUSALS = frozenset(
    {
        "invalid_composition",
        "unclosed_composition",
        "spatial_zero_composition_unsupported",
        "spatial_solver_failed",
        "spatial_solver_unresolved",
        "spatial_prediction_nonfinite",
        "spatial_prediction_underflow",
        "spatial_identifiability_unresolved",
        "forward_model_refused",
    }
)


def propagate_withheld_spatial_draws(
    fold: Fold,
    target_group_id: str,
    coordinate: SiteCoordinate,
    *,
    support_id: str,
    temporal_support_id: str,
    site_records: tuple[SiteRecord, ...],
    config: SpatialConfig,
    predictor_group_ids: tuple[str, ...],
    draw_ids: tuple[str, ...],
    draws: tuple[JointSpatialDraw | UnavailableSpatialDraw, ...],
    law_evidence_sha256: str,
    upstream_sources: tuple[str, ...],
    omitted_sources: tuple[str, ...],
    forward_model: ForwardModel,
) -> dict[str, Any]:
    """Push a supplied finite joint law through training refits and forward calls.

    The caller owns upstream evidence authentication and its joint scientific law.
    Atom IDs/masses and their paired contexts remain explicit; no draws or source
    distributions are generated here. Any refused mass suppresses unconditional
    moments. Counting-process draws require the separate observation workflow.
    """
    sha256(law_evidence_sha256)
    require(
        type(site_records) is tuple
        and bool(site_records)
        and all(isinstance(record, SiteRecord) for record in site_records),
        "Complete outcome-free physical-site/alias catalogue required",
    )
    # Reuse the maintained connected identity grouping. A caller cannot split a
    # target alias into training or turn a known target record into an external.
    admission = admit_training_groups(
        fold,
        site_records,
        fold.train_group_ids,
        criterion={"profile": "predeclared-whole-group-spatial-draws"},
    )
    require(
        type(draws) is tuple
        and 1 <= len(draws) <= 64
        and all(
            isinstance(draw, (JointSpatialDraw, UnavailableSpatialDraw))
            for draw in draws
        ),
        "Require 1–64 immutable coupled atoms",
    )
    require(
        type(draw_ids) is tuple
        and draw_ids == tuple(draw.draw_id for draw in draws)
        and len(set(draw_ids)) == len(draw_ids),
        "Frozen complete draw axis/order mismatch",
    )
    require(
        sum((draw.mass for draw in draws), Fraction()) == 1,
        "Exact complete joint mass must equal one",
    )
    require(
        type(upstream_sources) is tuple
        and bool(upstream_sources)
        and len(set(upstream_sources)) == len(upstream_sources),
        "Explicit unique upstream uncertainty declarations required",
    )
    require(
        type(omitted_sources) is tuple
        and len(set(omitted_sources)) == len(omitted_sources),
        "Explicit unique omissions required",
    )
    require(
        set(upstream_sources) <= UPSTREAM_SOURCES
        and not set(upstream_sources) & set(omitted_sources)
        and set(upstream_sources) | set(omitted_sources)
        == UPSTREAM_SOURCES | CONDITIONED_SOURCES,
        "Declare every uncertainty source without unsupported propagation",
    )
    require(
        set(CONDITIONED_SOURCES) <= set(omitted_sources),
        "No residual, counting, selection or target-coordinate law is implemented",
    )
    require(
        type(predictor_group_ids) is tuple
        and predictor_group_ids == tuple(sorted(set(predictor_group_ids)))
        and 2 <= len(predictor_group_ids) <= 128
        and set(predictor_group_ids) <= set(fold.train_group_ids),
        "Exact predefined training predictor population required",
    )
    require(
        target_group_id in fold.test_group_ids and support_id == config.support_id,
        "Withheld target and predefined support required",
    )
    from ...contracts import required_identity

    required_identity(temporal_support_id)
    available = tuple(draw for draw in draws if isinstance(draw, JointSpatialDraw))
    taxa = available[0].forward.taxa if available else ()
    ring_count = len(available[0].forward.local_k) if available else 0
    if available:
        require(2 <= len(taxa) <= 128, "Bounded exact taxon population required")
        require(1 <= ring_count <= 128, "Bounded forward ring population required")
    # Validate every atom and its complete ancestry before the first fit/callback.
    component_values: dict[tuple[str, tuple[str, ...]], str] = {}
    for draw in draws:
        graph = dict(draw.input_lineage)
        closure = assert_training_inputs(
            fold,
            draw.input_ids,
            graph,
            admitted_external_ids=draw.admitted_external_ids,
            training_admission=admission,
        )
        require(
            set(admission.admitted_record_ids) <= set(closure),
            "Incomplete outer training ancestry",
        )
        actual_time = (
            draw.forward.temporal_support_id
            if isinstance(draw, JointSpatialDraw)
            else draw.temporal_support_id
        )
        require(
            actual_time == temporal_support_id,
            "All atoms must address the same fixed target temporal support",
        )
        assert_training_inputs(
            fold,
            (*draw.input_ids, temporal_support_id),
            graph,
            admitted_external_ids=draw.admitted_external_ids,
            training_admission=admission,
        )
        if isinstance(draw, UnavailableSpatialDraw):
            continue
        for role, ids, values in (
            ("parameters", draw.forward.parameter_input_ids, draw.forward.ppe),
            (
                "regional",
                draw.forward.regional_input_ids,
                draw.forward.regional_deposition,
            ),
            (
                "geometry",
                draw.forward.geometry_input_ids,
                (draw.forward.local_k, draw.forward.terrestrial_fraction),
            ),
        ):
            checksum = manifest_sha256(values)
            require(
                component_values.setdefault((role, ids), checksum) == checksum,
                "A reused forward component identity has contradictory values",
            )
        require(
            tuple(key for key, _ in draw.compositions) == predictor_group_ids
            and tuple(key for key, _ in draw.coordinates) == predictor_group_ids,
            "Training composition/coordinate axes differ",
        )
        context = draw.forward
        require(
            context.method_profile == available[0].forward.method_profile
            and context.engine_build_id == available[0].forward.engine_build_id,
            "Fixed forward profile and engine build required",
        )
        require(
            context.taxa == taxa
            and len(context.local_k) == ring_count
            and all(len(row) == len(taxa) for row in context.local_k)
            and len(context.regional_deposition) == len(context.ppe) == len(taxa)
            and len(context.terrestrial_fraction) == ring_count,
            "Paired forward draw axes differ",
        )
        require(
            all(value >= 0 for row in context.local_k for value in row)
            and all(value >= 0 for value in context.regional_deposition)
            and all(value > 0 for value in context.ppe)
            and all(0 <= value <= 1 for value in context.terrestrial_fraction),
            "Forward numerical domains differ",
        )
        for _, composition in draw.compositions:
            closed_composition(dict(composition))
        assert_training_inputs(
            fold,
            (
                *draw.input_ids,
                *context.regional_input_ids,
                *context.parameter_input_ids,
                *context.geometry_input_ids,
                context.temporal_support_id,
            ),
            graph,
            admitted_external_ids=draw.admitted_external_ids,
            training_admission=admission,
        )
    rows = []
    coordinates = [
        {"role": role, "taxon": taxon, "unit": "fraction"}
        for role in ("vegetation", "pollen")
        for taxon in taxa
    ]
    for draw in draws:
        row: dict[str, Any] = {
            "draw_id": draw.draw_id,
            "bin_id": temporal_support_id,
            "mass": {
                "numerator": draw.mass.numerator,
                "denominator": draw.mass.denominator,
            },
            "atom_sha256": draw.sha256,
            "source_evidence_sha256": draw.source_evidence_sha256,
            "spatial_fit_attempted": False,
            "forward_attempted": False,
        }
        if isinstance(draw, UnavailableSpatialDraw):
            upstream = json.loads(draw.source_row_json)
            row.update(
                status=upstream["status"],
                reason_code=upstream["reason_code"],
                refusal_stage="upstream",
                upstream=draw.as_dict(),
            )
            rows.append(row)
            continue
        row["forward_inputs"] = draw.forward.as_dict()
        try:
            row["spatial_fit_attempted"] = True
            model = fit_spatial_model(
                fold,
                {key: dict(value) for key, value in draw.compositions},
                dict(draw.coordinates),
                config=config,
                input_ids=draw.input_ids,
                dependency_graph=dict(draw.input_lineage),
                admitted_external_ids=draw.admitted_external_ids,
                predictor_group_ids=predictor_group_ids,
                training_admission=admission,
            )
            prediction = model.predict(
                target_group_id=target_group_id,
                coordinate=coordinate,
                support_id=support_id,
            )
            vegetation = dict(prediction.fractions)
            context = draw.forward
            row["forward_attempted"] = True
            result = forward_model(
                tuple(vegetation[taxon] for taxon in taxa),
                context.regional_deposition,
                context.local_k,
                context.terrestrial_fraction,
                context.ppe,
            )
            if result.method_profile != context.method_profile:
                raise ValidationRefusal(
                    "forward_profile_mismatch", "Actual operator profile differs"
                )
            pollen_values = tuple(result.pollen_fraction)
            require(
                len(pollen_values) == len(taxa), "Forward output taxon axis differs"
            )
            pollen = closed_composition(dict(zip(taxa, pollen_values, strict=True)))
            row.update(
                status="success",
                model_sha256=model.model_sha256,
                prediction_sha256=prediction.prediction_sha256,
                identifiability=spatial_identifiability(
                    model,
                    target_group_id=target_group_id,
                    coordinate=coordinate,
                    support_id=support_id,
                ),
                coordinates=coordinates,
                values=[
                    *(vegetation[taxon] for taxon in taxa),
                    *(pollen[taxon] for taxon in taxa),
                ],
            )
        except LRARefusal as exc:
            if exc.reason_code not in NUMERICAL_REASONS:
                raise
            row.update(
                status="refused",
                reason_code=exc.reason_code,
                detail=str(exc),
                error=exc.as_dict(),
            )
        except ValidationRefusal as exc:
            if exc.reason_code not in NUMERICAL_REFUSALS:
                raise
            row.update(status="refused", reason_code=exc.reason_code, detail=str(exc))
        rows.append(row)
    payload: dict[str, Any] = {
        "schema_version": "lra-withheld-spatial-joint-uncertainty.v1",
        "fold": fold.as_dict(),
        "training_admission": admission.as_dict(),
        "site_records": [
            {
                "record_id": record.record_id,
                "site_id": record.site_id,
                "identity_keys": record.identity_keys,
                "block_id": record.block_id,
            }
            for record in site_records
        ],
        "target_group_id": target_group_id,
        "temporal_support_id": temporal_support_id,
        "target_coordinate": coordinate.as_dict(),
        "configuration": config.as_dict(),
        "draw_ids": draw_ids,
        "law_evidence_sha256": law_evidence_sha256,
        "rows": rows,
        "summary": summaries(rows, [temporal_support_id])[temporal_support_id],
        "propagated_sources": [
            "supplied_training_and_forward_joint_atoms",
            "train_only_spatial_refitting",
        ],
        "upstream_declared_sources": upstream_sources,
        "omitted_sources": omitted_sources,
        "law_authenticity_verified": False,
        "uncertainty_kind": "supplied_finite_law_pushforward",
        "empirical_coverage_verified": False,
        "outcome_accesses": [],
        "scientific_acceptance": "not_evaluated",
    }
    encoded = canonical_json(payload)
    return {
        **payload,
        "result_sha256": manifest_sha256(payload),
        "canonical_result_json": encoded,
    }
