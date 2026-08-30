# Winternight story plan v2 — Eye of the World Ch1-7

Agreed 2026-08-27. This supersedes the four-chapter scope in `docs/story-pass.md`.
All source locators are `NN:line-line` into `source/private/eotw/` files. Scene text
policy is book-text-first: quote the actual chapter text for every direct beat, trim to
GBA box limits, invent connective lines only where the book gives none (see
`.agents/skills/playable-scene-writer/SKILL.md`).

## Decision record

1. **Boundary removed.** The story runs to the end of Chapter 7: Rand gets Tam to the
   Winespring Inn and Moiraine agrees to heal him. The Ch6 fever speech — Aiel War
   memories, the baby found on Dragonmount, "Light, who am I?" (06:99-105) — is IN
   scope and is the emotional payoff of the night. Delete `forbidden_terms` /
   `excluded_topics` / "end before fever speech" principle and the tests that lock them.
2. **Ch6 is a playable tension mission**, not a cutscene: night litter-drag with a
   scripted hide from the Trolloc column and the returning Myrddraal (06:63-79).
3. **Village defense stays playable** (Lan + Moiraine), reframed by Bran's Ch7
   account (07:135-141) so its framing is book-quoted, not merely inferred.
4. **Six chapters, four unique map layouts** (up from 4/2). Update
   `design/campaign.yaml` constraints accordingly.
5. **Adaptation authority (owner grant, 2026-08-27).** Story-flow changes needed by
   the tactical-RPG format are authorized without further sign-off — reordering,
   interleaving parallel events (e.g. the village battle between the Rand/Tam
   chapters), splitting prose beats into playable legs, and inventing tactical detail.
   Lore is inviolable: no contradiction of canon facts, no invented fates for named
   characters, no new lore claims. Invented and inferred material still carries its
   status in the adaptation ledger.

## Chapter structure

| # | Chapter id | Title | Book | Type |
|---|---|---|---|---|
| P | wn00_festival | An Empty Road | Ch1-4 | Exploration/tutorial map |
| 1 | wn01_winternight | Winternight | Ch5 (to 05:145) | Battle: escape |
| 2 | wn02_village_burns | The Village Burns | inferred night, framed by 07:135-141 | Battle: defend + rescue |
| 3 | wn03_ruined_farm | The Ruined Farm | Ch5 (05:147-233) | Battle: search + duel |
| 4 | wn04_long_road | The Long Road | Ch6 | Battle: stealth escape |
| 5 | wn05_out_of_the_woods | Out of the Woods | Ch7 | Exploration map + ending |

Emotional shape: warmth → rupture → communal cost → lonely responsibility →
endurance with identity shattered → arrival that isn't safety, help with an unnamed price.

Difficulty/teaching ladder (see `.agents/skills/fe-map-design/SKILL.md`):
P move/talk/interact/attack-UI; C1 combat + escape under pressure; C2 multi-unit play
with strong units; C3 terrain, search, first real solo fight; C4 mechanics-light tension
peak; C5 denouement. Combat-heavy maps (2,3) sit mid-campaign.

## Map layouts (4 unique, with narrative-state variants)

| Layout | Variants | Used by |
|---|---|---|
| emonds_field | festival day / burning night / burned dawn | P, C2, C5 |
| althor_farm | evening whole / ruined night | C1, C3 |
| westwood_road | night (mission) / day (Ch1 cutscene background) | C4 |
| bonfire_outskirts | dawn | C5 final leg (may fold into emonds_field burned-dawn if the layout budget bites) |

## Chapter plans

### P — An Empty Road (Ch1-4)

Cutscenes: Quarry Road opening; the rider whose cloak does not move; Tam's
"flame and the void" (01:27-67). Fain's arrival and war news as Green-crowd scenes
(Ch3; public spectacle at 03:35-117 vs private dread 03:133-159 — see scene index in
`agent://IdxCh34`). Thom's entrance and performance (04:9-95). Council decision, watch
plan, dusk ride home armed (04:141-249).

Playable Green (festival-day layout):
- Required: carry cider casks from the cart to the inn cellar with Mat — the canon
  errand (01:253-263 → 02:9-51). Destination objective, two trips, Mat banter between.
- Required: raven scene as attack tutorial (02:105-127). Rand and Mat throw stones;
  the raven sidesteps: teaches the attack UI with a canon scripted miss. Moiraine's
  entrance line about the vile bird interrupts; coin scene follows (02:129-211).
- Optional talks: Egwene (braid, 03:207-251), Perrin, Ewin, Wit/Daise Congar
  (01:81-99), Cenn Buie omens (01:141-153).
- End: enter the inn as Tam decides to head home before dark.

### C1 — Winternight (Ch5 first half)

Cutscenes: farm chores montage (05:9-35); stew and locked doors (05:37-57);
sword reveal, Tam refusing its history (05:59-71).
Mission: the door bursts (05:73-85). Scripted opener: Rand's kettle throw scalds the
lead Trolloc; Tam kills two in the doorway. Objective: Rand escapes west while Tam
holds the yard; reinforcement waves make standing to fight hopeless (telegraphed per
fe-map-design rules; no enemy-phase spawns). Tam's wound is scripted and
performance-independent (05:117-145: names Trollocs, calls it a scratch).
Outro: Rand takes the sword; supplies are needed (05:147-161).

### C2 — The Village Burns (parallel night)

Framing upgrade: intro/outro quote Bran's Ch7 retelling — ball lightning out of a clear
night sky, Lan a whirlwind, "The man himself is a weapon" (07:135-141) — so the
chapter is presented as what Bran later tells Rand. Adaptation status: the framing
scenes are direct; the tactical detail remains gameplay_invention.
Mission: Lan + Moiraine defend, N-turn hold + civilian rescues. Six green allied
defenders make this a village battle rather than a two-person cleanup: Haral Luhhan
with a woodsman's axe, two hunters with bows, and three unnamed villagers with
axes/spears. They are AI-controlled and fight Trollocs. The five unnamed defenders
may fall without ending the mission. Luhhan is protected: his death is an immediate,
telegraphed loss because he appears after the battle. He starts behind the main line
near the inn/forge approach, reducing random front-line exposure while still letting
him contribute.
Bran's statement that not every Trolloc fell to Lan and Moiraine (07:141) anchors
their contribution in canon. Rebalance enemy count and positions against the
fe-map-design checklist so the allied force creates spectacle without trivializing
the rescue/hold objective.

### C3 — The Ruined Farm (Ch5 second half)

Mission (ruined-farm night layout, fog): Rand alone. Approach past the sheep pen —
the dead-flock touch beat as an interrupt region (05:169-171). Search the ruin:
waterbag, blankets, cloths, lantern (05:177-213). Narg waits inside: his broken
speech verbatim (05:187-197), scripted lunge, fight resolved as the book does —
the sword comes up in time (05:199-207). Rand starts wounded-adjacent in spirit,
not stats; Narg starts hurt so Rand is not recast as an expert.
Outro: broken cart, litter improvised from the shafts (05:213-227); rejoin Tam,
fever worse (05:227-233); litter build and setting out (06:9-43).

### C4 — The Long Road (Ch6)

Mission (westwood_road night layout): move Rand + litter (Tam as carried/paired
unit) east in legs. No combat objective; the enemy is detection.
- Leg events: roots and stumbles as terrain cost; Tam's fever outbursts as forced
  noise beats — Laman's sin (06:55-61), Avendesora (06:91-95).
- Set piece: the mounted Myrddraal and twenty Trollocs pass on the road; then the
  rider returns in silence, stopping opposite Rand's hiding place (06:63-79). Scripted
  hold-still check staged as regions/turn events, then release.
- Final cutscene of the chapter: the Dragonmount fever speech (06:99-105), Rand's
  fall to his knees, "You are my father" / "Light, who am I?"
Engine risk to spike first: litter/pair unit movement and forced-hide regions in LT.

### C5 — Out of the Woods (Ch7)

Cutscene: gray dawn, smoke too heavy, the burned village reveal (07:9-21).
Playable (burned-dawn layout): drag the litter down the Green to the inn.
- Talk/interrupt beats en route: Haral Luhhan (07:23-35, 07:43-49), Egwene's hug,
  Nynaeve's refusal — "There's nothing I can do" (07:51-79), the Dhurran dragging a
  blanketed shape (07:85), Dragon's Fang scrawled on the inn door (07:97).
- Inn cutscene: Bran, Thom, Tam upstairs; the Aes Sedai option surfaces
  (07:101-165).
- Final playable leg: Rand runs to the bonfires (short map hop or same layout),
  faces Moiraine and Lan among the burned Trollocs (07:167-205).
- Ending cutscenes: "I'll pay any price" (07:185); Moiraine rises — take me to your
  father; Lan's warning; fade as they walk to the inn. End card holds on Rand's
  question from C4.

## New beat ledger (final IDs, as shipped in source/story_beats.yaml)

Landed 2026-08-27 with the spec cutover (plan step 1). The existing stable IDs were
kept to limit churn: chapter ids stay `wn00_tutorial`, `wn01_farm_escape`,
`wn02_village_defense`, `wn03_return_to_farm` (the retitle to the table above is
deferred to the book-text pass), and the draft `p_*` prologue IDs were dropped — the
existing `c0_*` beats remain, with three additive beats for the Ch2 material.
Statuses: direct / inferred / gameplay_invention.

- c0_* additions: c0_cider_cellar (02:9-51 direct), c0_raven_omen (02:105-127
  direct), c0_moiraine_coin (02:129-211 direct). The remaining p_* draft entries
  (Fain, Thom, council, ride home) fold into the existing c0 beats during the
  Chapter 0 book-text rewrite.
- c1_*: unchanged; locator relock deferred to the C1 book-text pass.
- c2_*: kept; added c2_bran_account (07:135-141 direct) as the framing beat
  (chronology sits with the Ch7 telling, between c5_bran_and_thom and c5_bonfires).
- c3_*: kept; added c3_dead_flock (05:169-171 direct) and c3_litter_built
  (06:9-43 direct). c3_rand_rejoins_tam lost its `final_visible_event` /
  `fade_before_chapter_6` constraints.
- c4_* (Ch6, new): c4_night_road, c4_hide_mechanics (gameplay_invention),
  c4_laman_outburst, c4_column_passes, c4_rider_returns, c4_avendesora,
  c4_dragonmount_speech.
- c5_* (Ch7, new): c5_burned_village, c5_luhhan_meets, c5_nynaeve_refusal,
  c5_to_the_inn, c5_bran_and_thom, c5_bonfires, c5_walk_leg_split
  (gameplay_invention), c5_any_price, c5_moiraine_heals (campaign boundary beat).

Graybox `wn04_long_road` (new `westwood_road` layout) and `wn05_out_of_the_woods`
(emonds_field `burned_dawn` variant) missions and placeholder scenes exist with
original placeholder writing only, pending the book-text pass (step 3). The wn04
spec deliberately stays conservative: the refinement pass applies the C4 spike
results (docs/c4-spike.md) — rescue-carry pair_up for Tam, danger-region hide
windows, and a Move_to `march` AI for the column.

## Implementation sequence (bounded actions)

1. Cut over `source/canon_bible.yaml` (new ending_boundary: final beat
   c5_moiraine_heals; drop excluded_topics and the pre-Ch6 principle),
   `design/campaign.yaml` (6 chapters, drop forbidden_terms, layouts max 4,
   expected_minutes 60-100), `source/story_beats.yaml` (ledger above),
   `source/adaptation_rules.yaml` (drop campaign_endpoint truncation, add
   bran_account_framing, long_road_hide, raven_tutorial decisions). Update the
   tests that lock the old boundary and Chapter 0 tutorial contract in the same
   change; `make check` green.
2. Spike C4 engine mechanics in LT: carried-Tam unit, forced-hide region/event
   chain, detection loss condition. Go/no-go gate for the C4 mission design.
3. Rewrite scenes chapter-by-chapter with book text (playable-scene-writer),
   P → C1 → C3 → C2 → C4 → C5, each with mission spec redesigned against
   fe-map-design checklist and validated with `make check` + smoke.
4. New layouts: westwood_road (+ bonfire_outskirts decision), emonds_field
   burned-dawn variant, farm variants relock.
5. Full-campaign smoke, mission-coherence review per chapter, build report.
