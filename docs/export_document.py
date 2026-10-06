#!/usr/bin/env python3
"""Exporteer een document als leesbaar PDF."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable


DOCS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_DIR.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "output" / "documents"
SUPPORTED_SUFFIXES = {".md", ".markdown", ".html", ".htm", ".txt", ".docx", ".pdf"}

CSS = r"""
@page {
  size: A4;
  margin: 17mm 15mm 20mm;
}

:root {
  --red: #d71920;
  --dark: #242021;
  --muted: #655f61;
  --line: #d8d3d4;
  --soft: #f5f2f2;
}

html {
  font-family: Arial, Helvetica, sans-serif;
  color: var(--dark);
  font-size: 10.4pt;
  line-height: 1.48;
}

body { margin: 0; }

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 22mm;
  margin: 0 0 14mm;
  padding-bottom: 6mm;
  border-bottom: 3px solid var(--red);
}

.brand img { width: 47mm; max-height: 20mm; }
.brand span {
  color: var(--muted);
  font-size: 8.5pt;
  letter-spacing: .08em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 10mm;
  max-width: 150mm;
  font-size: 27pt;
  line-height: 1.12;
}

h1::before {
  display: block;
  width: 22mm;
  height: 4px;
  margin-bottom: 6mm;
  background: var(--red);
  content: "";
}

h2 {
  break-before: page;
  margin: 0 0 6mm;
  padding-bottom: 3mm;
  border-bottom: 2px solid var(--red);
  font-size: 20pt;
  line-height: 1.2;
}

h2:first-of-type { break-before: auto; }
h3 {
  break-after: avoid;
  margin: 8mm 0 3mm;
  color: var(--red);
  font-size: 14.5pt;
  line-height: 1.25;
}
h4 { break-after: avoid; margin: 6mm 0 2.5mm; font-size: 11.5pt; }
p, ul, ol, blockquote { orphans: 3; widows: 3; }
a { color: #8c1116; text-decoration: none; }
blockquote {
  margin: 5mm 0;
  padding: 4mm 5mm;
  border-left: 4px solid var(--red);
  background: var(--soft);
}
blockquote p { margin: 0; }

table {
  width: 100%;
  margin: 4mm 0 6mm;
  border-collapse: collapse;
  font-size: 7.5pt;
  line-height: 1.28;
  table-layout: fixed;
}
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td {
  padding: 2.1mm 1.8mm;
  border: 1px solid var(--line);
  vertical-align: top;
  overflow-wrap: anywhere;
}
th { color: #fff; background: var(--dark); font-weight: 700; }
tbody tr:nth-child(even) td { background: var(--soft); }
code { font-family: "SFMono-Regular", Consolas, monospace; font-size: .88em; }
pre {
  break-inside: avoid;
  padding: 4mm;
  border-left: 4px solid var(--red);
  background: #f1eeee;
  white-space: pre-wrap;
}

.diagram-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2.5mm;
  margin: 6mm 0;
  break-inside: avoid;
}
.diagram-step {
  min-height: 16mm;
  padding: 4mm 3mm;
  border-top: 3px solid var(--red);
  background: var(--soft);
  font-size: 8.5pt;
  font-weight: 700;
  text-align: center;
}
.diagram-step small {
  display: block;
  margin-bottom: 1.5mm;
  color: var(--red);
  font-size: 7pt;
  letter-spacing: .08em;
  text-transform: uppercase;
}
"""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exporteer een document als normaal PDF-bestand."
    )
    parser.add_argument(
        "--document",
        type=Path,
        help="Document om te exporteren. Zonder deze optie verschijnt een keuzelijst.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Map voor PDF-bestanden. Standaard: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--title",
        help="Optionele titel voor de PDF en metadata.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Toon beschikbare documenten en stop.",
    )
    return parser.parse_args()


def discover_documents() -> list[Path]:
    documents = [
        path
        for path in DOCS_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_SUFFIXES
        and path.name != Path(__file__).name
    ]
    return sorted(documents, key=lambda path: path.relative_to(DOCS_DIR).as_posix().lower())


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def print_documents(documents: Iterable[Path]) -> None:
    items = list(documents)
    if not items:
        print("Geen ondersteunde documenten gevonden in docs.")
        return
    for index, path in enumerate(items, start=1):
        print(f"{index:>2}. {display_path(path)}")


def choose_document(documents: list[Path]) -> Path:
    if not documents:
        raise RuntimeError("Geen ondersteunde documenten gevonden in docs.")
    print("Kies een document om te exporteren:\n")
    print_documents(documents)
    print()
    while True:
        answer = input(f"Nummer 1-{len(documents)}: ").strip()
        try:
            index = int(answer)
        except ValueError:
            print("Vul een geldig nummer in.")
            continue
        if 1 <= index <= len(documents):
            return documents[index - 1]
        print("Het gekozen nummer staat niet in de lijst.")


def validate_source(path: Path) -> Path:
    source = path.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Document niet gevonden: {source}")
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Niet-ondersteund bestandstype. Gebruik een van: {supported}")
    return source


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return normalized[:80] or "document"


def document_title(source: Path, explicit_title: str | None) -> str:
    if explicit_title and explicit_title.strip():
        return explicit_title.strip()
    if source.suffix.lower() in {".md", ".markdown", ".txt"}:
        text = source.read_text(encoding="utf-8", errors="replace")
        heading = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
        if heading:
            return heading.group(1).strip()
    return source.stem.replace("_", " ").replace("-", " ").strip().title()


def find_pandoc() -> str:
    executable = shutil.which("pandoc")
    if not executable:
        raise RuntimeError("Pandoc ontbreekt. Installeer Pandoc om documenten naar PDF om te zetten.")
    return executable


def find_chrome() -> str:
    configured = os.environ.get("CHROME_BIN", "").strip()
    candidates = [
        configured,
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
        shutil.which("microsoft-edge") or "",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError(
        "Google Chrome, Chromium of Edge ontbreekt. Stel eventueel CHROME_BIN in op het browserpad."
    )


def github_heading_slug(value: str) -> str:
    """Maak dezelfde soort anchors als GitHub voor Markdown-koppen."""
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[`*_~]", "", value)
    value = html.unescape(value).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s", "-", value)
    return value.strip("-") or "section"


def add_markdown_anchors(markdown: str) -> str:
    """Voeg expliciete anchors toe zodat Markdown-TOC-links ook in de PDF werken."""
    heading_pattern = re.compile(r"^( {0,3})(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
    explicit_id_pattern = re.compile(r"\s*\{#([A-Za-z][A-Za-z0-9_.:-]*)\}\s*$")
    fence_pattern = re.compile(r"^ {0,3}(`{3,}|~{3,})")

    slug_counts: dict[str, int] = {}
    result: list[str] = []
    active_fence: tuple[str, int] | None = None

    for line in markdown.splitlines(keepends=True):
        fence = fence_pattern.match(line)
        if fence:
            marker = fence.group(1)
            char = marker[0]
            length = len(marker)
            if active_fence is None:
                active_fence = (char, length)
            elif char == active_fence[0] and length >= active_fence[1]:
                active_fence = None
            result.append(line)
            continue

        if active_fence is not None:
            result.append(line)
            continue

        match = heading_pattern.match(line.rstrip("\r\n"))
        if not match:
            result.append(line)
            continue

        heading_text = match.group(3).strip()
        explicit_id = explicit_id_pattern.search(heading_text)
        if explicit_id:
            anchor = explicit_id.group(1)
        else:
            base = github_heading_slug(heading_text)
            occurrence = slug_counts.get(base, 0)
            anchor = base if occurrence == 0 else f"{base}-{occurrence}"
            slug_counts[base] = occurrence + 1

        newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
        result.append(f'<a id="{html.escape(anchor, quote=True)}"></a>{newline}')
        result.append(line)

    return "".join(result)


def replace_mermaid(markdown: str) -> str:
    pattern = re.compile(r"```mermaid\s*\n(.*?)```", flags=re.DOTALL | re.IGNORECASE)

    def replacement(match: re.Match[str]) -> str:
        diagram = match.group(1)
        labels = re.findall(r'\["([^"\n]+)"\]', diagram)
        if not labels:
            labels = re.findall(r"\[([^\]\n]+)\]", diagram)
        unique_labels = list(dict.fromkeys(label.strip() for label in labels if label.strip()))
        if not unique_labels:
            return f"```text\n{diagram.strip()}\n```"
        cards = []
        for index, label in enumerate(unique_labels, start=1):
            cards.append(
                '<div class="diagram-step">'
                f"<small>Onderdeel {index}</small>{html.escape(label)}"
                "</div>"
            )
        return (
            '<div class="diagram-grid" role="img" aria-label="Procesdiagram">'
            + "".join(cards)
            + "</div>"
        )

    return pattern.sub(replacement, markdown)


def write_header(path: Path, title: str) -> None:
    logo = PROJECT_ROOT / "static" / "provincie-utrecht-logo.svg"
    logo_html = '<img src="static/provincie-utrecht-logo.svg" alt="Provincie Utrecht">' if logo.is_file() else ""
    path.write_text(
        '<div class="brand">'
        + logo_html
        + f"<span>{html.escape(title)}</span>"
        + "</div>",
        encoding="utf-8",
    )


def prepare_pandoc_source(source: Path, temporary: Path) -> Path:
    if source.suffix.lower() not in {".md", ".markdown"}:
        return source
    prepared = temporary / source.name
    markdown = source.read_text(encoding="utf-8", errors="replace")
    markdown = replace_mermaid(markdown)
    markdown = add_markdown_anchors(markdown)
    prepared.write_text(markdown, encoding="utf-8")
    return prepared


def run(command: list[str], label: str) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"{label} is mislukt.\n{detail}")


def add_footer(source: Path, target: Path, title: str) -> int:
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject
    except ImportError as exc:
        raise RuntimeError(
            "De Python-package pypdf ontbreekt. Installeer deze met: python3 -m pip install pypdf"
        ) from exc

    reader = PdfReader(source)
    writer = PdfWriter()

    # Clone the complete PDF document instead of copying pages one by one.
    # This preserves document-level structures used by internal links,
    # named destinations, outlines and other catalog entries.
    writer.clone_document_from_reader(reader)

    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_reference = writer._add_object(font)

    total = len(writer.pages)

    for number, page in enumerate(writer.pages, start=1):

        # Important: make PDF rotation part of the actual page content.
        # After this, y=0 is visually the bottom of the page.
        page.transfer_rotation_to_content()

        resources = page.get("/Resources")
        if resources is None:
            resources = DictionaryObject()
            page[NameObject("/Resources")] = resources
        else:
            resources = resources.get_object()

        fonts = resources.get("/Font")
        if fonts is None:
            fonts = DictionaryObject()
            resources[NameObject("/Font")] = fonts
        else:
            fonts = fonts.get_object()

        fonts[NameObject("/FooterFont")] = font_reference

        font_size = 10
        footer_y = 20

        footer = (
            "q "
            f"BT /FooterFont {font_size} Tf "
            f"1 0 0 1 42 {footer_y} Tm "
            f"(Pagina {number} van {total}) Tj "
            "ET Q"
        )

        stream = DecodedStreamObject()
        stream.set_data(footer.encode("latin-1", errors="replace"))
        stream_reference = writer._add_object(stream)

        contents = page.get("/Contents")

        if contents is None:
            page[NameObject("/Contents")] = stream_reference
        elif isinstance(contents, ArrayObject):
            contents.append(stream_reference)
        else:
            page[NameObject("/Contents")] = ArrayObject([
                contents,
                stream_reference,
            ])

    writer.add_metadata({
        "/Title": title,
        "/Author": "ScenarioDossier documentexport",
    })

    with target.open("wb") as output:
        writer.write(output)

    return total


def pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def create_pdf(source: Path, target: Path, title: str, temporary: Path) -> int:
    if source.suffix.lower() == ".pdf":
        shutil.copy2(source, target)
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "De Python-package pypdf ontbreekt. Installeer deze met: python3 -m pip install pypdf"
            ) from exc
        return len(PdfReader(target).pages)

    pandoc = find_pandoc()
    chrome = find_chrome()
    prepared_source = prepare_pandoc_source(source, temporary)
    css = temporary / "document.css"
    header = temporary / "header.html"
    html_output = temporary / "document.html"
    raw_pdf = temporary / "document-raw.pdf"
    css.write_text(CSS, encoding="utf-8")
    write_header(header, title)

    resource_paths = os.pathsep.join(dict.fromkeys([
        str(source.parent),
        str(DOCS_DIR),
        str(PROJECT_ROOT),
    ]))
    command = [
        pandoc,
        str(prepared_source),
        "--to=html5",
        "--standalone",
        "--embed-resources",
        f"--resource-path={resource_paths}",
        f"--css={css}",
        f"--include-before-body={header}",
        "--metadata",
        f"pagetitle={title}",
        f"--output={html_output}",
    ]
    if source.suffix.lower() in {".md", ".markdown"}:
        command.insert(2, "--from=gfm")
    run(command, "Conversie met Pandoc")
    run([
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--print-to-pdf={raw_pdf}",
        html_output.as_uri(),
    ], "PDF-export met de browser")
    if not raw_pdf.is_file() or raw_pdf.stat().st_size == 0:
        raise RuntimeError("De browser heeft geen geldig PDF-bestand gemaakt.")
    return add_footer(raw_pdf, target, title)


def export_pdf(source: Path, output_dir: Path, title: str) -> Path:
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{slug(source.stem)}.pdf"

    with tempfile.TemporaryDirectory(prefix="document-export-") as temporary_name:
        temporary = Path(temporary_name)
        create_pdf(source, target, title, temporary)

    return target

def main() -> int:
    args = parse_arguments()
    documents = discover_documents()
    if args.list:
        print_documents(documents)
        return 0

    try:
        source = validate_source(args.document) if args.document else choose_document(documents)
        title = document_title(source, args.title)
        print(f"\nExporteren: {display_path(source)}")
        pdf = export_pdf(source, args.output_dir, title)
        print(f"Gereed: {pdf}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Fout: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nExport geannuleerd.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
