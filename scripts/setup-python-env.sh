#!/usr/bin/env bash
# Set up a Python corpus-linguistics environment in a target project directory.
#
# Usage:
#   bash setup-python-env.sh /path/to/project          # core: NLTK, spaCy, Stanza
#   bash setup-python-env.sh /path/to/project --opus   # also install opustools
#   bash setup-python-env.sh /path/to/project --lang de --lang fr   # extra spaCy models

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/project [--opus] [--lang <iso>]..." >&2
  exit 1
fi

project_dir="$1"; shift
install_opus=0
extra_langs=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --opus) install_opus=1; shift ;;
    --lang) extra_langs+=("$2"); shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: 'uv' is required. Install with: brew install uv" >&2
  exit 1
fi

mkdir -p "$project_dir"
cd "$project_dir"

# Create venv if missing
if [[ ! -d .venv ]]; then
  uv venv
fi

# Activate
# shellcheck disable=SC1091
. .venv/bin/activate

echo "Installing core corpus toolkit ..."
uv pip install \
  nltk \
  spacy \
  stanza \
  beautifulsoup4 \
  lxml \
  pdfminer.six \
  python-docx \
  tqdm \
  polars \
  regex

if [[ $install_opus -eq 1 ]]; then
  echo "Installing OPUS tools ..."
  uv pip install opustools opusfilter
fi

# NLTK data
echo "Downloading NLTK data ..."
python - <<'PY'
import nltk, ssl
try:
    _ctx = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _ctx
for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet",
            "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng",
            "universal_tagset"]:
    try:
        nltk.download(pkg, quiet=True)
    except Exception as e:
        print(f"  warn: {pkg}: {e}")
PY

# spaCy models
echo "Downloading spaCy English model (en_core_web_sm) ..."
python -m spacy download en_core_web_sm

for lang in "${extra_langs[@]}"; do
  case "$lang" in
    de) model="de_core_news_sm" ;;
    fr) model="fr_core_news_sm" ;;
    es) model="es_core_news_sm" ;;
    it) model="it_core_news_sm" ;;
    pl) model="pl_core_news_sm" ;;
    nl) model="nl_core_news_sm" ;;
    pt) model="pt_core_news_sm" ;;
    cs) model="" ;; # spaCy has no Czech model — fall back to Stanza below
    *)  model="" ;;
  esac
  if [[ -n "$model" ]]; then
    echo "Downloading spaCy $lang model ($model) ..."
    python -m spacy download "$model"
  else
    echo "No spaCy model for $lang — install via Stanza:"
    echo "  python -c \"import stanza; stanza.download('$lang')\""
  fi
done

cat <<EOF

Done. Environment ready at: $project_dir/.venv

To use:
  cd $project_dir
  source .venv/bin/activate

To verify:
  python -c "import nltk, spacy; print('nltk', nltk.__version__); print('spacy', spacy.__version__)"
EOF
