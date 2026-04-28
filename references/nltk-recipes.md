# NLTK recipes for corpus work

NLTK is fine for small-to-medium corpora and for teaching. For serious work, prefer spaCy or Stanza for annotation and CWB for indexed querying. NLTK's strengths: WordNet, lexical resources, classroom-friendly APIs, easy bigram/trigram collocation.

## Tokenize, sentence-split, POS-tag

```python
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag

text = open("corpus.txt", encoding="utf-8").read()
sents = sent_tokenize(text)
toks = [word_tokenize(s) for s in sents]
tagged = [pos_tag(s) for s in toks]
```

NLTK's POS tagger is slow and noisy. Use spaCy for anything beyond toy work — see `spacy-recipes.md`.

## Frequency distribution

```python
from nltk import FreqDist
fd = FreqDist(tok.lower() for s in toks for tok in s if tok.isalpha())
fd.most_common(50)
```

## Concordance and dispersion plot

```python
from nltk.text import Text
text_obj = Text(sum(toks, []))
text_obj.concordance("literally", lines=30, width=80)
text_obj.dispersion_plot(["literally", "really", "actually"])
text_obj.similar("literally")
```

`Text.concordance` is fine for one-off teaching demos. For programmatic use, our `scripts/concordance.py` is leaner.

## Bigram collocations

```python
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
bam = BigramAssocMeasures()

words = [w.lower() for s in toks for w in s if w.isalpha()]
finder = BigramCollocationFinder.from_words(words)
finder.apply_freq_filter(5)               # min joint count
finder.nbest(bam.likelihood_ratio, 30)   # G²
```

`bam.pmi`, `bam.student_t`, `bam.chi_sq`, `bam.likelihood_ratio` all available. `likelihood_ratio` (G²) is the academic standard. For trigrams: `TrigramCollocationFinder`, `TrigramAssocMeasures`.

## Lemmatization with WordNet

```python
from nltk.stem import WordNetLemmatizer
lem = WordNetLemmatizer()
lem.lemmatize("running", pos="v")  # 'run'
```

WordNet lemmatization is rule-based and limited; spaCy / Stanza are better for general use.

## Word and POS frequency tables in one pass

```python
import polars as pl
rows = []
for sent_toks in tagged:
    for w, p in sent_toks:
        rows.append({"word": w.lower(), "pos": p})
df = pl.DataFrame(rows)
df.group_by(["word", "pos"]).count().sort("count", descending=True).head(50)
```

`polars` is faster than pandas on Apple Silicon for corpus-scale data and worth the switch.

## Connecting NLTK to a CWB corpus

NLTK doesn't speak CWB natively. Two paths:

1. **`cwb-python` (community PyPI package)** — wraps the CWB C library; fastest for repeated queries
2. **Subprocess `cqp`** — slower but no extra deps:

   ```python
   import subprocess
   q = '[lemma="literally"]; cat;'
   res = subprocess.run(
       ["cqp", "-c", "-r", REGISTRY],
       input=f"MYCORPUS;\n{q}\nexit;\n",
       capture_output=True, text=True, check=True,
   )
   print(res.stdout)
   ```

For serious work, write the queries in `cqp` interactively, then automate the ones you keep.

## NLTK gotchas

- `nltk.download()` over institutional networks often hits SSL issues — see SKILL.md troubleshooting
- The default `punkt` tokenizer treats `Mr.` as two tokens. Use `punkt_tab` for newer behaviour, or switch to spaCy
- WordNet is English-only. Multilingual WordNets exist but are partial
- The `Text` class loads everything into memory. Don't use it for >1M tokens

## When NOT to use NLTK

- Multilingual annotation → Stanza
- High-quality English annotation → spaCy
- Indexed corpus access → CWB
- Word embeddings → gensim or sentence-transformers
- Modern transformer-based parsing → spaCy with `en_core_web_trf` or HuggingFace
