# File formats and conversions for corpus building

The first stage of any corpus project is getting messy real-world files into clean UTF-8 text. This file maps the common input formats to the tools that handle them best, with the trade-offs.

## PDF

Three quality tiers, in increasing cost:

1. **`pdfminer.six`** (Python; what `extract-text.py` uses by default)
   - Pure Python, fast enough for thousands of files
   - Decent text extraction; struggles with two-column layouts and headers/footers
   - No OCR — fails silently on scanned PDFs

2. **`pdftotext` from Poppler** (CLI; `brew install poppler`)
   - Faster than pdfminer.six; sometimes better on multi-column
   - `pdftotext -layout file.pdf -` preserves columns; `pdftotext -raw` is more linear
   - Still no OCR

3. **OCR for scanned PDFs**
   - `ocrmypdf input.pdf output.pdf` (which uses Tesseract)
   - Slow (minutes per PDF) but produces searchable PDFs that pdfminer.six / pdftotext can then handle
   - For Czech, German, etc., specify language: `ocrmypdf -l ces input.pdf output.pdf`

For **academic-quality PDF→markdown** (preserving headings, tables, math), see the user's `academic-pdf-to-mkd` skill in this same workskills folder. That's purpose-built and worth using when output quality matters more than throughput.

## HTML / web pages

`extract-text.py` uses BeautifulSoup with the lxml parser. It strips `<script>`, `<style>`, and `<noscript>`, then takes `get_text()`.

Better quality requires content extraction — separating the article body from navigation, ads, related-links sidebars:

- `trafilatura` (Python) — best-in-class for general web content extraction:
  ```python
  import trafilatura
  raw = open("page.html").read()
  text = trafilatura.extract(raw, include_comments=False, include_tables=False)
  ```
- `readability-lxml` — older but still useful

For **scraping** (fetching the HTML in the first place), use `requests` for static pages and Playwright (the `chrome-devtools-mcp` plugin or direct) for JavaScript-heavy sites. Don't write the corpus-tools-skill scrape; pick the right tool per site.

## DOCX

`python-docx` (the `docx` import in `extract-text.py`) extracts paragraphs cleanly. It does NOT extract:

- Text in headers and footers
- Text in text boxes
- Tracked changes (will silently drop deleted text or accept all changes — depends on the file)
- Comments

For tracked-changes-aware extraction, see the user's `doc-editorial-skill`. For tables and complex layouts, see `docx` reference docs.

## EPUB

Not handled by `extract-text.py`. Use `ebooklib` or `pandoc`:

```bash
pandoc -f epub -t plain book.epub -o book.txt
```

`pandoc` is reliable and supports many input formats (EPUB, ODT, RTF, LaTeX, MediaWiki, etc.). One Homebrew install (`brew install pandoc`) covers a wide format space.

## Plain text

If the file is already `.txt` or `.md`, just read it. The only gotchas:

- **Encoding detection**: not all "plain text" is UTF-8. Run `file --mime-encoding *.txt` to inventory; `iconv -f WINDOWS-1252 -t UTF-8 input.txt` to convert
- **Line endings**: Windows CRLF vs Unix LF rarely matters for corpus work but trips up some tools. `dos2unix file.txt` if needed

## CSV / TSV / JSONL

These are common output formats from prior pipelines. For corpus-building, treat one row as one document:

```python
import polars as pl
df = pl.read_csv("articles.csv")
for row in df.iter_rows(named=True):
    out = Path(f"texts/{row['id']}.txt")
    out.write_text(row["body"], encoding="utf-8")
```

## Vertical text (`.vrt`) — CWB input format

This is what `scripts/annotate.py` produces. One token per line; tabs separate columns; XML-like tags mark structure:

```
<text id="article42">
<s>
The     the     DET     DT
quick   quick   ADJ     JJ
brown   brown   ADJ     JJ
fox     fox     NOUN    NN
.       .       PUNCT   .
</s>
</text>
```

For `cwb-encode` this is the canonical input. For sharing or human inspection, the format is also reasonable.

## CoNLL-U — Universal Dependencies format

```
1   The     the     DET   DT    Definite=Def|PronType=Art   2  det     _  _
2   fox     fox     NOUN  NN    Number=Sing                 0  root    _  _
...
```

Ten tab-separated columns: id, word, lemma, upos, xpos, features, head, deprel, deps, misc. Sentence boundaries are blank lines.

Stanza outputs CoNLL-U directly; spaCy via `spacy_conll`. UD treebanks for ~150 languages live at https://universaldependencies.org. The `udapi` Python library handles CoNLL-U I/O cleanly.

## Audio and video

For transcription-derived corpora (oral history, interviews, broadcast news), the user's `speech-to-text` skill is the right tool — local MLX-based ASR with optional speaker diarization, producing time-coded text that can feed into the rest of this pipeline.

Per the Learning Log epistemic rules: ASR-generated transcripts have low reliability for proper nouns. Always verify named entities externally before treating them as corpus evidence.

## Format-conversion quick-reference

| Source | Target | Tool |
|---|---|---|
| PDF (digital) | TXT | `pdfminer.six` (in `extract-text.py`) or `pdftotext` |
| PDF (scanned) | TXT | `ocrmypdf` then `pdftotext` |
| HTML | TXT | `trafilatura` (best) or BeautifulSoup |
| DOCX | TXT | `python-docx` (in `extract-text.py`) |
| EPUB / RTF / ODT | TXT | `pandoc` |
| Plain text (any encoding) | UTF-8 TXT | `iconv` |
| CSV/JSONL rows | TXT files | `polars` script |
| TXT | VRT (annotated) | `scripts/annotate.py` (uses spaCy) |
| TXT | CoNLL-U | `stanza` |
| Audio/video | TXT | speech-to-text skill |
