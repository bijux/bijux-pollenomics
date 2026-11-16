"""Every source family must retain attempts only beneath its original directory."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.country_authority import (
    NeotomaCountryAuthorityPlan,
    capture_neotoma_country_authority,
)
from bijux_pollenomics.collection.sources.neotoma.capture.reference_tables import (
    NeotomaReferenceTablePlan,
    capture_neotoma_reference_tables,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    capture_neotoma_resources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.unit_resources import (
    capture_neotoma_unit_resources,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from ..resources.native_payloads import plan, response, spec
from ..unit_resources.test_capture import prepared


def capture_arguments(family: str, root: Path) -> tuple[Any, dict[str, Any]]:
    if family == "native":
        return capture_neotoma_resources, {"plan": plan(spec())}
    if family == "country":
        return capture_neotoma_country_authority, {
            "plan": NeotomaCountryAuthorityPlan(("Sweden",))
        }
    if family == "reference":
        return capture_neotoma_reference_tables, {
            "plan": NeotomaReferenceTablePlan(("variableunits",))
        }
    assert family == "unit"
    unit_plan, roster, metadata = prepared(root)
    return capture_neotoma_unit_resources, {
        "plan": unit_plan,
        "roster_path": roster,
        "metadata_captures": metadata,
    }


@pytest.mark.parametrize("family", ["native", "country", "reference", "unit"])
@pytest.mark.parametrize("replacement", ["symlink", "directory"])
@pytest.mark.parametrize("transport_failure", [False, True])
def test_source_attempts_do_not_write_into_a_replaced_root(
    tmp_path: Path, family: str, replacement: str, transport_failure: bool
) -> None:
    capture, kwargs = capture_arguments(family, tmp_path)
    output = tmp_path / "capture"
    staging = build_staging_output_dir(output)
    original = tmp_path / "original-owned-stage"
    foreign = tmp_path / "another-writer"
    foreign.mkdir()
    (foreign / "preserve").write_bytes(b"foreign evidence")

    def fetch(url: str, **_: object) -> Any:
        assert (staging / "request-plan.json").is_file()
        staging.rename(original)
        if replacement == "symlink":
            staging.symlink_to(foreign, target_is_directory=True)
        else:
            foreign.rename(staging)
        if transport_failure:
            raise TimeoutError("provider request failed after staging replacement")
        return response(url, b'{"status":"success","data":[]}')

    with pytest.raises((ValueError, OSError)):
        capture(output, fetch=fetch, **kwargs)

    foreign_root = foreign if replacement == "symlink" else staging
    assert sorted(path.name for path in foreign_root.iterdir()) == ["preserve"]
    assert (foreign_root / "preserve").read_bytes() == b"foreign evidence"
    assert sorted(path.name for path in original.iterdir()) == ["request-plan.json"]
    assert not output.exists()


def test_native_capture_replays_its_final_published_source_buffers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication import ownership

    from ..resources.native_payloads import body

    publish = vars(ownership)["publish_new_output_tree"]
    resource = spec()
    content = body(resource)
    output = tmp_path / "capture"

    def publish_then_corrupt(**kwargs: Any) -> None:
        publish(**kwargs)
        target = next(output.glob("*.body"))
        target.write_bytes(target.read_bytes() + b"\n")

    monkeypatch.setattr(ownership, "publish_new_output_tree", publish_then_corrupt)
    with pytest.raises(ValueError, match="identity|byte limit"):
        capture_neotoma_resources(
            output,
            plan=plan(resource),
            fetch=lambda url, **_: response(url, content),
        )
    assert output.is_dir()
    assert (output / "capture-manifest.json").is_file()


@pytest.mark.parametrize("family", ["native", "country", "reference", "unit"])
def test_equal_byte_published_capture_replacement_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, family: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication import ownership

    capture, kwargs = capture_arguments(family, tmp_path)
    output, saved = tmp_path / "capture", tmp_path / "owned-capture"
    if family == "native":
        from ..resources.native_payloads import body

        raw = body(kwargs["plan"].resources[0])
    else:
        raw = b'{"status":"success","data":[]}'
    publish = vars(ownership)["publish_new_output_tree"]

    def swapped(**publication: Any) -> None:
        publish(**publication)
        output.rename(saved)
        shutil.copytree(saved, output)

    monkeypatch.setattr(ownership, "publish_new_output_tree", swapped)
    with pytest.raises(ValueError, match="identity|inode"):
        capture(output, fetch=lambda url, **_: response(url, raw), **kwargs)
    assert (saved / "capture-manifest.json").read_bytes() == (
        output / "capture-manifest.json"
    ).read_bytes()
    assert saved.stat().st_ino != output.stat().st_ino
