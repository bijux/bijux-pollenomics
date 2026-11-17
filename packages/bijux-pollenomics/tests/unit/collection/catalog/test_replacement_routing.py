"""Catalog replacement modes match generated workflow callback ownership."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.collection.catalog.replacement import (
    build_source_replacement_rules,
)
from bijux_pollenomics.collection.workflow.context_collection import (
    collect_context_source,
)
from bijux_pollenomics.collection.workflow.planning.source_registry import (
    CONTEXT_SOURCE_SPECS,
)


@pytest.mark.parametrize("source", list(CONTEXT_SOURCE_SPECS))
def test_context_counts_and_relative_members_match_publication_policy(
    tmp_path: Path, source: str
) -> None:
    spec = CONTEXT_SOURCE_SPECS[source]
    final = tmp_path / spec.output_dir_name
    foreign = tmp_path / ("." + spec.output_dir_name + ".staging")
    foreign.mkdir()
    (foreign / "foreign.txt").write_text("PRESERVE")
    observed: list[Path] = []
    report = SimpleNamespace(**{field: 7 for _, field in spec.count_attributes})

    def collector(*, output_root: Path, **_: object) -> object:
        observed.append(output_root)
        (output_root / "raw").mkdir(parents=True)
        (output_root / "raw/generated.json").write_text('{"generated": true}')
        return report

    counts = collect_context_source(
        collect_function=collector,
        spec=spec,
        output_root=tmp_path,
        country_boundaries={},
    )
    assert counts == {field: 7 for field, _ in spec.count_attributes}
    assert (final / "raw/generated.json").read_text() == '{"generated": true}'
    assert (foreign / "foreign.txt").read_text() == "PRESERVE"
    rule = build_source_replacement_rules(
        selected_sources=(source,), source_output_roots={source: str(final)}
    )[source]
    if spec.owns_output_publication:
        assert observed == [final]
        assert rule.refresh_mode == "staging_swap"
        assert rule.staging_output_root == str(foreign)
    else:
        assert len(observed) == 1 and observed[0] != final
        assert observed[0] != foreign
        assert rule.refresh_mode == "owned_callback_replacement"
        assert rule.staging_output_root is None


def test_compatibility_facade_reuses_the_same_callback_owner(tmp_path: Path) -> None:
    from bijux_pollenomics.collection import SourceReplacementRule
    from bijux_pollenomics.collection.workflow.materialization.staging import (
        collect_into_staging_dir,
    )

    alias = import_module("pollenomics.collection.workflow.materialization.staging")
    public = import_module("pollenomics.collection")
    assert alias.collect_into_staging_dir is collect_into_staging_dir
    assert public.SourceReplacementRule is SourceReplacementRule
    result = {"generated_count": 1}

    def collect(root: Path) -> object:
        (root / "generated.txt").write_text("GENERATED")
        return result

    final = tmp_path / "facade-output"
    assert alias.collect_into_staging_dir(final, collect) is result
    assert (final / "generated.txt").read_text() == "GENERATED"
