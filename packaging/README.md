# Winternight private Linux build

This archive is a private technical proof of concept. Do not redistribute it.

Requirements: Linux, `uv`, and a graphical desktop. Launch with:

```bash
./run.sh
```

Controls: arrow keys move the cursor, `X` confirms, `Z` cancels, and `S` opens
Start/skip functions. The launcher installs the pinned runtime dependencies in
an isolated `uv` environment and works around a pinned LT terrain-panel restore
bug by hiding that optional panel.

The archive contains the generated project, the minimum pinned Lex Talionis
Python runtime used by it, provenance records, known issues, and license notices.
