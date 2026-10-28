"""Reopen current raw official response/link/guide custody without another request."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).absolute().parent))
from contracts import (
    PAGE,
    PDF,
    PDF_BYTES,
    PDF_SHA,
    dump,
    guide_bytes,
    literal_pdf_link,
    pin,
    read,
    require,
    sha,
    validate_response,
)


def validate_claims(value: dict[str, Any], plan: dict[str, Any]) -> None:
    require(
        value["schema_version"] == "current-official-slu-guide-retrieval.v1"
        and value["candidate"] == plan["candidate"],
        "Current retrieval epoch differs",
    )
    require(
        type(value["actual_exit"]) is int
        and value["actual_exit"] == 0
        and value["current_retrieval_only"] is True,
        "Current acquisition did not pass",
    )
    require(
        value["original_2026_09_21_acquisition_recovered"] is False
        and value["historical_a063_receipt_recovered"] is False,
        "Current source was promoted to missing history",
    )
    require(
        type(value["workbook_or_outcome_requests"]) is int
        and value["workbook_or_outcome_requests"] == 0,
        "Unrelated data request claim",
    )
    require(
        value["same_raw_PDF_bytes"] is True
        and value["retained_guide"] == plan["retained_guide"],
        "Retained comparison binding differs",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    out = Path(plan["output"])
    progress = read(out / "stage-progress.json")
    require(
        len(progress) == 1
        and progress[0]["argv"] == plan["stages"][0]["argv"]
        and type(progress[0]["actual_exit"]) is int
        and progress[0]["actual_exit"] == 0
        and progress[0]["timed_out"] is False,
        "Actual current acquisition stage did not pass",
    )
    report = read(out / "current-retrieval.json")
    validate_claims(report, plan)
    require(report["plan_sha256"] == sha(args.plan), "Current plan SHA differs")
    page = (out / "official-page.html").read_bytes()
    guide = (out / "current-official-guide.pdf").read_bytes()
    for name, url, body, kind in [
        ("official-page-response.json", PAGE, page, "page"),
        ("official-PDF-response.json", PDF, guide, "pdf"),
    ]:
        response = read(out / name)
        validate_response(response, url, body, kind)
        require(
            response["TLS"]["certificate_verification_required"] is True
            and response["TLS"]["hostname_verification"] is True
            and response["TLS"]["CA"] == plan["CA"]
            and response["TLS"]["OpenSSL"] == plan["OpenSSL"]
            and response["proxy_handler"] == {},
            "TLS/proxy authority differs",
        )
    link = literal_pdf_link(
        page, read(out / "official-page-response.json")["final_url"]
    )
    require(
        read(out / "literal-guide-link.json") == report["literal_href"] == link,
        "Literal official-page href witness differs",
    )
    guide_bytes(guide, Path(plan["retained_guide"]["path"]).read_bytes())
    require(
        report["page"] == pin(out / "official-page.html")
        and report["official_PDF"] == pin(out / "current-official-guide.pdf"),
        "Current raw source identity differs",
    )
    for row in plan["input_pins"]:
        require(pin(Path(row["path"])) == row, "Protected source/runtime changed")
    dump(
        out / "independent-current-source-review.json",
        {
            "schema_version": "independent-current-slu-guide-source-review.v1",
            "candidate": plan["candidate"],
            "plan_sha256": sha(args.plan),
            "actual_exit": 0,
            "current_raw_page": pin(out / "official-page.html"),
            "literal_link": link,
            "current_guide": pin(out / "current-official-guide.pdf"),
            "guide_sha256": PDF_SHA,
            "guide_bytes": PDF_BYTES,
            "retained_raw_PDF_exact": True,
            "official_current_page_response_link_asset_chain": True,
            "original_2026_09_21_or_a063_recovered": False,
            "workbook_measurement_outcomes_or_guide_history_closed": False,
            "additional_network_requests": 0,
            "scope": "Current source acquisition and exact public PDF copy only, distinct from absent original acquisition and current NFI benchmark/human/release acceptance.",
        },
    )


if __name__ == "__main__":
    main()
