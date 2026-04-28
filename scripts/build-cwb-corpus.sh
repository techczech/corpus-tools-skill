#!/usr/bin/env bash
# Encode a directory of vertical-text (.vrt) files as a CWB corpus, run cwb-make,
# and register it.
#
# Usage:
#   bash build-cwb-corpus.sh --id MYCORPUS --vrt-dir /path/to/vrt
#   bash build-cwb-corpus.sh --id MYCORPUS --vrt-dir ./vrt --registry ~/.local/share/cwb/registry --data ~/.local/share/cwb/data

set -euo pipefail

corpus_id=""
vrt_dir=""
registry="${CORPUS_REGISTRY:-$HOME/.local/share/cwb/registry}"
data_root="$HOME/.local/share/cwb/data"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --id)       corpus_id="$2"; shift 2 ;;
    --vrt-dir)  vrt_dir="$2"; shift 2 ;;
    --registry) registry="$2"; shift 2 ;;
    --data)     data_root="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$corpus_id" || -z "$vrt_dir" ]]; then
  echo "Usage: $0 --id CORPUS_ID --vrt-dir /path/to/vrt [--registry ...] [--data ...]" >&2
  exit 1
fi

if ! command -v cwb-encode >/dev/null 2>&1; then
  echo "Error: cwb-encode not found. Run setup-cwb.sh first." >&2
  exit 1
fi

# Lowercase for paths; uppercase for corpus id
id_lc="$(echo "$corpus_id" | tr '[:upper:]' '[:lower:]')"
id_uc="$(echo "$corpus_id" | tr '[:lower:]' '[:upper:]')"

corpus_data="$data_root/$id_lc"
mkdir -p "$corpus_data" "$registry"

echo "Encoding $id_uc from $vrt_dir into $corpus_data ..."
# -d: data dir, -F: input dir of .vrt files, -R: registry file, -c: charset
# Positional attributes: word lemma pos tag
# Structural attributes: <text id> <s>
cwb-encode \
  -d "$corpus_data" \
  -F "$vrt_dir" \
  -R "$registry/$id_lc" \
  -c utf8 \
  -P lemma -P pos -P tag \
  -S text:0+id \
  -S s

echo "Building lexicon and indices with cwb-make ..."
# CORPUS_REGISTRY env var must include this registry dir for cwb-make to find it
CORPUS_REGISTRY="$registry" cwb-make -V "$id_uc"

echo
echo "Corpus $id_uc indexed."
echo
echo "Try a query:"
echo "  CORPUS_REGISTRY='$registry' cqp -eC"
echo "  > $id_uc;"
echo "  > [lemma=\"literally\"];"
echo "  > cat;"
