# corpus-tools-skill

**Draft, untested — testers welcome.**

A Claude Code / Claude Desktop skill that sets up and operates a local corpus-linguistics toolchain on macOS Apple Silicon — Python (NLTK, spaCy, Stanza), the IMS Open Corpus Workbench (CWB / `cwb-encode` / `cqp`), OPUS for parallel corpora, and helpers for building, annotating, and querying corpora compiled from raw text files, PDFs, HTML, or DOCX.

## Status

This skill is a first draft generated from research on the state of agent / MCP tooling for linguistic research. **It has not been end-to-end tested yet.** Specifically:

- `scripts/setup-python-env.sh` has been logically reviewed but not run against a fresh `uv` install on a clean machine.
- `scripts/setup-cwb.sh` assumes a Homebrew formula `cwb` exists; this needs verification on current Homebrew (a third-party tap may be required).
- `scripts/extract-text.py`, `scripts/concordance.py`, and `scripts/annotate.py` parse cleanly and have been argument-tested but have not been run against real corpora end-to-end.
- `scripts/build-cwb-corpus.sh` follows the documented `cwb-encode` / `cwb-make` invocation but has not been exercised against real `.vrt` data.
- The parallel-corpus workflow in `references/parallel-corpora.md` is built from the documented OPUS / hunalign / `cwb-align-encode` pipeline but the integration has not been smoke-tested.

**If you want to help test, please:**

1. Try `scripts/setup-python-env.sh ./corpus-test` on your platform and report what fails.
2. Try `scripts/setup-cwb.sh` and report whether `brew install cwb` works directly or needs a tap.
3. Try the full corpus-build pipeline (`extract-text.py` → `annotate.py` → `build-cwb-corpus.sh`) on a small directory of test files.
4. Open issues for anything that surprises you — wrong package names, missing dependencies, broken Homebrew formulas, encoding issues, performance gotchas.
5. PRs welcome, especially: Linux support for the bash scripts, clean handling of Apple Silicon MPS in spaCy transformer models, additional language coverage in `setup-python-env.sh`.

This is a personal skill repo by [@techczech](https://github.com/techczech) (Dominik Lukeš); no warranty, MIT-licensed.

## What this skill does

Once installed in your Claude environment, the skill triggers when you mention setting up NLTK / spaCy / Stanza, installing CWB, building a local corpus from raw files, tokenizing / POS-tagging / lemmatizing, running concordances or keyword statistics over local data, or working with parallel corpora outside Sketch Engine.

It covers two layers:

1. **Python ecosystem** — NLTK, spaCy, Stanza in a `uv`-managed virtualenv. Best for: corpus building from messy sources, ad-hoc analysis, smaller corpora.
2. **CWB (IMS Open Corpus Workbench)** — `cwb-encode`, `cwb-make`, `cqp`. Best for: serious concordancing at scale, CQL queries, durable indexed corpora.

It also provides a CLI replacement for [ParaConc](http://paraconc.com/)'s parallel-concordancing workflow, since no MCP server for parallel corpora exists at the time of writing.

## Requirements

- macOS on Apple Silicon (the scripts assume Homebrew; Linux is untested).
- Python 3.10+ and [`uv`](https://docs.astral.sh/uv/).
- Homebrew, for the IMS Open Corpus Workbench.
- No accounts, API keys or paid services. Allow a few GB of disk for spaCy/Stanza models and corpora; transformer models want 8 GB or more of RAM.

## Install

```bash
git clone https://github.com/techczech/corpus-tools-skill ~/.claude/skills/corpus-tools-skill
```

For Codex, clone into `~/.codex/skills/corpus-tools-skill` instead. Then run `scripts/setup-python-env.sh` and `scripts/setup-cwb.sh` as needed.

## Layout

```
SKILL.md                        # the skill definition Claude reads
scripts/
  setup-python-env.sh           # uv venv + NLTK/spaCy/Stanza + standard data
  setup-cwb.sh                  # Homebrew install of IMS CWB
  extract-text.py               # PDF/HTML/DOCX/TXT → UTF-8 text, recursive
  concordance.py                # KWIC concordance over a directory of .txt files
  annotate.py                   # spaCy → vertical-text (.vrt) for cwb-encode
  build-cwb-corpus.sh           # cwb-encode + cwb-make + register in one shot
references/
  nltk-recipes.md               # tokenize, frequency, concordance, collocations, lemmas
  spacy-recipes.md              # batch annotation, log-likelihood keywords, dependency matching
  cwb-cheatsheet.md             # CWB CLI tools and CQL syntax inside cqp
  file-formats.md               # PDF/HTML/DOCX/EPUB conversion + encoding gotchas
  parallel-corpora.md           # ParaConc-replacement workflow with OPUS + CWB
```

## Background

The skill follows the code-generation pattern (Klemen et al. 2025) rather than a custom NLTK MCP server, because no MCP wrapper exists for parallel corpora or general NLTK / Python NLP work.

Sister skill: [`sketchengine-skill`](https://github.com/techczech/sketchengine-skill) — for cloud-hosted Sketch Engine corpora via the `ricCap/sketch-engine-mcp-server` MCP.

## License

MIT.
