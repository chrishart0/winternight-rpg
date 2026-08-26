# Template strategy

Phase 0 intentionally does not copy LT-Maker's bundled sample projects. `build/minimal.ltproj` is constructed from LT prefabs and repository-owned assets on every compile. The generated project itself is the validated minimal template for the Phase 1 adapter.

If a future engine version makes prefab serialization impractical, place only a provenance-audited known-good base under `template/minimal.ltproj` and document the reason and format contract in `EXEC_PLAN.md`.
