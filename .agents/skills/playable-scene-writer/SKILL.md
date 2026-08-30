---
name: playable-scene-writer
description: Write playable scene dialogue and narration from approved beats for a first-time player. Use when authoring or rewriting design/scenes YAML, tightening character voice, fixing entry orientation, combat quotes, or pickup lines; do not extract canon beats or design missions.
---

# Playable Scene Writer

Turn approved beat IDs into playable talk. Beats, status, and locators stay in `narrative-adapter`. Objectives, maps, and turn counts stay in `tactical-mission-designer`. Coherence of goal-to-action stays in `mission-coherence`.

Follow `AGENTS.md`, the ending boundary in `source/canon_bible.yaml`, and [references/scene-card.md](references/scene-card.md) before changing a scene.

## Write each scene as one job

Keep scene IDs. For every scene, the last A-press must leave the player able to answer:

1. Who is this, in relationship words?
2. Where are we, in words that match the visible background or map?
3. What does someone want right now?
4. What changed?
5. What do I do next?

Quote the actual book text from `source/private/eotw/` for every direct beat: pick the strongest lines, trim to box limits, and invent connective lines only where the book gives none. When a quotation exceeds the box budget, split it at natural pauses into consecutive boxes with the same speaker and portrait. Every resulting box must be a contiguous verbatim subsequence of the source quotation; never reword quoted text. Inferred and invented beats get original lines in the same voice. If a quoted line only works with novel context the player lacks, add an orienting line around it rather than replacing it.

## Constraints that do not move

- Respect the ending boundary in `source/canon_bible.yaml`; do not write past its final scene.
- Dialogue and narration: at most 56 characters per text box. This conservative budget comes from the pinned engine's native 240x160, portrait-backed, two-row `speak` box: representative prose fit at 56 characters and first auto-scrolled at 57.
- Illegal in strings: `; { } #` and raw newlines.
- Combat quotes and item pickups are first-class lines, not captions.
- UI teaching may be narration. Do not put menu verbs in a character's mouth unless that character is teaching a physical task.
- Preserve test-locked contracts: `sc_c0_quarry_road` compiles to exactly eight `speak;` commands, Rand Right / Tam Left, no Close/Open transitions; delivery narration keeps `Optional`, `Item`, and `Equip`; Tam's opening handoff keeps `Find Mat on the Green`.

## Voice

Each named speaker must fail a swap-test: if the line could be anyone's, rewrite it from `source/characters.yaml`. Do not stack three portraits on one side. Prefer questions over explanations. Do not invent maps, missions, or engine patches to fix prose.

After content changes, run `make check`. Do not edit `build/`.
