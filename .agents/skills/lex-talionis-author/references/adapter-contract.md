# LT adapter contract

- Upstream: `https://gitlab.com/rainlash/lt-maker.git` at the exact `engine.lock` commit.
- Runtime: CPython 3.11.
- Input: validated, versioned repository specifications and approved assets.
- Output: a newly created `.ltproj` with deterministic project bytes.
- Engine-owned checks: resource/database loading, event parsing, validation APIs, and level initialization.
- Repository-owned checks: schema, IDs, references, hashes, file inventory, provenance, and deterministic comparison.

Direct serialized fields require a contract test against the pinned engine. Record unsupported APIs or engine patches in `EXEC_PLAN.md`.
