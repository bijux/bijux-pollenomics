"""Place hierarchy resolution backed by tracked archaeological evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess  # nosec B404

_SINGLE_COUNTRY_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]+$")


@dataclass(frozen=True)
class _Hierarchy:
    site_name: str
    municipality_name: str
    region_name: str
    country_name: str
    broader_geography: str


def _project_hierarchy_profiles(
    output_root: Path,
    project_accession: str,
) -> dict[str, _Hierarchy]:
    if project_accession != "PRJEB36540":
        return {}
    text = _ghostscript_text(
        output_root
        / "adna"
        / "governance"
        / "source_library"
        / "papers"
        / "10.1038-s42003-021-02794-8"
        / "supplementary"
        / "42003_2021_2794_MOESM2_ESM.pdf"
    )
    if not text:
        return {}
    profiles = {
        "Ulucak Höyük": _Hierarchy(
            site_name="Ulucak Höyük",
            municipality_name="Izmir area",
            region_name="West Central Turkey",
            country_name="Turkey",
            broader_geography="Western Anatolia",
        ),
        "Barcın Höyük": _Hierarchy(
            site_name="Barcın Höyük",
            municipality_name="Yenişehir Plain",
            region_name="Bursa Province",
            country_name="Turkey",
            broader_geography="Northwestern Anatolia",
        ),
        "Tepecik-Çiftlik Höyük": _Hierarchy(
            site_name="Tepecik-Çiftlik Höyük",
            municipality_name="Çiftlik district",
            region_name="Niğde Province",
            country_name="Turkey",
            broader_geography="Central Anatolian Plateau",
        ),
        "Tepecik-Çiftlik": _Hierarchy(
            site_name="Tepecik-Çiftlik Höyük",
            municipality_name="Çiftlik district",
            region_name="Niğde Province",
            country_name="Turkey",
            broader_geography="Central Anatolian Plateau",
        ),
        "Barcın": _Hierarchy(
            site_name="Barcın Höyük",
            municipality_name="Yenişehir Plain",
            region_name="Bursa Province",
            country_name="Turkey",
            broader_geography="Northwestern Anatolia",
        ),
    }
    if "Barcın Höyük, a seventh millennium Neolithic site" not in text:
        profiles.pop("Barcın Höyük", None)
        profiles.pop("Barcın", None)
    if "Ulucak Höyük, lies 25 km east of İzmir" not in text:
        profiles.pop("Ulucak Höyük", None)
    if (
        "Tepecik-Çiftlik mound is located in the Çiftlik district of Niğde province"
        not in text
    ):
        profiles.pop("Tepecik-Çiftlik Höyük", None)
        profiles.pop("Tepecik-Çiftlik", None)
    return profiles


def _resolve_hierarchy(
    *,
    hierarchy_profiles: dict[str, _Hierarchy],
    locality_text: str,
    political_entity: str,
) -> _Hierarchy:
    if locality_text in hierarchy_profiles:
        return hierarchy_profiles[locality_text]
    if (
        locality_text.endswith(" context")
        and locality_text.removesuffix(" context") in hierarchy_profiles
    ):
        return hierarchy_profiles[locality_text.removesuffix(" context")]
    country_name = (
        political_entity if _SINGLE_COUNTRY_RE.fullmatch(political_entity or "") else ""
    )
    broader_geography = ""
    if political_entity and not country_name:
        broader_geography = political_entity
    elif locality_text and not country_name:
        broader_geography = locality_text
    return _Hierarchy(
        site_name=locality_text,
        municipality_name="",
        region_name="",
        country_name=country_name,
        broader_geography=broader_geography,
    )


def _ghostscript_text(path: Path) -> str:
    if not path.is_file():
        return ""
    gs = shutil.which("gs")
    if gs is None:
        return ""
    pdf_path = path.resolve()
    # Ghostscript is invoked without a shell against one checked-in local PDF path.
    result = subprocess.run(
        [
            gs,
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            "-sOutputFile=-",
            str(pdf_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )  # nosec B603
    if result.returncode != 0:
        return ""
    return result.stdout
