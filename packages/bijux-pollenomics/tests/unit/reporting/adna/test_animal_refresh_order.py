"""Animal refresh dependency order and publication-root ownership."""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from bijux_pollenomics.reporting.service import refresh_animal_adna_foundation


def test_animal_review_counts_follow_publication_at_the_requested_root(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    report_root = tmp_path / "publication"
    order = Mock()
    functions = (
        "refresh_source_library",
        "materialize_tracked_species_adna",
        "materialize_animal_publication_artifacts",
        "generate_published_reports",
        "_materialize_cross_species_adna_artifacts",
    )
    with ExitStack() as stack:
        for name in functions:
            mocked = stack.enter_context(
                patch(f"bijux_pollenomics.reporting.service.{name}")
            )
            order.attach_mock(mocked, name)
        stack.enter_context(
            patch(
                "bijux_pollenomics.reporting.service.build_tracked_animal_atlas_evidence_rows",
                return_value=(),
            )
        )
        stack.enter_context(
            patch(
                "bijux_pollenomics.reporting.service.build_project_registry",
                return_value=(),
            )
        )
        stack.enter_context(
            patch(
                "bijux_pollenomics.reporting.service.resolve_species_definition",
                return_value=SimpleNamespace(latin_name="Ovis aries"),
            )
        )
        refresh_animal_adna_foundation(
            data_root=data_root,
            aadr_root=data_root / "aadr",
            report_root=report_root,
            countries=("Sweden",),
            version="v66",
            species_names=("sheep",),
        )

    assert [entry[0] for entry in order.mock_calls] == list(functions)
    assert order.mock_calls[-1] == call._materialize_cross_species_adna_artifacts(
        data_root, report_root=report_root
    )
