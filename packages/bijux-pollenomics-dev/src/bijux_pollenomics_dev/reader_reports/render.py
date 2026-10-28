"""Render the supported reader-report Markdown grammar without losing tokens."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

from .diagram import mermaid_to_dot
from .scientific_limits import validate_embedded_report
from .source import portable_link


class RenderError(ValueError):
    """Markdown contains a construct outside the report PDF grammar."""


def _verified_scientific_comments(markdown: str, root: Path, source: Path) -> str:
    """Suppress only structural markers while rendering every scientific statement."""
    if "scientific-verification-and-limits:" not in markdown:
        return markdown
    try:
        validate_embedded_report(markdown.encode("utf-8"))
        pattern = re.compile(
            r"^<!-- scientific-verification-and-limits:(?:begin|end) -->\n",
            re.MULTILINE,
        )
        result, count = pattern.subn("", markdown)
        if count != 2:
            raise ValueError("Scientific custody comment count differs")
        return result
    except (ValueError, OSError, KeyError) as error:
        raise RenderError(str(error)) from error


_ESCAPE = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "#": r"\#",
    "$": r"\$",
    "%": r"\%",
    "&": r"\&",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "→": r"\ensuremath{\rightarrow}",
}
_URL_ESCAPE = {"%": r"\%", "#": r"\#", "&": r"\&", "_": r"\_", "~": r"\string~"}


def escape_latex(value: str) -> str:
    """Escape text tokens before inserting them into a LaTeX document."""
    return "".join(_ESCAPE.get(char, char) for char in value)


_NUMERIC_CODE_ATOM = re.compile(
    r"(?<![\w.])[+\-−]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-−]?[0-9]+)?(?![\w.])"
)


def _inline_code(value: str) -> str:
    if len(value) <= 28:
        return r"\texttt{" + escape_latex(value) + "}"
    pieces: list[str] = []
    for part in re.split(r"(\s+|[/=*,;)])", value):
        escaped = escape_latex(part)
        if part in {"/", "=", "*", ",", ";", ")"}:
            pieces.append(escaped + r"\allowbreak{}")
        elif (
            len(part) > 28
            and not part.isspace()
            and not any(
                len(match[0]) > 28 for match in _NUMERIC_CODE_ATOM.finditer(part)
            )
        ):
            pieces.append(r"\seqsplit{" + escaped + "}")
        else:
            pieces.append(escaped)
    return r"\texttt{" + "".join(pieces) + "}"


def _inline_text(value: str) -> str:
    """Offer path delimiter breaks without splitting ordinary prose or numbers."""
    result: list[str] = []
    for part in re.split(r"(\s+)", value):
        escaped = escape_latex(part).replace("/", r"/\allowbreak{}")
        if "/" in part and re.search(r"\.[A-Za-z]{1,12}[.,;:!?)}\]]*\Z", part):
            escaped = escaped.replace("-", r"-\allowbreak{}").replace(
                r"\_", r"\_\allowbreak{}"
            )
        result.append(escaped)
    return "".join(result)


def _url_argument(value: str) -> str:
    """Keep only encoded URL characters before escaping TeX argument markers."""
    from urllib.parse import quote

    encoded = quote(value, safe="/:?=@+.,;-%#&_~")
    return "".join(_URL_ESCAPE.get(char, char) for char in encoded)


@dataclass(frozen=True)
class Asset:
    """Carry one rendered auxiliary asset and its content kind."""

    name: str
    content: str
    kind: str


@dataclass(frozen=True)
class RenderedReport:
    """Carry LaTeX, auxiliary assets, and the audited render counts."""

    latex: str
    assets: tuple[Asset, ...]
    local_link_count: int
    external_link_count: int
    diagram_count: int
    code_block_count: int


class ReportRenderer:
    """Render reviewed Markdown tokens against a pinned repository revision."""

    def __init__(self, root: Path, source: Path, revision: str) -> None:
        """Bind the repository, source report, and link revision for rendering."""
        self.root = root
        self.source = source
        self.revision = revision
        self.assets: list[Asset] = []
        self.local_links = 0
        self.external_links = 0
        self.diagrams = 0
        self.code_blocks = 0
        self.parser = MarkdownIt("commonmark").enable("table")

    def _inline(
        self, children: list[Token] | None, *, compound_lines: bool = False
    ) -> str:
        if children is None:
            raise RenderError("missing inline content")
        output: list[str] = []
        link_depth = 0
        punctuation_prefix = 0
        for index, token in enumerate(children):
            kind = token.type
            if kind == "text":
                output.append(_inline_text(token.content[punctuation_prefix:]))
                punctuation_prefix = 0
            elif kind == "code_inline":
                code = _inline_code(token.content)
                if (
                    compound_lines
                    and len(token.content) > 28
                    and token.content.count("(") > 1
                    and token.content.count(")") > 1
                    and re.search(r"\s[+*/−-]\s", token.content)
                ):
                    punctuation = ""
                    if index + 1 < len(children):
                        following = children[index + 1]
                        if following.type == "text":
                            match = re.match(r"[.,;:!?]+", following.content)
                            if match is not None:
                                punctuation = match[0]
                                punctuation_prefix = len(punctuation)
                    code = (
                        r"\linebreak[4]"
                        + code
                        + escape_latex(punctuation)
                        + r"\linebreak[4]"
                    )
                output.append(code)
            elif kind == "strong_open":
                output.append(r"\textbf{")
            elif kind == "strong_close":
                output.append("}")
            elif kind == "em_open":
                output.append(r"\emph{")
            elif kind == "em_close":
                output.append("}")
            elif kind == "link_open":
                destination = token.attrGet("href")
                if not isinstance(destination, str):
                    raise RenderError("link has no destination")
                url = portable_link(self.root, self.source, destination, self.revision)
                if url == destination:
                    self.external_links += 1
                else:
                    self.local_links += 1
                output.append(r"\href{" + _url_argument(url) + "}{")
                link_depth += 1
            elif kind == "link_close":
                if not link_depth:
                    raise RenderError("unmatched link_close")
                output.append("}")
                link_depth -= 1
            elif kind == "softbreak":
                output.append(" ")
            elif kind == "hardbreak":
                output.append(r"\\")
            else:
                raise RenderError(f"unsupported inline Markdown token: {kind}")
        if link_depth:
            raise RenderError("unclosed link")
        return "".join(output)

    def _table(self, tokens: list[Token], start: int) -> tuple[str, int]:
        rows: list[list[str]] = []
        header_rows = 0
        row: list[str] | None = None
        in_header = False
        index = start + 1
        while index < len(tokens):
            token = tokens[index]
            kind = token.type
            if kind == "table_close":
                break
            if kind in {"thead_open", "tbody_open"}:
                in_header = kind == "thead_open"
            elif kind in {"thead_close", "tbody_close", "th_close", "td_close"}:
                pass
            elif kind == "tr_open":
                row = []
            elif kind == "tr_close":
                if row is None:
                    raise RenderError("table row has no start")
                rows.append(row)
                if in_header:
                    header_rows += 1
                row = None
            elif kind in {"th_open", "td_open"}:
                if row is None:
                    raise RenderError("table cell outside row")
            elif kind == "inline":
                if row is None:
                    raise RenderError("table inline outside row")
                row.append(self._inline(token.children))
            else:
                raise RenderError(f"unsupported table Markdown token: {kind}")
            index += 1
        if index == len(tokens) or not rows or header_rows != 1:
            raise RenderError("table needs one header row and a closing token")
        columns = len(rows[0])
        if columns < 2 or any(len(row) != columns for row in rows):
            raise RenderError("table rows have inconsistent widths")
        width = rf"\dimexpr\linewidth/{columns}-2\tabcolsep-\arrayrulewidth-0.5pt\relax"
        spec = (
            "|"
            + "|".join(
                ">{\\raggedright\\arraybackslash}p{" + width + "}" for _ in rows[0]
            )
            + "|"
        )
        size = (
            r"\scriptsize"
            if columns >= 5
            else r"\footnotesize"
            if columns >= 4
            else r"\small"
        )
        result = [
            r"\begingroup",
            size,
            r"\setlength{\tabcolsep}{3pt}",
            r"\renewcommand{\arraystretch}{1.22}",
        ]
        result.append(r"\begin{longtable}{" + spec + "}")
        result.append(r"\hline")
        result.append(
            " & ".join(r"\textbf{" + cell + "}" for cell in rows[0]) + r" \\ \hline"
        )
        result.append(r"\endfirsthead")
        result.append(r"\hline")
        result.append(
            " & ".join(r"\textbf{" + cell + "}" for cell in rows[0]) + r" \\ \hline"
        )
        result.append(r"\endhead")
        for cells in rows[1:]:
            result.append(" & ".join(cells) + r" \\ \hline")
        result.extend([r"\end{longtable}", r"\endgroup"])
        return "\n".join(result) + "\n", index + 1

    def _fence(self, token: Token) -> str:
        info = token.info.strip().split(None, 1)
        language = info[0].lower() if info else ""
        if language == "mermaid":
            self.diagrams += 1
            name = f"diagram-{self.diagrams:03d}.dot"
            try:
                dot = mermaid_to_dot(token.content)
            except ValueError as error:
                raise RenderError(str(error)) from error
            self.assets.append(Asset(name=name, content=dot, kind="diagram"))
            pdf_name = name.removesuffix(".dot") + ".pdf"
            return (
                r"\begin{center}\includegraphics[width=\linewidth,height=0.55\textheight,keepaspectratio]{"
                + pdf_name
                + r"}\end{center}"
                + "\n"
            )
        if language and not re.fullmatch(r"[A-Za-z0-9_+.-]{1,32}", language):
            raise RenderError(f"unsupported code fence info: {token.info!r}")
        self.code_blocks += 1
        name = f"code-{self.code_blocks:03d}.txt"
        self.assets.append(Asset(name=name, content=token.content, kind="code"))
        label = (
            r"\noindent\textsf{" + escape_latex(language) + r"}\par"
            if language not in {"", "text", "plain"}
            else ""
        )
        return (
            label
            + "\n"
            + r"\VerbatimInput[breaklines=true,breakanywhere=true,fontsize=\footnotesize]{"
            + name
            + "}\n"
        )

    def render(self, markdown: str) -> RenderedReport:
        """Render supported Markdown and count links, diagrams, and code blocks."""
        pieces: list[str] = []
        markdown = _verified_scientific_comments(markdown, self.root, self.source)
        tokens = self.parser.parse(markdown)
        index = 0
        pending_heading: str | None = None
        ordered_depth = 0
        while index < len(tokens):
            token = tokens[index]
            kind = token.type
            if kind == "table_open":
                rendered, index = self._table(tokens, index)
                pieces.append(rendered)
                continue
            if kind == "heading_open":
                pending_heading = token.tag
            elif kind == "heading_close":
                if pending_heading is not None:
                    raise RenderError("heading is missing inline text")
            elif kind == "inline":
                body = self._inline(
                    token.children, compound_lines=pending_heading is None
                )
                if pending_heading is None and token.content.startswith(
                    "Retained evidence: "
                ):
                    body = body.replace(r"}, \href", r"}, \par\noindent\href")
                if pending_heading:
                    if pending_heading == "h1":
                        pieces.append(
                            r"\begin{center}{\LARGE\bfseries "
                            + body
                            + r"}\end{center}"
                            + "\n"
                        )
                    elif pending_heading == "h2":
                        pieces.append(r"\section*{" + body + "}\n")
                    elif pending_heading == "h3":
                        pieces.append(r"\subsection*{" + body + "}\n")
                    else:
                        raise RenderError(
                            f"unsupported heading level: {pending_heading}"
                        )
                    pending_heading = None
                else:
                    pieces.append(body + r"\par" + "\n")
            elif kind == "fence":
                pieces.append(self._fence(token))
            elif kind == "code_block":
                self.code_blocks += 1
                name = f"code-{self.code_blocks:03d}.txt"
                self.assets.append(Asset(name=name, content=token.content, kind="code"))
                pieces.append(
                    r"\VerbatimInput[breaklines=true,breakanywhere=true,fontsize=\footnotesize]{"
                    + name
                    + "}\n"
                )
            elif kind == "bullet_list_open":
                pieces.append(r"\begin{itemize}" + "\n")
            elif kind == "bullet_list_close":
                pieces.append(r"\end{itemize}" + "\n")
            elif kind == "ordered_list_open":
                ordered_depth += 1
                if ordered_depth > 4:
                    raise RenderError("ordered list nesting exceeds four levels")
                pieces.append(r"\begin{enumerate}" + "\n")
                start = token.attrGet("start") or 1
                pieces.append(
                    r"\setcounter{enum"
                    + ("i", "ii", "iii", "iv")[ordered_depth - 1]
                    + "}{"
                    + str(int(start) - 1)
                    + "}\n"
                )
            elif kind == "ordered_list_close":
                pieces.append(r"\end{enumerate}" + "\n")
                ordered_depth -= 1
            elif kind == "list_item_open":
                pieces.append(r"\item ")
            elif kind == "blockquote_open":
                pieces.append(r"\begin{quote}" + "\n")
            elif kind == "blockquote_close":
                pieces.append(r"\end{quote}" + "\n")
            elif kind == "hr":
                pieces.append(r"\par\noindent\rule{\linewidth}{0.4pt}\par" + "\n")
            elif kind in {"paragraph_open", "paragraph_close", "list_item_close"}:
                pass
            else:
                raise RenderError(f"unsupported block Markdown token: {kind}")
            index += 1
        if pending_heading:
            raise RenderError("unclosed heading")
        return RenderedReport(
            latex="".join(pieces),
            assets=tuple(self.assets),
            local_link_count=self.local_links,
            external_link_count=self.external_links,
            diagram_count=self.diagrams,
            code_block_count=self.code_blocks,
        )


def document_latex(body: str, title: str, source_path: str, source_sha256: str) -> str:
    """Wrap rendered content in the reproducible reader-paper LaTeX template."""
    return (
        r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=20mm,headheight=15pt]{geometry}
\usepackage{fontspec}
\setmainfont{STIXTwoText-Regular.otf}[
  BoldFont=STIXTwoText-Bold.otf,
  ItalicFont=STIXTwoText-Italic.otf,
  BoldItalicFont=STIXTwoText-BoldItalic.otf
]
\setsansfont{Arial}
\setmonofont{Menlo}
\usepackage{xcolor,graphicx,array,longtable,fvextra,seqsplit,xurl}
\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
\usepackage{microtype}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyfoot[L]{\footnotesize Source: \texttt{\seqsplit{"""
        + escape_latex(source_path)
        + r"""}}}
\fancyfoot[R]{\footnotesize \thepage}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.45em}
\setlength{\emergencystretch}{3em}
\hypersetup{pdftitle={"""
        + escape_latex(title)
        + r"""}}
\begin{document}
"""
        + r"""\noindent
{\footnotesize Source SHA-256: \texttt{\seqsplit{"""
        + escape_latex(source_sha256)
        + r"""}}. Repository links identify source paths; newly committed pages may be unavailable online until publication.}
"""
        + body
        + "\n\\end{document}\n"
    )
