#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/.venv/bin/article-crawler" \
  --url-file "$SCRIPT_DIR/urls.txt" \
  -o "$SCRIPT_DIR/My Reading List - $(date "+%Y-%m-%-d").epub" \
  -t "My Reading List - $(date "+%-d %B %Y")"
