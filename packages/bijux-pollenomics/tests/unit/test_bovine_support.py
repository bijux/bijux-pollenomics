from __future__ import annotations

from bijux_pollenomics.adna import build_bovine_support_program


def test_bovine_support_program_keeps_taurine_and_indicine_split() -> None:
    program = build_bovine_support_program()

    rows = {row.species_latin_name: row for row in program.species_rows}

    assert program.combined_claim_rule.combined_claim_allowed is False
    assert (
        "wild_or_progenitor_context_present"
        in program.combined_claim_rule.currently_blocked_by
    )
    assert rows["Bos taurus"].curated_core_project_count >= 1
    assert rows["Bos indicus"].curated_core_project_count == 0
    assert (
        "missing_species_specific_core_projects" in rows["Bos indicus"].blocking_reasons
    )
