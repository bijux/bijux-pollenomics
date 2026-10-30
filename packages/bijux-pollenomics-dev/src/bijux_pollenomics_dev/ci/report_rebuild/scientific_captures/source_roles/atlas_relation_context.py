"""Bind declared relation context and producer inventories to fixed old sources."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule
from ..presentation_source_roles import atlas_extension_matches
from .documentation import DOCUMENTED_SOURCE_STRINGS, _documented_source_matches

_RELATION_CONTEXT_CONTRACTS: dict[
    str, tuple[int, str, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py": (
        8379,
        "220ba4fbc8e3f884408b6b7bec47d6e70b021a1fe3f4d517c259dabf8681b834",
        "existing_named_documentation",
        (
            (
                (
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/scoring.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/__init__.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/selection.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/union.py",\n'
                ),
                (
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/scoring.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/__init__.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/relation.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/selection.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/union.py",\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py": (
        2256,
        "45e5cee80192bc03f149bdfc86b0a679875bf8e68146f4342454b8dbec2bfb4b",
        "ordinary_original_bytes",
        (
            (
                (
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                    b"\n"
                    b"from ..network import PhenomenonEvent, PropagationCandidate\n"
                    b"\n"
                    b"\n"
                    b"def candidate_geojson(\n"
                ),
                (
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                    b"\n"
                    b"from ..candidates import CandidatePropagationScenario\n"
                    b"from ..network import PhenomenonEvent, PropagationCandidate\n"
                    b"from .relation import candidate_relation_details\n"
                    b"\n"
                    b"\n"
                    b"def candidate_geojson(\n"
                ),
            ),
            (
                (
                    b"    events: Mapping[str, PhenomenonEvent],\n"
                    b"    *,\n"
                    b"    directional: bool,\n"
                    b") -> dict[str, object]:\n"
                    b'    """Export evaluated rows without inferring a route or changing uncertainty."""\n'
                    b"    features = []\n"
                ),
                (
                    b"    events: Mapping[str, PhenomenonEvent],\n"
                    b"    *,\n"
                    b"    directional: bool,\n"
                    b"    scenario: CandidatePropagationScenario,\n"
                    b") -> dict[str, object]:\n"
                    b'    """Export evaluated rows without inferring a route or changing uncertainty."""\n'
                    b"    features = []\n"
                ),
            ),
            (
                (
                    b'                    "target_observation_ids": list(target.observation_ids),\n'
                    b'                    "source_event": source.as_dict(),\n'
                    b'                    "target_event": target.as_dict(),\n'
                    b"                },\n"
                    b"            }\n"
                    b"        )\n"
                ),
                (
                    b'                    "target_observation_ids": list(target.observation_ids),\n'
                    b'                    "source_event": source.as_dict(),\n'
                    b'                    "target_event": target.as_dict(),\n'
                    b'                    "relation_details": candidate_relation_details(\n'
                    b"                        row, source, target, scenario\n"
                    b"                    ),\n"
                    b"                },\n"
                    b"            }\n"
                    b"        )\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py": (
        5746,
        "32192101f980cedc3291f68795838ab7437404a1697f77ba699c2e21ae15867f",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    return {\n"
                    b'        "directed_candidates.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(directed, events, directional=True),\n"
                    b"        },\n"
                    b'        "indeterminate_pairs.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(indeterminate, events, directional=False),\n"
                    b"        },\n"
                    b'        "lower_level_edge_union.json": {\n'
                    b"            **metadata,\n"
                ),
                (
                    b"    return {\n"
                    b'        "directed_candidates.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(\n"
                    b"                directed, events, directional=True, scenario=result.scenario\n"
                    b"            ),\n"
                    b"        },\n"
                    b'        "indeterminate_pairs.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(\n"
                    b"                indeterminate, events, directional=False, scenario=result.scenario\n"
                    b"            ),\n"
                    b"        },\n"
                    b'        "lower_level_edge_union.json": {\n'
                    b"            **metadata,\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py": (
        8502,
        "e131724adacd5471cdc1b236079b5d091b33ed618ed5e1e1c8afab49363a0e57",
        "existing_named_native_asset_binding",
        (
            (
                (
                    b'            \'<div class="inline-actions"><button id="lra-download" \'\n'
                    b'            \'class="inline-button is-primary" type="button">\'\n'
                    b'            "Download selected estimates</button></div>"\n'
                    b'            \'<p class="search-meta"><a href="native-view.json">Complete bound model view</a> \xc2\xb7 \'\n'
                    b"            '<a href=\"index.html\">Complete report and original product downloads</a>'\n"
                    b'            "</p></div></details>"\n'
                ),
                (
                    b'            \'<div class="inline-actions"><button id="lra-download" \'\n'
                    b'            \'class="inline-button is-primary" type="button">\'\n'
                    b'            "Download selected estimates</button></div>"\n'
                    b'            \'<section id="lra-method-context" aria-label="Native LRA method and declared uncertainty">\'\n'
                    b"            '<p class=\"search-meta\">Method and uncertainty context unavailable until the bound model view is loaded.</p>'\n"
                    b'            "</section>"\n'
                    b'            \'<p class="search-meta"><a href="native-view.json">Complete bound model view</a> \xc2\xb7 \'\n'
                    b"            '<a href=\"index.html\">Complete report and original product downloads</a>'\n"
                    b'            "</p></div></details>"\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence.py": (
        11083,
        "0042bf044bc3ac845294ae0e060e0e36ce8ebbfbc7c022cddb3987c377aedfc7",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                ),
                (
                    b'"""Validate and normalize optional Atlas source, signal, and relation records."""\n'
                    b"\n"
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                ),
            ),
            (
                (
                    b"\n"
                    b"@dataclass(frozen=True)\n"
                    b"class AtlasEvidence:\n"
                    b"    detail_records: tuple[JsonObject, ...]\n"
                    b"    edge_records: tuple[JsonObject, ...]\n"
                    b"    scientific_signals: tuple[JsonObject, ...]\n"
                ),
                (
                    b"\n"
                    b"@dataclass(frozen=True)\n"
                    b"class AtlasEvidence:\n"
                    b'    """Normalized detail, relation, signal, and sequence records for map display."""\n'
                    b"\n"
                    b"    detail_records: tuple[JsonObject, ...]\n"
                    b"    edge_records: tuple[JsonObject, ...]\n"
                    b"    scientific_signals: tuple[JsonObject, ...]\n"
                ),
            ),
            (
                (
                    b'                "target_record_id": _required_text(row, "target_record_id", "edge"),\n'
                    b'                "source_country": source_country,\n'
                    b'                "target_country": target_country,\n'
                    b'                "cross_border": source_country != target_country,\n'
                    b"            }\n"
                    b"        )\n"
                    b'    normalized.sort(key=lambda item: str(item["edge_id"]))\n'
                ),
                (
                    b'                "target_record_id": _required_text(row, "target_record_id", "edge"),\n'
                    b'                "source_country": source_country,\n'
                    b'                "target_country": target_country,\n'
                    b"                # Historical flat edges use label compatibility. Native candidate\n"
                    b"                # flags retain their original value or absence without inference.\n"
                    b"                **(\n"
                    b'                    {"cross_border": source_country != target_country}\n'
                    b'                    if "candidate_status" not in row\n'
                    b"                    else {}\n"
                    b"                ),\n"
                    b"            }\n"
                    b"        )\n"
                    b'    normalized.sort(key=lambda item: str(item["edge_id"]))\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/native-lra.js": (
        18936,
        "33bd7c0644279d96c37d07960279be04f986c4d91ae42cbaa460536aa659818e",
        "ordinary_original_bytes",
        (
            (
                b"  re"
                b"turn"
                b" Obj"
                b"ect."
                b"free"
                b"ze({"
                b"refr"
                b"esh}"
                b");\n}"
                b"\n\nfu"
                b"ncti"
                b"on c"
                b"reat"
                b"eNat"
                b"iveL"
                b"raCo"
                b"ntro"
                b"ller"
                b"(vie"
                b"w, v"
                b"iewS"
                b"ha25"
                b"6, a"
                b"dapt"
                b"ers)"
                b" {\n "
                b" 'us"
                b"e st"
                b"rict"
                b"';\n "
                b" con"
                b"st c"
                b"lone"
                b" = v"
                b"alue"
                b" => "
                b"JSON"
                b".par"
                b"se(J"
                b"SON."
                b"stri"
                b"ngif"
                b"y(va"
                b"lue)"
                b");\n",
                b"  re"
                b"turn"
                b" Obj"
                b"ect."
                b"free"
                b"ze({"
                b"refr"
                b"esh}"
                b");\n}"
                b"\n\nfu"
                b"ncti"
                b"on n"
                b"ativ"
                b"eLra"
                b"Meth"
                b"odCo"
                b"ntex"
                b"tHtm"
                b"l(vi"
                b"ew) "
                b"{\n  "
                b"cons"
                b"t ob"
                b"ject"
                b" = v"
                b"alue"
                b" => "
                b"valu"
                b"e !="
                b"= nu"
                b"ll &"
                b"& ty"
                b"peof"
                b" val"
                b"ue ="
                b"== '"
                b"obje"
                b"ct' "
                b"&& !"
                b"Arra"
                b"y.is"
                b"Arra"
                b"y(va"
                b"lue)"
                b";\n  "
                b"cons"
                b"t es"
                b"cape"
                b" = v"
                b"alue"
                b" => "
                b"Stri"
                b"ng(v"
                b"alue"
                b").re"
                b"plac"
                b"e(/["
                b'&<>"'
                b"']/g"
                b", ch"
                b"arac"
                b"ter "
                b"=> ("
                b"{'&'"
                b":'&a"
                b"mp;'"
                b",'<'"
                b":'&l"
                b"t;',"
                b"'>':"
                b"'&gt"
                b";','"
                b"\"':'"
                b"&quo"
                b"t;',"
                b'"\'":'
                b"'&#3"
                b"9;'}"
                b"[cha"
                b"ract"
                b"er])"
                b");\n "
                b" con"
                b"st l"
                b"iter"
                b"al ="
                b" val"
                b"ue ="
                b"> es"
                b"cape"
                b"(JSO"
                b"N.st"
                b"ring"
                b"ify("
                b"valu"
                b"e));"
                b"\n  c"
                b"onst"
                b" met"
                b"hod "
                b"= ob"
                b"ject"
                b"(vie"
                b"w?.m"
                b"etho"
                b"d) ?"
                b" vie"
                b"w.me"
                b"thod"
                b" : {"
                b"};\n "
                b" con"
                b"st p"
                b"rofi"
                b"le ="
                b" typ"
                b"eof "
                b"meth"
                b"od.p"
                b"rofi"
                b"le ="
                b"== '"
                b"stri"
                b"ng' "
                b"&& m"
                b"etho"
                b"d.pr"
                b"ofil"
                b"e.tr"
                b"im()"
                b"\n   "
                b" ? e"
                b"scap"
                b"e(me"
                b"thod"
                b".pro"
                b"file"
                b") : "
                b"'Una"
                b"vail"
                b"able"
                b": no"
                b" val"
                b"id m"
                b"etho"
                b"d pr"
                b"ofil"
                b"e su"
                b"ppli"
                b"ed.'"
                b";\n  "
                b"func"
                b"tion"
                b" set"
                b"ting"
                b"s(va"
                b"lue,"
                b" lab"
                b"el) "
                b"{\n  "
                b"  if"
                b" (!o"
                b"bjec"
                b"t(va"
                b"lue)"
                b") re"
                b"turn"
                b" `<p"
                b">${e"
                b"scap"
                b"e(la"
                b"bel)"
                b"} un"
                b"avai"
                b"labl"
                b"e: n"
                b"o se"
                b"ttin"
                b"gs o"
                b"bjec"
                b"t su"
                b"ppli"
                b"ed.<"
                b"/p>`"
                b";\n  "
                b"  co"
                b"nst "
                b"rows"
                b" = ["
                b"];\n "
                b"   f"
                b"unct"
                b"ion "
                b"appe"
                b"nd(r"
                b"ecor"
                b"d, p"
                b"refi"
                b"x) {"
                b"\n   "
                b"   O"
                b"bjec"
                b"t.en"
                b"trie"
                b"s(re"
                b"cord"
                b").fo"
                b"rEac"
                b"h((["
                b"key,"
                b" ite"
                b"m]) "
                b"=> {"
                b"\n   "
                b"    "
                b" con"
                b"st p"
                b"ath "
                b"= pr"
                b"efix"
                b" ? `"
                b"${pr"
                b"efix"
                b"}.${"
                b"key}"
                b"` : "
                b"key;"
                b"\n   "
                b"    "
                b" if "
                b"(obj"
                b"ect("
                b"item"
                b") &&"
                b" Obj"
                b"ect."
                b"keys"
                b"(ite"
                b"m).l"
                b"engt"
                b"h) a"
                b"ppen"
                b"d(it"
                b"em, "
                b"path"
                b");\n "
                b"    "
                b"   e"
                b"lse "
                b"rows"
                b".pus"
                b"h(`<"
                b"tr><"
                b"th s"
                b"cope"
                b'="ro'
                b'w">$'
                b"{esc"
                b"ape("
                b"path"
                b")}</"
                b"th><"
                b"td>$"
                b"{lit"
                b"eral"
                b"(ite"
                b"m)}<"
                b"/td>"
                b"</tr"
                b">`);"
                b"\n   "
                b"   }"
                b");\n "
                b"   }"
                b"\n   "
                b" app"
                b"end("
                b"valu"
                b"e, '"
                b"');\n"
                b"    "
                b"retu"
                b"rn r"
                b"ows."
                b"leng"
                b"th\n "
                b"    "
                b" ? `"
                b"<div"
                b" cla"
                b'ss="'
                b"focu"
                b"s-de"
                b"tail"
                b"-tab"
                b"le-w"
                b'rap"'
                b"><ta"
                b"ble "
                b"clas"
                b's="f'
                b"ocus"
                b"-det"
                b"ail-"
                b"tabl"
                b'e"><'
                b"capt"
                b"ion>"
                b"${es"
                b"cape"
                b"(lab"
                b"el)}"
                b"</ca"
                b"ptio"
                b"n><t"
                b"head"
                b"><tr"
                b"><th"
                b" sco"
                b'pe="'
                b'col"'
                b">Dec"
                b"lare"
                b"d fi"
                b"eld<"
                b"/th>"
                b"<th "
                b"scop"
                b'e="c'
                b'ol">'
                b"Lite"
                b"ral "
                b"valu"
                b"e</t"
                b"h></"
                b"tr><"
                b"/the"
                b"ad><"
                b"tbod"
                b"y>${"
                b"rows"
                b".joi"
                b"n(''"
                b")}</"
                b"tbod"
                b"y></"
                b"tabl"
                b"e></"
                b"div>"
                b"`\n  "
                b"    "
                b": `<"
                b"p>${"
                b"esca"
                b"pe(l"
                b"abel"
                b")}: "
                b"no f"
                b"ield"
                b"s de"
                b"clar"
                b"ed.<"
                b"/p>`"
                b";\n  "
                b"}\n  "
                b"cons"
                b"t om"
                b"issi"
                b"ons "
                b"= vi"
                b"ew?."
                b"unce"
                b"rtai"
                b"nty_"
                b"omis"
                b"sion"
                b"s;\n "
                b" con"
                b"st u"
                b"ncer"
                b"tain"
                b"ty ="
                b" Arr"
                b"ay.i"
                b"sArr"
                b"ay(o"
                b"miss"
                b"ions"
                b") &&"
                b" omi"
                b"ssio"
                b"ns.e"
                b"very"
                b"(val"
                b"ue ="
                b"> ty"
                b"peof"
                b" val"
                b"ue ="
                b"== '"
                b"stri"
                b"ng' "
                b"&& v"
                b"alue"
                b".tri"
                b"m())"
                b"\n   "
                b" ? o"
                b"miss"
                b"ions"
                b".len"
                b"gth "
                b"? `<"
                b"ul>$"
                b"{omi"
                b"ssio"
                b"ns.m"
                b"ap(v"
                b"alue"
                b" => "
                b"`<li"
                b">${e"
                b"scap"
                b"e(va"
                b"lue)"
                b"}</l"
                b"i>`)"
                b".joi"
                b"n(''"
                b")}</"
                b"ul>`"
                b"\n   "
                b"   :"
                b" '<p"
                b">No "
                b"unce"
                b"rtai"
                b"nty "
                b"omis"
                b"sion"
                b"s we"
                b"re d"
                b"ecla"
                b"red."
                b" Thi"
                b"s do"
                b"es n"
                b"ot e"
                b"stab"
                b"lish"
                b" com"
                b"plet"
                b"e un"
                b"cert"
                b"aint"
                b"y co"
                b"vera"
                b"ge.<"
                b"/p>'"
                b"\n   "
                b" : '"
                b"<p>D"
                b"ecla"
                b"red "
                b"unce"
                b"rtai"
                b"nty "
                b"omis"
                b"sion"
                b"s un"
                b"avai"
                b"labl"
                b"e: n"
                b"o va"
                b"lid "
                b"list"
                b" sup"
                b"plie"
                b"d.</"
                b"p>';"
                b"\n  r"
                b"etur"
                b"n `<"
                b"h4>M"
                b"etho"
                b"d an"
                b"d de"
                b"clar"
                b"ed u"
                b"ncer"
                b"tain"
                b"ty</"
                b"h4><"
                b"p>Me"
                b"thod"
                b" pro"
                b"file"
                b": ${"
                b"prof"
                b"ile}"
                b"</p>"
                b"${se"
                b"ttin"
                b"gs(m"
                b"etho"
                b"d.co"
                b"nfig"
                b"urat"
                b"ion,"
                b" 'De"
                b"clar"
                b"ed c"
                b"onfi"
                b"gura"
                b"tion"
                b"')}$"
                b"{set"
                b"ting"
                b"s(me"
                b"thod"
                b".ver"
                b"sion"
                b"s, '"
                b"Decl"
                b"ared"
                b" ver"
                b"sion"
                b"s')}"
                b"<h5>"
                b"Decl"
                b"ared"
                b" unc"
                b"erta"
                b"inty"
                b" omi"
                b"ssio"
                b"ns</"
                b"h5>$"
                b"{unc"
                b"erta"
                b"inty"
                b"}<p>"
                b"Thes"
                b"e ar"
                b"e de"
                b"clar"
                b"atio"
                b"ns f"
                b"rom "
                b"the "
                b"boun"
                b"d re"
                b"sult"
                b", no"
                b"t va"
                b"lida"
                b"ted "
                b"assu"
                b"mpti"
                b"ons "
                b"or s"
                b"cien"
                b"tifi"
                b"c ap"
                b"prov"
                b"al. "
                b"Disp"
                b"lay "
                b"filt"
                b"ers "
                b"do n"
                b"ot r"
                b"efit"
                b" the"
                b" mod"
                b"el. "
                b"Meth"
                b"od s"
                b"umma"
                b"ries"
                b" do "
                b"not "
                b"esta"
                b"blis"
                b"h to"
                b"tal "
                b"unce"
                b"rtai"
                b"nty "
                b"or h"
                b"eld-"
                b"out "
                b"pred"
                b"icti"
                b"ve c"
                b"over"
                b"age."
                b"</p>"
                b"`;\n}"
                b"\n\nfu"
                b"ncti"
                b"on c"
                b"reat"
                b"eNat"
                b"iveL"
                b"raCo"
                b"ntro"
                b"ller"
                b"(vie"
                b"w, v"
                b"iewS"
                b"ha25"
                b"6, a"
                b"dapt"
                b"ers)"
                b" {\n "
                b" 'us"
                b"e st"
                b"rict"
                b"';\n "
                b" con"
                b"st c"
                b"lone"
                b" = v"
                b"alue"
                b" => "
                b"JSON"
                b".par"
                b"se(J"
                b"SON."
                b"stri"
                b"ngif"
                b"y(va"
                b"lue)"
                b");\n",
            ),
            (
                b"  fu"
                b"ncti"
                b"on m"
                b"ount"
                b"() {"
                b"\n   "
                b" con"
                b"st h"
                b"ost "
                b"= do"
                b"cume"
                b"nt.g"
                b"etEl"
                b"emen"
                b"tByI"
                b"d('l"
                b"ra-c"
                b"ontr"
                b"ols'"
                b");\n "
                b"   h"
                b"ost."
                b"hidd"
                b"en ="
                b" fal"
                b"se;\n"
                b"    "
                b"Obje"
                b"ct.e"
                b"ntri"
                b"es({"
                b"role"
                b"s: '"
                b"lra-"
                b"role"
                b"', s"
                b"ite_"
                b"ids:"
                b" 'lr"
                b"a-si"
                b"te',"
                b" tax"
                b"a: '"
                b"lra-"
                b"taxo"
                b"n', "
                b"bin_"
                b"ids:"
                b" 'lr"
                b"a-bi"
                b"n'})"
                b".for"
                b"Each"
                b"(([k"
                b"ey, "
                b"id])"
                b" => "
                b"{\n  "
                b"    "
                b"cons"
                b"t co"
                b"ntro"
                b"l = "
                b"docu"
                b"ment"
                b".get"
                b"Elem"
                b"entB"
                b"yId("
                b"id);"
                b"\n   "
                b"   a"
                b"llow"
                b"ed[k"
                b"ey]."
                b"forE"
                b"ach("
                b"valu"
                b"e =>"
                b" {\n",
                b"  fu"
                b"ncti"
                b"on m"
                b"ount"
                b"() {"
                b"\n   "
                b" con"
                b"st h"
                b"ost "
                b"= do"
                b"cume"
                b"nt.g"
                b"etEl"
                b"emen"
                b"tByI"
                b"d('l"
                b"ra-c"
                b"ontr"
                b"ols'"
                b");\n "
                b"   h"
                b"ost."
                b"hidd"
                b"en ="
                b" fal"
                b"se;\n"
                b"    "
                b"cons"
                b"t me"
                b"thod"
                b"Cont"
                b"ext "
                b"= do"
                b"cume"
                b"nt.g"
                b"etEl"
                b"emen"
                b"tByI"
                b"d('l"
                b"ra-m"
                b"etho"
                b"d-co"
                b"ntex"
                b"t');"
                b"\n   "
                b" if "
                b"(met"
                b"hodC"
                b"onte"
                b"xt) "
                b"meth"
                b"odCo"
                b"ntex"
                b"t.in"
                b"nerH"
                b"TML "
                b"= na"
                b"tive"
                b"LraM"
                b"etho"
                b"dCon"
                b"text"
                b"Html"
                b"(vie"
                b"w);\n"
                b"    "
                b"Obje"
                b"ct.e"
                b"ntri"
                b"es({"
                b"role"
                b"s: '"
                b"lra-"
                b"role"
                b"', s"
                b"ite_"
                b"ids:"
                b" 'lr"
                b"a-si"
                b"te',"
                b" tax"
                b"a: '"
                b"lra-"
                b"taxo"
                b"n', "
                b"bin_"
                b"ids:"
                b" 'lr"
                b"a-bi"
                b"n'})"
                b".for"
                b"Each"
                b"(([k"
                b"ey, "
                b"id])"
                b" => "
                b"{\n  "
                b"    "
                b"cons"
                b"t co"
                b"ntro"
                b"l = "
                b"docu"
                b"ment"
                b".get"
                b"Elem"
                b"entB"
                b"yId("
                b"id);"
                b"\n   "
                b"   a"
                b"llow"
                b"ed[k"
                b"ey]."
                b"forE"
                b"ach("
                b"valu"
                b"e =>"
                b" {\n",
            ),
        ),
    ),
}
NATIVE_METHOD_CONTEXT_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/native-lra.js"
ATLAS_RELATION_CONTEXT_SOURCES = frozenset(
    name for name in _RELATION_CONTEXT_CONTRACTS if name != NATIVE_METHOD_CONTEXT_SOURCE
)
CHRONOLOGY_ATLAS_RELATION_CONTEXT_SOURCES = frozenset(_RELATION_CONTEXT_CONTRACTS)
_MODELS_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py"
_PAYLOAD_SOURCE = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py"
)
_CAPTURE_CONTEXTS = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
}


def atlas_relation_context_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Restore each fixed source through only relation spans and its named prior law."""
    contract = _RELATION_CONTEXT_CONTRACTS.get(name)
    if contract is None:
        return False
    size, digest, composition, spans = contract
    if len(captured) != size or hashlib.sha256(captured).hexdigest() != digest:
        return False
    restored = current
    for original, extension in spans:
        if restored.count(extension) != 1:
            return False
        restored = restored.replace(extension, original, 1)
    if any(restored.count(original) != 1 for original, _ in spans):
        return False
    if composition == "ordinary_original_bytes":
        return restored == captured
    if composition == "existing_named_documentation":
        return (
            name == _MODELS_SOURCE
            and name in DOCUMENTED_SOURCE_STRINGS
            and _documented_source_matches(name, captured, restored)
        )
    if composition == "existing_named_native_asset_binding":
        return name == _PAYLOAD_SOURCE and atlas_extension_matches(
            name, captured, restored
        )
    return False


def validated_atlas_relation_context_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate changed relation semantics without retagging native observations."""
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    name = historical.get("path")
    contract = _RELATION_CONTEXT_CONTRACTS.get(name) if isinstance(name, str) else None
    if not isinstance(name, str) or contract is None:
        raise ReportRebuildError("Unknown Atlas relation context source")
    size, digest, composition, spans = contract
    expected = {"sha256": digest, "bytes": size}
    if (
        context is None
        or (
            name == NATIVE_METHOD_CONTEXT_SOURCE
            and source_buffer.prefix
            != "data/atlas/sample-chronology-source-view-capture"
        )
        or repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != context[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for original, path in group["resolved_paths"]
            if original == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Atlas relation context source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_path = _regular_confined_file(
        repository,
        name,
        "current Atlas relation context",
    )
    before = current_path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError("Atlas relation context source is linked or unbounded")
    current = current_path.read_bytes()
    if not atlas_relation_context_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Atlas relation context differs beyond its declared source changes"
        )
    source_buffer.fresh()
    again = _regular_confined_file(
        repository,
        name,
        "current Atlas relation context",
    )
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError(
            "Atlas relation context source changed during verification"
        )
    return {
        "path": name,
        "classification": "atlas_relation_context_extension",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": digest,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "named_relation_and_exact_documentation_spans_reversed": len(spans),
        "preexisting_source_correspondence": composition,
        "projection_method_context_and_refusals_intentionally_extended": True,
        "producer_inventory_intentionally_extended": name == _MODELS_SOURCE,
        "retained_current_producer_digest_guard_relaxed": False,
        "all_current_projection_outputs_equal_claimed": False,
        "historical_native_equal_current_output_claimed": False,
        "historical_browser_equal_current_browser_claimed": False,
        "historical_outputs_revalidated_under_current_contract_claimed": False,
        "old_native_equal_current_admission_claimed": False,
        "new_native_or_scientific_execution_claimed": False,
        **(
            {"declared_native_method_display_intentionally_extended": True}
            if name == NATIVE_METHOD_CONTEXT_SOURCE
            else {}
        ),
    }
