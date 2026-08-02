#!/bin/bash
# Uncle Frappe AI Generation Platform — optional local-backend installer.
#
# Installs the optional Python packages that unlock keyless local backends:
# embeddings, Piper TTS, faster-whisper STT, Helsinki translation,
# Real-ESRGAN upscaling, rembg background removal, OCR helpers, documents.
#
# Usage:
#   bash scripts/install-optional.sh                # install all groups
#   bash scripts/install-optional.sh --group NAME   # install one group
#   bash scripts/install-optional.sh --groups A,B   # install several groups
#   bash scripts/install-optional.sh --dry-run      # show what would install
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQ="$ROOT/optional_requirements.txt"
DRY_RUN=0
SELECTED=""

usage() {
    echo "Usage: $0 [--group NAME] [--groups A,B] [--dry-run]"
    echo "Groups: embeddings, speech, translation, upscaling, background_removal, ocr, documents, search"
    exit 0
}

# map group name -> requirement lines (everything below the group comment)
group_lines() {
    local wanted="$1"
    awk -v w="$wanted" '
        /^# Group: / { group = $3; next }
        /^#/ || /^$/ { next }
        { if (group == w) print }
    ' "$REQ"
}

# default: every requirement line
all_lines() {
    awk '/^#/ || /^$/ { next } { print }' "$REQ"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --group) SELECTED="$2"; shift 2 ;;
        --groups) SELECTED="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --help|-h) usage ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

if [ -n "$SELECTED" ]; then
    BACKENDS=(${SELECTED//,/ })
    LINES=""
    for g in "${BACKENDS[@]}"; do
        g="${g// /_}"
        part="$(group_lines "$g")"
        if [ -z "$part" ]; then
            echo "Unknown group: $g" >&2
            usage
        fi
        LINES="$LINES
$part"
    done
    REQS="$(echo "$LINES" | sed '/^$/d' | sort -u)"
    echo "Installing optional group(s): ${BACKENDS[*]}"
else
    REQS="$(all_lines "$REQ")"
    echo "Installing all optional local-backend dependencies"
fi

if [ "$DRY_RUN" = "1" ]; then
    echo "Dry run — would install:"
    echo "$REQS"
    exit 0
fi

echo "$REQS" > /tmp/acos-optional-reqs.txt
pip install -r /tmp/acos-optional-reqs.txt
rm -f /tmp/acos-optional-reqs.txt

echo ""
echo "Optional backends installed. Verify with:"
echo "  python -m ai_generation.cli local-backends"
echo "  python scripts/verify_generation.py"
