#!/usr/bin/env python3
"""Quick KWIC concordance over a directory of plain-text files.

Word-boundary regex by default; pass --regex for full PCRE patterns.
Good for sub-million-token corpora; for larger work, use CWB.

Usage:
    python concordance.py --dir /path/to/texts --query "literally"
    python concordance.py --dir ./texts --query "break.*ice" --regex --window 10
    python concordance.py --dir ./texts --query "literally" --max 50 --case-sensitive
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", required=True, type=Path)
    p.add_argument("--query", required=True)
    p.add_argument("--window", type=int, default=7, help="words of context per side")
    p.add_argument("--max", type=int, default=200, help="max KWIC lines to print")
    p.add_argument("--regex", action="store_true",
                   help="treat --query as a full regex (default: word-boundary literal)")
    p.add_argument("--case-sensitive", action="store_true")
    args = p.parse_args()

    if not args.dir.is_dir():
        print(f"Error: {args.dir} is not a directory", file=sys.stderr)
        return 1

    pattern = args.query if args.regex else r"\b" + re.escape(args.query) + r"\b"
    flags = 0 if args.case_sensitive else re.IGNORECASE
    rx = re.compile(pattern, flags)

    n_hits = 0
    for txt in args.dir.rglob("*.txt"):
        try:
            content = txt.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        tokens = content.split()
        # Build per-token offsets so KWIC windows are word-based
        for i, tok in enumerate(tokens):
            if rx.search(tok):
                left = " ".join(tokens[max(0, i - args.window):i])
                right = " ".join(tokens[i + 1:i + 1 + args.window])
                # Truncate long left/right for terminal readability
                left = left[-60:].rjust(60)
                right = right[:60].ljust(60)
                source = txt.relative_to(args.dir)
                print(f"{source}\t{left}  >>{tok}<<  {right}")
                n_hits += 1
                if n_hits >= args.max:
                    print(f"\n... reached --max {args.max}; stopping.")
                    return 0
    print(f"\n{n_hits} hits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
