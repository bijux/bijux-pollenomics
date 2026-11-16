"""Cleanup notes have less authority than the failure already being unwound."""

import pytest

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note


def test_useful_cleanup_note_appends_without_replacing_user_notes() -> None:
    primary = OSError("primary")
    primary.add_note("existing user diagnostic")
    notes = primary.__notes__
    add_cleanup_note(primary, lambda: "secondary resource close failed")
    assert primary.__notes__ is notes
    assert notes == ["existing user diagnostic", "secondary resource close failed"]


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_diagnostic_builder_failure_cannot_replace_active_primary(
    failure: type[BaseException],
) -> None:
    primary = OSError("primary")
    primary.add_note("existing user diagnostic")

    def note() -> str:
        raise failure("diagnostic failure")

    add_cleanup_note(primary, note)
    assert primary.__notes__ == ["existing user diagnostic"]


def test_invalid_existing_notes_are_preserved_without_coercion() -> None:
    primary = OSError("primary")
    foreign = ("existing user diagnostic",)
    primary.__notes__ = foreign  # type: ignore[assignment]
    add_cleanup_note(primary, lambda: "secondary diagnostic")
    assert vars(primary)["__notes__"] is foreign


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_custom_note_failure_does_not_escape_or_overwrite_notes(
    failure: type[BaseException],
) -> None:
    class Primary(OSError):
        def add_note(self, note: str) -> None:
            raise failure("custom note failure")

    primary = Primary("primary")
    foreign = ["existing user diagnostic"]
    primary.__notes__ = foreign
    add_cleanup_note(primary, lambda: "secondary diagnostic")
    assert primary.__notes__ is foreign and foreign == ["existing user diagnostic"]
