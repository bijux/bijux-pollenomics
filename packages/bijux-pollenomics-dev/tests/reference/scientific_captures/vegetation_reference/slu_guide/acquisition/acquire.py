"""Acquire only the bounded current official SLU page and its literal guide asset."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import ssl
import sys
import time
from typing import Any
from urllib.parse import urljoin
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)

sys.path.insert(0, str(Path(__file__).absolute().parent))
from contracts import (
    PAGE,
    PAGE_LIMIT,
    PDF,
    PDF_LIMIT,
    REDIRECT_LIMIT,
    dump,
    guide_bytes,
    https_url,
    literal_pdf_link,
    pin,
    read,
    require,
    response_headers,
    sha,
    utc,
    validate_response,
)


class Redirects(HTTPRedirectHandler):
    def __init__(self, deadline: float) -> None:
        super().__init__()
        self.rows: list[dict[str, Any]] = []
        self.deadline = deadline

    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Any:
        require(time.monotonic() < self.deadline, "Retrieval wall budget")
        require(len(self.rows) < REDIRECT_LIMIT, "Redirect budget")
        locations = headers.get_all("Location", [])
        require(len(locations) == 1, "Ambiguous official redirect")
        destination = https_url(urljoin(req.full_url, locations[0]))
        require(destination == newurl, "Redirect URL differs from literal Location")
        self.rows.append(
            {
                "from_url": req.full_url,
                "literal_location": locations[0],
                "to_url": destination,
                "status": code,
                "UTC": utc(),
                "headers": list(headers.raw_items()),
            }
        )
        return super().redirect_request(req, fp, code, msg, headers, destination)


def bounded_body(response: Any, limit: int, deadline: float) -> bytes:
    chunks = []
    total = 0
    while True:
        require(time.monotonic() < deadline, "Retrieval wall budget")
        chunk = response.read(min(65536, limit + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        require(total <= limit, "Response byte budget")
        chunks.append(chunk)
    require(total > 0, "Empty official response")
    return b"".join(chunks)


def fetch(
    url: str, kind: str, ca: Path, deadline: float
) -> tuple[bytes, dict[str, Any]]:
    https_url(url)
    redirects = Redirects(deadline)
    context = ssl.create_default_context(cafile=str(ca))
    opener = build_opener(ProxyHandler({}), redirects, HTTPSHandler(context=context))
    request = Request(
        url,
        headers={
            "User-Agent": "bijux-source-custody/1",
            "Accept": "text/html" if kind == "page" else "application/pdf",
            "Accept-Encoding": "identity",
        },
    )
    started = utc()
    timeout = min(8.0, deadline - time.monotonic())
    require(timeout > 0, "Retrieval wall budget")
    with opener.open(request, timeout=timeout) as response:
        headers = list(response.headers.raw_items())
        require(response.status == 200, "Official HTTP response not200")
        response_headers(headers, kind)
        body = bounded_body(
            response, PAGE_LIMIT if kind == "page" else PDF_LIMIT, deadline
        )
        record = {
            "requested_url": url,
            "final_url": response.geturl(),
            "status": response.status,
            "headers": headers,
            "redirects": redirects.rows,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "started_UTC": started,
            "completed_UTC": utc(),
            "TLS": {
                "certificate_verification_required": context.verify_mode
                == ssl.CERT_REQUIRED,
                "hostname_verification": context.check_hostname,
                "CA": pin(ca),
                "OpenSSL": ssl.OPENSSL_VERSION,
            },
            "proxy_handler": {},
            "request_headers": dict(request.header_items()),
        }
    validate_response(record, url, body, kind)
    return body, record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    out = Path(plan["output"])
    require(
        Path(sys.executable).absolute() == Path(plan["qualified_python"])
        and sys.flags.isolated == 1,
        "Qualified isolated interpreter required",
    )
    for row in plan["input_pins"]:
        require(pin(Path(row["path"])) == row, "Source/runtime input changed")
    current_stage = "page"
    try:
        deadline = time.monotonic() + 45
        page, page_receipt = fetch(PAGE, "page", Path(plan["CA"]["path"]), deadline)
        with (out / "official-page.html").open("xb") as stream:
            stream.write(page)
        dump(out / "official-page-response.json", page_receipt)
        link = literal_pdf_link(page, page_receipt["final_url"])
        dump(out / "literal-guide-link.json", link)
        current_stage = "PDF"
        guide, pdf_receipt = fetch(PDF, "pdf", Path(plan["CA"]["path"]), deadline)
        with (out / "current-official-guide.pdf").open("xb") as stream:
            stream.write(guide)
        dump(out / "official-PDF-response.json", pdf_receipt)
        guide_bytes(guide, Path(plan["retained_guide"]["path"]).read_bytes())
        dump(
            out / "current-retrieval.json",
            {
                "schema_version": "current-official-slu-guide-retrieval.v1",
                "candidate": plan["candidate"],
                "plan_sha256": sha(args.plan),
                "actual_exit": 0,
                "page": pin(out / "official-page.html"),
                "literal_href": link,
                "official_PDF": pin(out / "current-official-guide.pdf"),
                "retained_guide": plan["retained_guide"],
                "same_raw_PDF_bytes": True,
                "current_retrieval_only": True,
                "original_2026_09_21_acquisition_recovered": False,
                "historical_a063_receipt_recovered": False,
                "workbook_or_outcome_requests": 0,
                "source_scope": "Current official public page/PDF acquisition only. No reconstruction of missing original retrieval/copy/literalhref receipt; no NFI measured-pair/outcome/human/rights/official-release acceptance.",
            },
        )
    except Exception as error:
        dump(
            out / "current-retrieval-refusal.json",
            {
                "candidate": plan["candidate"],
                "plan_sha256": sha(args.plan),
                "actual_exit": 1,
                "stage": current_stage,
                "UTC": utc(),
                "error_type": type(error).__name__,
                "reason": str(error),
                "current_or_original_source_chain_qualified": False,
            },
        )
        raise


if __name__ == "__main__":
    main()
