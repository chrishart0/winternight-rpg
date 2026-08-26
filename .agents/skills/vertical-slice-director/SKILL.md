---
name: vertical-slice-director
description: Maintain Winternight phase gates, execution evidence, and bounded next actions. Use when starting, resuming, closing, or changing a project phase; do not use it to author narrative, missions, assets, or LT files.
---

# Vertical Slice Director

Read `AGENTS.md` and `EXEC_PLAN.md` first. State the current phase, remaining gate evidence, blockers, and one next bounded action. Update `EXEC_PLAN.md` when evidence or scope state changes.

Do not cross a phase gate because files exist or a command exits successfully. Require the evidence named by the gate. On failure, record the narrow failure and pursue the smallest in-phase fix; do not silently redesign the architecture or expand content scope.

Read [references/phase-gates.md](references/phase-gates.md) when evaluating or changing a gate.
