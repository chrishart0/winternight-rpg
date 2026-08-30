# Fun improvement plan

Agreed inputs: `docs/qa/fun-review.md` (per-mission verdicts and 18 ranked
recommendations, all contract-aware), the banked design rules in
`.agents/skills/fe-map-design/references/fun-review-learnings.md`, the healing
design dossier (HealingScout, 2026-08-28), and two owner directives: give
Moiraine a weak healing spell, and add Nynaeve to the wn02 defense as a healer
introduced tutorial-style (guided first move: heal Haral Luhhan; she may start
in the inn).

## Governing principle (empirically earned)

**Optional content must change the next tactical state.** Every chapter gets one
small, visible mechanical payoff for its optional material. Speed vs
preparation, safety vs story, mastery that shows — no filler enemies, no canon
contradiction.

## Workstream A — compiler/vocabulary (prerequisites)

A1. **Healing range emission.** `_components()` healing branch
    (`campaign_lt_adapter.py:88-123`) currently emits no range components, so
    every healing item is SELF-ONLY in the pinned engine
    (`item_funcs.get_range` -> {0}). Emit `min_range`/`max_range` from the
    existing ItemDefinition fields (`models.py:228-236`). This is a latent
    defect fix and a hard prerequisite for Nynaeve healing Luhhan.
A2. **`healing_spell` item kind.** Emits `spell` (Spells menu, no counter/
    double) + `target_ally` + `heal` + `min_range`/`max_range` + `uses`;
    optional `heal_exp` component (requires the four heal exp constants) and
    optional `weapon_type: Magic` for wexp. Omit weapon_type gate on items any
    class may use.
A3. **Scripted-forecast lesson vocabulary** (for the wn00 raven, fun-review P
    rec 3): a narrow addition that stages one guided target-select/confirm
    interaction against a harmless scripted target with a forced authored
    outcome, then removes the target. No damage, no enemy.
A4. Regression tests for A1-A3 in the compile-to-tmp pattern; runtime probe
    evidence per the c4-spike method.

## Workstream B — healing feature (owner directive)

B1. **Moiraine: weak heal spell.** New `healing_spell` item, e.g. id
    `mending_weave` ("a limited weave that knits battle wounds — nothing like
    true Healing"), heal ~7, range 1-2, 2-3 uses, added to Moiraine's
    starting_items in `source/characters.yaml`. Lore guardrail: description and
    any scene reference must read as battle mending, never the deep Healing
    reserved for wn05 (`canon_bible` scope fact: ordinary help cannot cure
    Tam's fever).
B2. **Nynaeve joins wn02 as healer.**
    - Unit entry in `village_defense.yaml`: team player, start inside the inn
      region. Nynaeve is mortal as a playable unit; death offers Restart or
      Continue, and continuing keeps her story portraits while removing her
      from later playable deployment.
    - Keep her `village_wisdom` class. Healing Herbs use the top-level Staff
      action, heal the user or an adjacent ally at range 0–1, and do not scale
      from magic.
    - **Tutorial introduction (guided, not forced):** Nynaeve's Talk recruits
      Egwene, then one stable narration card says "Move Nynaeve beside Haral.
      Staff: Healing Herbs." A `combat_end` trigger confirms the player-performed
      heal and plays the Haral/Nynaeve exchange. Haral starts at 28/40, so the
      action is legal on turn 1.
    - Scene work: brief Bran-account framing line acknowledging the Wisdom
      working through the night (canon-consistent: she and Egwene tended the
      wounded); combat-quote/heal bark for Nynaeve.
B3. **Balance re-check (mandatory).** The wn02 rebalance margins were Lan
    31-40 / Moiraine 24-31 / Haral 12-15 at turn 7. Adding up to ~24 healed HP
    (Nynaeve) + Moiraine's weave shifts difficulty down. Compensate to keep
    tension (options: Nynaeve heal 6 x2 uses; +1 STR on late waves; or accept
    the flank-wave-earlier change from B-wn02 below as the offset). Re-run the
    worst-case table for every mandatory unit and two real-input golden runs.
B4. Routing/verification: add nynaeve to `input_playthrough.py` wn02 priority
    (after civilians) with a heal intent; extend the wn02 smoke truth table
    (`nynaeve_protected`, guided-heal event fired).

## Workstream C — per-mission fun improvements

From `docs/qa/fun-review.md` (file/line anchors and locked contracts are in
the review; implement as written unless it conflicts with B):

- **wn00 (FLAT -> target FUN):** (1) optional Talks as route-planning choices
  between cart and cellar; (2) compress cask geometry one tile; (3) raven
  becomes the guided input lesson via A3.
- **wn01:** (1) turn-8 mercy win becomes a visible caught LOSS ("Reach
  Westwood" becomes mandatory; Tam's wound stays scripted on the success path
  only — story never proceeds through player failure); (2) pursuit wave turn
  3 -> 2 with east-edge telegraph; (3) trim pre-control 22 pages -> ~16.
- **wn02:** (1) flank wave turn 6 -> 5 with warning (also the natural
  difficulty offset for B3); (2) saved-home splits the flank (1 unit if
  home_saved, 2 if not); (3) green-survivor acknowledgment page on victory.
  Plus B2 Nynaeve integration.
- **wn03:** (1) make the authored 12-turn cap real (turn-10 fever warning,
  turn-13 loss); (2) Narg kill unlocks a quick west exit (kill = tempo,
  evade = long route); (3) sheep-pen detour grants fog radius 4 + farmhouse
  highlight (information vs speed).
- **wn04:** (1) real hold-still hide decision: two Hide shelter tiles activate
  at rider_halts, `rand_hidden` required at the watch check; sweepers
  do_nothing during the halt, pursue after; (2) sweepers turn 5 -> 4 with
  west-edge bark; (3) show the rider marker before highlighting the watched
  strip.
- **wn05:** (1) Luhhan's Talk grants Tam one assisted extra litter move
  (refresh) — help made mechanical; (2) nonlethal fever barks at turns 4/6/8
  while tam_at_inn is false (never lose); (3) both-Talks callback narration
  before the any-price scene.

## Locked contracts (unchanged)

Six green allies with mortal protected Luhhan; Tam's scripted wound; the
non-combat column/rider; zero-enemy wn05 with no hard timeout; scripted raven
misses with no combat; boundary scenes; fair turn-start reinforcements with
telegraphs; the 56-char dialogue and 30/16-char objective budgets; book-text
policy for any new direct-beat dialogue.

## Sequencing

1. **Wave G1:** Workstream A (compiler) alone — everything downstream depends
   on it.
2. **Wave G2 (parallel, disjoint owners):** wn00+wn01 owner; wn02 owner
   (B2-B4 + C-wn02); wn03 owner; wn04+wn05 owner. Each verifies on /tmp
   compiles with real-input probes; no repo make.
3. **Gate:** orchestrator `make check`.
4. **Wave G3:** QA fun re-review (dual-run per changed mission, dead-turn
   ratios recomputed, verdict target: no chapter below MOSTLY FUN, wn00 and
   wn02 target FUN) + regression QA on loss paths. Fix loop as needed.
5. EXEC_PLAN evidence update.

## Risks

- wn01 timeout flip changes smoke truth tables (`turn_eight_forces_wound`)
  and the automated player's stall assumptions — the wn01 owner must update
  `smoke.py`/`input_playthrough.py` expectations with the mission change.
- wn02 difficulty is a three-body problem (healer in, flank earlier, home
  branch) — B3's math table and two golden runs are the gate.
- wn04 hide shelters change the golden route — update wn04 routing and truth
  tables together.
- A3 is the only genuinely new engine-facing mechanism; spike it first inside
  Wave G1 with a /tmp runtime proof before wn00 depends on it.
