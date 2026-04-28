#!/usr/bin/env python3
"""Recursively extract plain text from a directory of mixed-format sources.

Supported inputs: .pdf, .html, .htm, .docx, .txt, .md
Output: one .txt per input, mirroring the input tree under --out.

Usage:
    python extract-text.py --in /path/to/sources --out /path/to/texts
    python extract-text.py --in ./pdfs --out ./extracted --skip-existing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXTRACTORS: dict[str, str] = {
    ".pdf": "pdf",
    ".html": "html",
    ".htm": "html",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "txt",
}


def extract_pdf(path: Path) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(str(path)) or ""


def extract_html(path: Path) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(path.read_bytes(), "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def extract_docx(path: Path) -> str:
    import docx  # python-docx
    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


EXTRACT_FUNCS = {
    "pdf": extract_pdf,
    "html": extract_html,
    "docx": extract_docx,
    "txt": extract_txt,
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="src", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    src: Path = args.src
    dst: Path = args.out
    if not src.is_dir():
        print(f"Error: {src} is not a directory", file=sys.stderr)
        return 1
    dst.mkdir(parents=True, exist_ok=True)

    n_ok = n_skip = n_fail = 0
    for source in src.rglob("*"):
        if not source.is_file():
            continue
        ext = source.suffix.lower()
        kind = EXTRACTORS.get(ext)
        if not kind:
            continue
        rel = source.relative_to(src).with_suffix(".txt")
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if args.skip_existing and out.exists():
            n_skip += 1
            continue
        try:
            text = EXTRACT_FUNCS[kind](source)
            out.write_text(text, encoding="utf-8")
            n_ok += 1
            print(f"ok   {rel}")
        except Exception as e:  # noqa: BLE001
            n_fail += 1
            print(f"fail {rel}: {e}", file=sys.stderr)

    print(f"\nExtracted: {n_ok}  Skipped: {n_skip}  Failed: {n_fail}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
