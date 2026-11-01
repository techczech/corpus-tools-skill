---
name: corpus-tools-skill
description: "Use to set up and run a local corpus toolchain (NLTK, spaCy, Stanza, CWB) on macOS: build corpora from PDF/HTML/DOCX, concordances, keywords. Not Sketch Engine."
---

# Corpus Tools Skill

A pragmatic toolchain for compiling, annotating, and querying corpora locally on macOS Apple Silicon. Two layers:

1. **Python ecosystem** — NLTK, spaCy, Stanza in a `uv`-managed virtualenv. Best for: corpus building from messy sources, annotation, ad-hoc analysis
2. **CWB (IMS Open Corpus Workbench)** — `cwb-encode`, `cwb-make`, `cqp`. Best for: serious concordancing at scale, CQL queries, durable indexed corpora

Pick the layer that matches the task: Python for one-off scripts and analysis, CWB for repeated structured queries over a stable corpus.

## Setup

### Python environment

```bash
bash scripts/setup-python-env.sh /path/to/project
```

Creates a `.venv/` in the project, installs NLTK + spaCy + Stanza + helpers (pdftotext, beautifulsoup4, lxml, tqdm, polars), downloads the standard NLTK datasets (`punkt`, `stopwords`, `wordnet`, `averaged_perceptron_tagger`), and installs the spaCy `en_core_web_sm` model. Add languages by passing `--lang de --lang fr` etc.

The script uses `uv` (per the user's global AGENTS.md). If `uv` is not installed, it errors clearly.

### CWB (IMS Open Corpus Workbench)

```bash
bash scripts/setup-cwb.sh
```

Installs CWB via Homebrew (`brew install cwb`) and verifies the tools are on PATH. Sets up a default registry at `~/.local/share/cwb/registry` and a data directory at `~/.local/share/cwb/data`.

### OPUS tools (parallel corpora)

OPUS tools are pip-installable via the same Python environment. The setup script handles this if you pass `--opus`:

```bash
bash scripts/setup-python-env.sh /path/to/project --opus
```

This installs `opustools` and `opusfilter`. See [`references/parallel-corpora.md`](references/parallel-corpora.md) for ParaConc-style workflows.

## Building a corpus from raw sources

Most user starting points are messy: a directory of PDFs, a folder of scraped HTML, a backup of DOCX files. The pipeline:

1. **Extract text** — `scripts/extract-text.py` recursively converts PDF / HTML / DOCX / TXT into a flat directory of UTF-8 `.txt` files, one per source. Preserves filename for traceability
2. **Inspect** — eyeball a sample for OCR errors, layout artifacts, encoding issues. Cheap to fix early
3. **Annotate** — `scripts/annotate.py` runs spaCy or Stanza over the extracted text and writes CoNLL-U or vertical (TSV) format
4. **Index** — for CWB use, `scripts/build-cwb-corpus.sh` runs `cwb-encode`, `cwb-make`, and registers the corpus

For the file-format conversion options the extract step relies on, see [`references/file-formats.md`](references/file-formats.md).

## Querying

### Quick concordance over plain text

```bash
python scripts/concordance.py --dir /path/to/texts --query "literally" --window 7
```

In-memory regex/word-boundary concordance over a directory of `.txt` files. Good enough for sub-million-token corpora and quick exploration. For more, see [`references/nltk-recipes.md`](references/nltk-recipes.md) — covers `nltk.Text.concordance`, dispersion plots, frequency distributions, and bigram collocations.

### CQL queries against a CWB corpus

Once `build-cwb-corpus.sh` has indexed the data, `cqp` is the CLI:

```bash
cqp -eC
> MYCORPUS;
> [lemma="literally"] within <s/>;
> count by lemma;
```

For the syntax cheatsheet, see [`references/cwb-cheatsheet.md`](references/cwb-cheatsheet.md). For Python wrappers around CQP, see [`references/nltk-recipes.md`](references/nltk-recipes.md) (the `cwb-python` package).

### spaCy / Stanza for annotated data

For finer-grained annotation (dependency parses, NER, custom pipelines), use spaCy or Stanza directly. See [`references/spacy-recipes.md`](references/spacy-recipes.md) for the patterns that come up most: lemmatised frequency lists, POS-filtered keyword extraction, dependency-pattern matching, batch annotation of large corpora with `nlp.pipe`.

## Frequency, keyword, collocation analysis

The bundled `scripts/concordance.py` gives KWIC lines for small to medium corpora:

```bash
python scripts/concordance.py --dir /path/to/texts --query "research" --window 7 --max 50
```

There are no bundled scripts for frequency lists, keywords or collocations. Write them from the recipes in [`references/nltk-recipes.md`](references/nltk-recipes.md) (frequency, collocations) and [`references/spacy-recipes.md`](references/spacy-recipes.md) (POS-filtered frequency, log-likelihood keywords).

For larger corpora (>10M tokens), use CWB — it handles indexed access far better than re-scanning text files.

## Parallel corpora — the ParaConc-style workflow

There is no MCP server for parallel corpora at the time of writing. The local-CLI path:

1. **Source data**: OPUS (`opus_get`), Europarl, OpenSubtitles, etc. — see [`references/parallel-corpora.md`](references/parallel-corpora.md)
2. **Filter**: `opusfilter` — language detection, length ratios, deduplication
3. **Align (if needed)**: `hunalign` or `bleualign` for unaligned bitexts
4. **Encode as a parallel CWB corpus** with aligned `<s>` boundaries and metadata
5. **Query**: `cqp` with parallel-corpus syntax (`align`, paired sentences)

See [`references/parallel-corpora.md`](references/parallel-corpora.md) for the full recipe.

## Troubleshooting

- **NLTK download fails** — `python -c "import ssl; ssl._create_default_https_context = ssl._create_unverified_context; import nltk; nltk.download('punkt')"` is the corporate-network workaround
- **spaCy model not found** — `python -m spacy download en_core_web_sm` (or `en_core_web_trf` for transformer-quality at ~10x cost)
- **CWB `cwb-encode` complains about UTF-8** — the input file must be vertical text (one token per line) with proper UTF-8; the extract → annotate steps produce this
- **Memory blowups on large corpora** — Python in-memory tools fail above ~5M tokens. CWB is the right answer at scale
- **Apple Silicon vs spaCy transformer models** — the `en_core_web_trf` model uses PyTorch; install with MPS support: `uv pip install torch` (defaults to MPS on Apple Silicon)

## Out of scope

- Cloud corpus services (Sketch Engine specifically) — see sketchengine-skill
- Treebank-specific tooling (Universal Dependencies querying) — `udapi` is mentioned in `references/spacy-recipes.md` but full UD workflows would be a separate skill
- LLM-mediated corpus inquiry — that's a research-methodology question, not a tooling question.
