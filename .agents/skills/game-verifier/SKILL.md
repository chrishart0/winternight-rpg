---
name: game-verifier
description: Verify schemas, cross-references, generated resources, LT loading/event contracts, level initialization, reports, and deterministic builds. Use after content, compiler, adapter, or asset changes; do not modify generated output to make checks pass.
---

# Game Verifier

Run the narrowest relevant check first, then `make check` before closing a phase gate. Validate observable contracts: structured input, stable IDs, asset dimensions/hashes, event triggers and commands, level win/loss/intro/outro references, LT loader compatibility, runtime level initialization, and clean rebuild equality.

Do not mock the LT loader/parser boundary. A headless smoke test is not an interactive playthrough; report that limitation. Write results to the build report and update `EXEC_PLAN.md` only with observed evidence.

Use [scripts/verify.sh](scripts/verify.sh) for the complete Phase 0 verification sequence.
