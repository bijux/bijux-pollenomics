"""Hash-bound primary-source contract for the PRJEB31621 cattle panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


ARCHIVE_GZIP_SHA256: Final = (
    "6f958dbaf61775f20e5acf59fe3a3616ab6ec3ef9ac9b8399a00e1e9e82a6487"
)
ARCHIVE_TEXT_SHA256: Final = (
    "3fa7867b615e14cb5333e8c70d8df3329084a932ebd29d65fd00502d95781ced"
)
FERTILE_CRESCENT_CATTLE_SUPPLEMENT_SHA256: Final = (
    "bc076874345613dc71269f66db8b4941589d3be1eacae90043f3d94618b5e56c"
)


@dataclass(frozen=True)
class CattleSiteEvidence:
    """One numbered archaeological-context section and its ancient individuals."""

    section_number: int
    pdf_page: int
    source_heading: str
    locality_text: str
    political_entity: str
    sample_ids: tuple[str, ...]

    @property
    def locator(self) -> str:
        """Return a stable human-readable locator into the governed PDF."""
        return (
            f"Archaeological sites and context section {self.section_number} "
            f'"{self.source_heading}" (PDF page {self.pdf_page})'
        )


SITE_EVIDENCE: Final = (
    CattleSiteEvidence(
        1, 2, "Abu Gosh, Israel", "Abu Gosh", "Israel", ("Abu1", "Abu2")
    ),
    CattleSiteEvidence(2, 2, "Acemhöyük, Turkey", "Acemhöyük", "Turkey", ("Ace1",)),
    CattleSiteEvidence(
        3,
        3,
        "Belovode-Veliko Laole, Serbia",
        "Belovode-Veliko Laole",
        "Serbia",
        ("Bel1", "Bel2"),
    ),
    CattleSiteEvidence(4, 3, "Bestansur, Iraq", "Bestansur", "Iraq", ("Bes1", "Bes2")),
    CattleSiteEvidence(
        5, 4, "Blagotin, Serbia", "Blagotin", "Serbia", ("Bla1", "Bla2")
    ),
    CattleSiteEvidence(6, 5, "Bubanj, Serbia", "Bubanj", "Serbia", ("Bub1",)),
    CattleSiteEvidence(7, 5, "Çatalhöyük, Turkey", "Çatalhöyük", "Turkey", ("Ch22",)),
    CattleSiteEvidence(
        8,
        6,
        "Dariali Tamara Fort, Georgia",
        "Dariali Tamara Fort",
        "Georgia",
        ("Kaz1", "Kaz2", "Kaz3", "Kaz4", "Kaz5"),
    ),
    CattleSiteEvidence(9, 6, "Gilat, Israel", "Gilat", "Israel", ("Gil1",)),
    CattleSiteEvidence(10, 7, "Gyumri, Armenia", "Gyumri", "Armenia", ("Gyu2",)),
    CattleSiteEvidence(
        11,
        7,
        "Hasanlu, Iran",
        "Hasanlu",
        "Iran",
        ("Has1", "Has3", "Has4", "Has5"),
    ),
    CattleSiteEvidence(
        12, 8, "Horvat Castra, Israel", "Horvat Castra", "Israel", ("Cas1",)
    ),
    CattleSiteEvidence(
        13, 8, "Koktepe, Uzbekistan", "Koktepe", "Uzbekistan", ("Kok1",)
    ),
    CattleSiteEvidence(
        14,
        9,
        "Kul Tepe, Azerbaijan, Iran",
        "Kul Tepe, Azerbaijan",
        "Iran",
        ("Azer1",),
    ),
    CattleSiteEvidence(15, 9, "Maral Tappeh, Iran", "Maral Tappeh", "Iran", ("Mar1",)),
    CattleSiteEvidence(
        16, 10, "Menteşe, Turkey", "Menteşe", "Turkey", ("Men1", "Men2")
    ),
    CattleSiteEvidence(
        17,
        10,
        "Mianroud, Fars, Iran",
        "Mianroud, Fars",
        "Iran",
        ("Far1",),
    ),
    CattleSiteEvidence(
        18,
        11,
        "Monjukli Depe, Turkmenistan",
        "Monjukli Depe",
        "Turkmenistan",
        ("Mon1",),
    ),
    CattleSiteEvidence(
        19, 11, "Nahal Tillah, Israel", "Nahal Tillah", "Israel", ("Nah1",)
    ),
    CattleSiteEvidence(
        20,
        12,
        "Nishapur Kohandež, Central Khorasan, Iran",
        "Nishapur Kohandež, Central Khorasan",
        "Iran",
        ("Kho1",),
    ),
    CattleSiteEvidence(
        21,
        12,
        "Pločnik, Serbia",
        "Pločnik",
        "Serbia",
        tuple(f"Plo{number}" for number in range(1, 9)),
    ),
    CattleSiteEvidence(
        22,
        13,
        "Promachon, Serres, Greece",
        "Promachon, Serres",
        "Greece",
        ("Pro1",),
    ),
    CattleSiteEvidence(
        23,
        14,
        "Sarakenos Cave, Boeotia, Greece",
        "Sarakenos Cave, Boeotia",
        "Greece",
        ("Sar38",),
    ),
    CattleSiteEvidence(24, 14, "Stubline, Serbia", "Stubline", "Serbia", ("Stu1",)),
    CattleSiteEvidence(
        25,
        15,
        "Suberde and Erbaba, Turkey",
        "Suberde and Erbaba",
        "Turkey",
        ("Sub1",),
    ),
    CattleSiteEvidence(
        26,
        16,
        "Taghit Haddouch, Morroco",
        "Taghit Haddouch",
        "Morocco",
        ("Th7",),
    ),
    CattleSiteEvidence(
        27,
        17,
        "Tappeh-Sang-e-Chakhmaq, Iran",
        "Tappeh-Sang-e-Chakhmaq",
        "Iran",
        ("Sac3",),
    ),
    CattleSiteEvidence(
        28, 17, "Tel Ashqelon, Israel", "Tel Ashqelon", "Israel", ("Ash4",)
    ),
    CattleSiteEvidence(29, 18, "Tel Dan, Israel", "Tel Dan", "Israel", ("Dan1",)),
    CattleSiteEvidence(
        30,
        18,
        "Tel es-Qashish, Israel",
        "Tel es-Qashish",
        "Israel",
        ("Tqa1", "Tqa2", "Tqa3"),
    ),
    CattleSiteEvidence(
        31,
        19,
        "Tel es-Safi, Israel",
        "Tel es-Safi",
        "Israel",
        ("Tsa1", "Tsa2", "Tsa3"),
    ),
    CattleSiteEvidence(32, 19, "Tel-Hreiz, Israel", "Tel-Hreiz", "Israel", ("Thr1",)),
    CattleSiteEvidence(33, 20, "Tel Masos, Israel", "Tel Masos", "Israel", ("Mas1",)),
    CattleSiteEvidence(
        34,
        20,
        "Tel Miqne-Ekron, Israel",
        "Tel Miqne-Ekron",
        "Israel",
        ("Tmq1", "Tmq2", "Tmq3", "Tmq4"),
    ),
    CattleSiteEvidence(
        35, 20, "Tel Yoqneam, Israel", "Tel Yoqneam", "Israel", ("Tyq1",)
    ),
    CattleSiteEvidence(36, 21, "Tel Zahara, Israel", "Tel Zahara", "Israel", ("Zah1",)),
    CattleSiteEvidence(37, 21, "Tel-Dalit, Israel", "Tel-Dalit", "Israel", ("Tda1",)),
    CattleSiteEvidence(
        38,
        22,
        "Tepe Shizar, Qazvin, Iran",
        "Tepe Shizar, Qazvin",
        "Iran",
        ("Qaz1",),
    ),
    CattleSiteEvidence(
        39, 22, "Tilla Bulak, Uzbekistan", "Tilla Bulak", "Uzbekistan", ("Bul1",)
    ),
    CattleSiteEvidence(
        40,
        23,
        "Yerqurqan  (Erkurgan), Uzbekistan:",
        "Yerqurqan (Erkurgan)",
        "Uzbekistan",
        ("Yer1",),
    ),
)


APPROXIMATE_BP_BY_SAMPLE: Final = {
    "Ace1": 4200,
    "Ash4": 3100,
    "Azer1": 6100,
    "Bel1": 6900,
    "Bel2": 6900,
    "Bes1": 2800,
    "Bes2": 629,
    "Bla1": 8100,
    "Bla2": 8100,
    "Bub1": 7600,
    "Bul1": 3800,
    "Cas1": 1400,
    "Ch22": 7600,
    "Far1": 7700,
    "Gyu2": 7040,
    "Has1": 3700,
    "Has3": 4470,
    "Has4": 2900,
    "Has5": 2300,
    "Kaz1": 1000,
    "Kaz2": 1050,
    "Kaz3": 1350,
    "Kaz4": 1200,
    "Kaz5": 1290,
    "Kho1": 1400,
    "Kok1": 3500,
    "Mar1": 6150,
    "Mas1": 3100,
    "Men1": 8050,
    "Men2": 7920,
    "Mon1": 7200,
    "Plo1": 7125,
    "Plo2": 6950,
    "Plo3": 7025,
    "Plo4": 7000,
    "Plo5": 6650,
    "Plo6": 7126,
    "Plo7": 7000,
    "Plo8": 7001,
    "Qaz1": 4760,
    "Sac3": 7373,
    "Stu1": 6600,
    "Tda1": 5050,
    "Th7": 7993,
    "Thr1": 6700,
    "Tmq1": 3150,
    "Tmq2": 3150,
    "Tmq3": 2925,
    "Tmq4": 3300,
    "Tqa1": 4800,
    "Tqa2": 4800,
    "Tqa3": 4800,
    "Tsa1": 2820,
    "Tsa2": 3100,
    "Tsa3": 2800,
    "Tyq1": 2200,
    "Yer1": 2050,
    "Zah1": 1850,
}


SOURCE_INTERVAL_BY_SAMPLE: Final = {
    "Abu1": "7500-6000 BCE",
    "Abu2": "7500-6000 BCE",
    "Dan1": "3500-3000 BC",
    "Gil1": "c.4300–3300 BC",
    "Nah1": "3300-3050 BC",
    "Pro1": "5320-5070 Cal. BC",
    "Sar38": "5750-5600 BC",
    "Sub1": (
        "6020-6140 cal BC in the section narrative; "
        "6221-6024 cal. BC in the section table"
    ),
}


CANONICAL_BP_INTERVAL_BY_SAMPLE: Final = {
    "Abu1": (7949, 9449),
    "Abu2": (7949, 9449),
    "Dan1": (4949, 5449),
    "Gil1": (5249, 6249),
    "Nah1": (4999, 5249),
    "Pro1": (7019, 7269),
    "Sar38": (7549, 7699),
}


CHRONOLOGY_CONFLICT_BY_SAMPLE: Final = {
    "Sub1": (
        "The primary supplement gives two non-identical calibrated intervals and "
        "retains Suberde-versus-Erbaba curation history; numeric chronology and an "
        "exact single-site claim must remain withheld."
    )
}


EXPLICIT_ARCHIVE_ALIASES: Final = {
    "Bes1": ("SAMEA5577351", ("Bes1A_", "Bes1B_")),
    "Bes2": ("SAMEA5577352", ("Bes2A_", "Bes2B_")),
    "Gyu2": ("SAMEA5577362", ("Gyu2A_", "Gyu2B_")),
    "Men2": ("SAMEA5577377", ("Men2A_", "Men2B_")),
    "Sub1": (
        "SAMEA5577393",
        ("Sub1A_", "Sub1B_", "Sub1C_", "Sub1D_", "Sub1F_", "Sub1G_", "Sub1H_"),
    ),
}


ARCHIVE_ONLY_IDENTITIES: Final = {
    "SAMEA5577008": ("9913", "Bos taurus", "Sik_5_"),
    "SAMEA5577009": ("9913", "Bos taurus", "Lag_40_"),
    "SAMEA5577010": ("9915", "Bos indicus", "Thar_1_"),
    "SAMEA5577011": ("9915", "Bos indicus", "Sha_3b_"),
    "SAMEA5577012": ("9913", "Bos taurus", "Wag_1a_"),
    "SAMEA5577149": ("9915", "Bos indicus", "Har03b_"),
    "SAMEA5577150": ("9913", "Bos taurus", "High2_"),
    "SAMEA5577151": ("9913", "Bos taurus", "Somba2_"),
    "SAMEA5577153": ("9913", "Bos taurus", "Alent1_"),
    "SAMEA5577154": ("9904", "Bos gaurus", "Ga5_"),
    "SAMEA5577376": ("9913", "Bos taurus", "MV013A_"),
    "SAMEA5605818": ("9913", "Bos taurus", "SAR1."),
}


DARIALI_SOURCE_COORDINATE: Final = "UTM 38N 469400, 4731800; datum not stated"


__all__ = [
    "APPROXIMATE_BP_BY_SAMPLE",
    "ARCHIVE_ONLY_IDENTITIES",
    "ARCHIVE_GZIP_SHA256",
    "ARCHIVE_TEXT_SHA256",
    "CANONICAL_BP_INTERVAL_BY_SAMPLE",
    "CHRONOLOGY_CONFLICT_BY_SAMPLE",
    "CattleSiteEvidence",
    "DARIALI_SOURCE_COORDINATE",
    "EXPLICIT_ARCHIVE_ALIASES",
    "SITE_EVIDENCE",
    "SOURCE_INTERVAL_BY_SAMPLE",
    "FERTILE_CRESCENT_CATTLE_SUPPLEMENT_SHA256",
]
