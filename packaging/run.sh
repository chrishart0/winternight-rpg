#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec uv run --python 3.11 \
  --with pygame-ce==2.3.2 \
  --with typing-extensions==4.8.0 \
  python launch.py
