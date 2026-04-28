#!/usr/bin/env python3
"""Annotate a directory of plain-text files with spaCy: tokenize, POS-tag, lemmatize.

Output: vertical-text format (one token per line, tabs separate columns), suitable
for `cwb-encode -xsB`. One .vrt per input .txt, mirroring the directory layout.

Vertical columns: word \t lemma \t POS \t TAG

Usage:
    python annotate.py --in /path/to/texts --out /path/to/annotated
    python annotate.py --in ./texts --out ./vrt --model en_core_web_sm --batch 1000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="src", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--model", default="en_core_web_sm")
    p.add_argument("--batch", type=int, default=200)
    p.add_argument("--corpus-id", default="MYCORPUS",
                   help="corpus id used in <text> wrapper element")
    args = p.parse_args()

    try:
        import spacy
    except ImportError:
        print("Error: spaCy not installed. Run setup-python-env.sh first.", file=sys.stderr)
        return 1

    print(f"Loading spaCy model: {args.model} ...")
    nlp = spacy.load(args.model, disable=["parser", "ner"])

    src: Path = args.src
    dst: Path = args.out
    dst.mkdir(parents=True, exist_ok=True)

    files = sorted(src.rglob("*.txt"))
    if not files:
        print(f"No .txt files under {src}", file=sys.stderr)
        return 1

    for path in files:
        rel = path.relative_to(src).with_suffix(".vrt")
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue

        with out.open("w", encoding="utf-8") as fh:
            text_id = path.stem.replace('"', "'")
            fh.write(f'<text id="{text_id}">\n')
            doc = nlp(text)
            for sent in doc.sents:
                fh.write("<s>\n")
                for tok in sent:
                    if tok.is_space:
                        continue
                    word = tok.text.replace("\t", " ").replace("\n", " ")
                    lemma = (tok.lemma_ or word).replace("\t", " ")
                    pos = tok.pos_ or "X"
                    tag = tok.tag_ or "X"
                    fh.write(f"{word}\t{lemma}\t{pos}\t{tag}\n")
                fh.write("</s>\n")
            fh.write("</text>\n")
        print(f"ok   {rel}")

    print(f"\nDone: {len(files)} file(s) annotated to {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
