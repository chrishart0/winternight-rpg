---
name: lex-talionis-author
description: Compile validated repository specifications into a project for the exact LT-Maker commit in engine.lock. Use for LT serialization, resources, events, levels, engine launch, or adapter investigation; do not hand-edit generated build files.
---

# Lex Talionis Author

Read `engine.lock`, `AGENTS.md`, and [references/adapter-contract.md](references/adapter-contract.md). Use `uv run --python 3.11` and the pinned submodule. Prefer LT prefabs, serializers, loaders, parsers, and validation APIs; isolate unavoidable format details inside `src/winternight_gen/lt_adapter.py`.

Compile only into a fresh build directory. Refuse to compile while the repository editor lock is present. Never modify `vendor/lt-maker` without an approved patch record. Verify with `$game-verifier`; do not infer playability from serialization success.

Run scripts in this skill only when they provide a maintained wrapper around repository commands; compiler logic belongs in `src/winternight_gen`.
