# spaCy / Stanza recipes for corpus work

spaCy is the default for English and major European languages. Stanza covers more languages (including Czech, Russian, classical Greek, etc.) and produces UD-style output.

## Pick a model

| Use case | Model | Cost |
|---|---|---|
| Default English, fast | `en_core_web_sm` (~12 MB) | Cheap; CPU-friendly |
| English, higher quality | `en_core_web_md` / `en_core_web_lg` (~50–600 MB) | Larger word vectors |
| English, best quality | `en_core_web_trf` (~440 MB; transformer) | ~10× slower; uses MPS on Apple Silicon |
| Other major European languages | `de_core_news_sm`, `fr_core_news_sm`, etc. | Same pattern |
| Czech, Polish, Hungarian, Russian, ancient languages | Stanza | Slower; broader coverage |

`setup-python-env.sh` installs `en_core_web_sm` by default. Pass `--lang de` etc. for more.

## Batch-annotate a directory

The `scripts/annotate.py` in this skill writes vertical text (`.vrt`) per source file. For a quick programmatic pass over a corpus:

```python
import spacy
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
for path in dir.rglob("*.txt"):
    text = path.read_text(encoding="utf-8", errors="replace")
    doc = nlp(text)
    # do something
```

For larger corpora, use `nlp.pipe` with batching:

```python
texts = (p.read_text(encoding="utf-8", errors="replace") for p in dir.rglob("*.txt"))
for doc in nlp.pipe(texts, batch_size=200, n_process=4):
    ...
```

`n_process` parallelises across CPU cores; useful on Apple Silicon with the small model. Doesn't help with the transformer model — that one is GPU/MPS bound.

## Lemmatised frequency list

```python
from collections import Counter
counts = Counter()
for doc in nlp.pipe(texts, batch_size=200):
    for tok in doc:
        if tok.is_alpha and not tok.is_stop:
            counts[(tok.lemma_.lower(), tok.pos_)] += 1
counts.most_common(50)
```

## POS-filtered keyword extraction

```python
import math
from collections import Counter

def freqs(texts, nlp, pos):
    c = Counter()
    for doc in nlp.pipe(texts, batch_size=200):
        for t in doc:
            if t.pos_ == pos and t.is_alpha:
                c[t.lemma_.lower()] += 1
    return c

target = freqs(target_texts, nlp, "NOUN")
ref    = freqs(ref_texts, nlp, "NOUN")
N_t, N_r = sum(target.values()), sum(ref.values())

def log_likelihood(o1, o2, n1, n2):
    e1 = n1 * (o1 + o2) / (n1 + n2)
    e2 = n2 * (o1 + o2) / (n1 + n2)
    g2 = 0
    if o1 > 0 and e1 > 0: g2 += 2 * o1 * math.log(o1 / e1)
    if o2 > 0 and e2 > 0: g2 += 2 * o2 * math.log(o2 / e2)
    return g2

keywords = []
for w, c in target.items():
    if c < 5:
        continue
    g2 = log_likelihood(c, ref.get(w, 0), N_t, N_r)
    keywords.append((w, c, ref.get(w, 0), g2))
keywords.sort(key=lambda x: -x[3])
```

## Dependency-pattern matching (Matcher and DependencyMatcher)

For classic CQL-style "find passive-voice constructions" — spaCy has `Matcher` (token-level) and `DependencyMatcher` (subtree-level):

```python
from spacy.matcher import Matcher
nlp = spacy.load("en_core_web_sm")
m = Matcher(nlp.vocab)
# Passive voice: be + past participle
m.add("PASSIVE", [[
    {"LEMMA": "be"},
    {"TAG": "RB", "OP": "*"},
    {"TAG": "VBN"},
]])
for doc in nlp.pipe(texts, batch_size=200):
    for mid, start, end in m(doc):
        print(doc[start:end].text)
```

For dependency-relation patterns (e.g. "find verbs whose direct object is `decision`"):

```python
from spacy.matcher import DependencyMatcher
dm = DependencyMatcher(nlp.vocab)
dm.add("MAKE_DECISION", [[
    {"RIGHT_ID": "verb", "RIGHT_ATTRS": {"POS": "VERB"}},
    {"LEFT_ID": "verb", "REL_OP": ">", "RIGHT_ID": "obj",
     "RIGHT_ATTRS": {"DEP": "dobj", "LEMMA": "decision"}},
]])
```

## Stanza for languages spaCy doesn't cover well

```python
import stanza
stanza.download("cs")  # Czech, one-off
nlp = stanza.Pipeline(lang="cs", processors="tokenize,pos,lemma,depparse")
doc = nlp("Tohle je první věta. A tohle je druhá.")
for sent in doc.sentences:
    for tok in sent.tokens:
        for word in tok.words:
            print(word.text, word.lemma, word.upos, word.feats, word.deprel)
```

Stanza output is UD-flavoured — closer to treebank conventions than spaCy. Use Stanza when CoNLL-U output is the goal.

## Going to/from CoNLL-U

Stanza outputs CoNLL-U directly:

```python
from stanza.utils.conll import CoNLL
CoNLL.write_doc2conll(doc, "out.conllu")
```

For consuming UD treebanks (or talking to UDagent-style tools), `udapi` is the standard library:

```python
import udapi
udapi.Document("data.conllu")
```

## Common pitfalls

- spaCy's `parser` and `ner` are slow. Disable with `disable=["parser", "ner"]` if you only need POS + lemmas
- Large documents overflow the default 1M-character limit. `nlp.max_length = 5_000_000` to widen, but consider sentence-splitting first
- The `tok.text` attribute does not include trailing whitespace; use `tok.text_with_ws` if you need to round-trip
- `tok.pos_` is universal POS (NOUN, VERB, ...); `tok.tag_` is the language-specific fine-grained tag (Penn Treebank for English). Pick one and be consistent
- spaCy's `is_stop` uses a built-in stoplist that's small. For real stopword work, use a curated list

## Performance reference, Apple Silicon M-series

- `en_core_web_sm` + 4 processes: ~50k tokens/sec
- `en_core_web_lg` + 4 processes: ~20k tokens/sec
- `en_core_web_trf` (MPS): ~5k tokens/sec
- Stanza (cs, default): ~3k tokens/sec
