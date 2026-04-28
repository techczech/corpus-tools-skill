# IMS Open Corpus Workbench — CLI cheatsheet

CWB is a 30-year-old C toolchain for managing and querying linguistically-annotated corpora at scale. Mature, fast, durable, and the de facto standard for academic corpus linguistics under the hood. Sketch Engine, NoSketch Engine, KonText, #LancsBox X, and the Yu et al. agent-driven framework all sit on top of CWB or its CQP query language.

## The toolchain

| Tool | Purpose |
|---|---|
| `cwb-encode` | Index a vertical-text (`.vrt`) corpus into binary form |
| `cwb-make` | Build the lexicon and indexes after encoding |
| `cwb-describe-corpus` | Print metadata about an indexed corpus |
| `cwb-decode` | Dump an indexed corpus back to vertical text |
| `cqp` | Interactive Corpus Query Processor (the query CLI) |
| `cwb-scan-corpus` | Generate frequency tables over indexed corpora |
| `cwb-align-encode` | Encode parallel-corpus alignments |

## Configuring registry path

CWB looks up corpora by name in a registry directory:

```bash
export CORPUS_REGISTRY="$HOME/.local/share/cwb/registry"
```

The `setup-cwb.sh` script in this skill creates this directory and points to it. After encoding, the corpus's registry file lives at `$CORPUS_REGISTRY/<corpus-id-lowercase>`.

## Encoding a vertical-text corpus

`scripts/build-cwb-corpus.sh` wraps this. Manual invocation:

```bash
cwb-encode \
  -d $DATA_DIR/mycorpus \
  -F /path/to/vrt \
  -R $CORPUS_REGISTRY/mycorpus \
  -c utf8 \
  -P lemma -P pos -P tag \
  -S text:0+id \
  -S s
```

- `-P` declares positional attributes (token-level; `word` is implicit)
- `-S` declares structural attributes (XML-like elements). `text:0+id` means a `<text>` element with depth 0 and an `id` attribute
- `-c utf8` for character set
- `-F dir` reads all `.vrt` files under that directory in alphanumeric order

Then build the indexes:

```bash
cwb-make -V MYCORPUS
```

`-V` is "verbose"; `cwb-make` builds the lexicon, frequency table, and inverted index for each positional attribute. Indexing scales linearly; a 100M-token corpus takes a few minutes on Apple Silicon.

## Querying interactively with `cqp`

```bash
cqp -eC
```

`-e` enables readline editing; `-C` gives colourised KWIC output.

```cqp
> MYCORPUS;
MYCORPUS> [lemma="literally"];
MYCORPUS> cat;                       # show concordance lines
MYCORPUS> count by lemma;            # frequency by lemma of matched tokens
MYCORPUS> show +pos;                 # add POS column to KWIC
MYCORPUS> set Context 5;             # widen context to 5 tokens each side
```

CQL syntax inside `cqp` is the same as Sketch Engine — see the sketchengine-skill's `cql.md` for patterns.

### Saving and naming queries

```cqp
PASSIVES = [lemma="be"] [pos="RB.*"]{0,3} [pos="V.N"];
PASSIVES;
cat PASSIVES;
```

### Subcorpus filtering

```cqp
MYCORPUS> Q1 = [lemma="literally"];
MYCORPUS> Q1 expand to s;            # expand each match to its sentence
MYCORPUS> Q1 = Q1 :: match.text_id="article42";  # restrict to a specific text
```

### Frequency statistics

```cqp
> count Q1 by lemma %c;              # case-insensitive count by lemma
> group Q1 match[-1] lemma by match lemma;  # group by left-context lemma + match lemma
> save Q1 results.txt;
```

## Useful CLI invocations

### Print all matches to stdout (scriptable)

```bash
echo 'MYCORPUS; [lemma="literally"]; cat;' | cqp -c
```

### Get a frequency list of a positional attribute

```bash
cwb-scan-corpus -o lemma-freq.txt MYCORPUS lemma+0
```

The `+0` is a position offset (0 = current token; -1 = previous, +1 = next). For bigrams of POS:

```bash
cwb-scan-corpus -o pos-bigrams.txt MYCORPUS pos+0 pos+1
```

### Decode a corpus back to vertical text

```bash
cwb-decode MYCORPUS -ALL > mycorpus-decoded.vrt
```

Useful for sharing the source data or re-encoding under a new schema.

## Parallel corpora

Two parallel corpora are encoded separately, each with `<s>` boundaries that include unique sentence IDs. Then `cwb-align-encode` records the pairings:

```bash
# corpus EN with sentence-id attribute
# corpus DE with sentence-id attribute
cwb-align-encode -D -R $CORPUS_REGISTRY/en-de.align en-de.alignments.txt
```

Once aligned, in `cqp`:

```cqp
EN; show match, target;
EN> [lemma="literally"];
EN> show DE;                  # show aligned DE sentences alongside EN matches
```

For full parallel-corpus workflow including OPUS data, see `parallel-corpora.md`.

## Performance and limits

- 100M tokens index in ~2 minutes on M-series; queries return in <1s
- 2-billion-token corpora (Hansard scale) work but indexing takes ~1 hour
- Memory: indexes are mmap'd; even huge corpora open instantly
- No graceful degradation for malformed `.vrt` — fix the input

## When CWB is the wrong tool

- Vector-similarity / semantic search → use sentence-transformers + a vector store
- Natural-language LLM querying without writing CQL → use sketchengine-skill (the MCP wrapper) or build the Yu et al. style three-tool MCP
- Quick exploration of <1M tokens → Python + `scripts/concordance.py` is faster to start with
- Web-served querying → CQPweb is the canonical front-end (built on CWB)

## Reference

- CQP manual: https://cwb.sourceforge.io/files/CQP_Manual/
- CWB encoding tutorial: https://cwb.sourceforge.io/documentation.php
- Yu et al. (2026) — agent-driven CQP via MCP: https://arxiv.org/abs/2604.07189 (and the dossier in `_LEARNINGLOG/linguistics/agent-tools-for-linguists/`)
