# Round 2 QA — `wn02_village_defense`

**Mission coherence: coherent.** The told-story framing, three-part objective, protected-unit identity, rescue feedback, six-turn defense, turn-7 resolution, and cause-specific loss paths agree in the compiled game.

**Verdict: PASS**

## Test scope and evidence

- Compiled project: `build/winternight.ltproj` (not recompiled or edited).
- Project tree exercised: `a666a9e750c52f07f28e4fdd0e2cd16e5f139f600f3f220962600bb5eea9753d`.
- Engine commit exercised: `1820e585450f6f47605aebd686b2a3f13af181f0`.
- Runtime: pinned LT engine with `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`, native 240×160 rendering, and posted pygame key-down/key-up input.
- Deterministic seeds: 5002 (door defense, Luhhan-death loss, objective UI), 5003 (lazy fixed-position defense), and 5004 (missed-rescue loss).
- Full machine-readable traces: `/tmp/wn02-golden-door-result.json`, `/tmp/wn02-golden-lazy-result.json`, `/tmp/wn02-luhhan_loss-inside5002-result.json`, `/tmp/wn02-loss-door-result.json`, and `/tmp/wn02-ui-step-result.json`.
- The cited PNGs below were opened and visually reviewed, not merely checked for existence.

## Findings

No blocking, major, or minor player-facing regressions were found. There is therefore no faulty spec location to report in this round.

## Round-1 finding re-test

### Round 1 BLOCKER — “The authored defense cannot reliably reach turn 7 even after all three civilians are rescued”

**Fixed.** Two distinct real-input formations reached the turn-7 win event with every rescue flag true and Lan, Moiraine, and Haral alive:

| Route | Player formation after rescue | Turn-7 HP: Lan / Moiraine / Haral | Outcome |
| --- | --- | ---: | --- |
| Door/bodyguard, seed 5002 | Lan `[7,9]`; Moiraine `[9,7]`; attack only threats in range | 31 / 31 / 15 | `sc_c2_defense_end` played |
| Lazy fixed-position, seed 5003 | Lan stayed `[9,8]`; Moiraine stayed `[10,8]`; no repositioning after the opening | 40 / 24 / 12 | `sc_c2_defense_end` played |

West and east reached the inn on turn 1 and south on turn 2 in both runs. The lazy route is intentionally non-optimized: the two combat units hold their starting tiles and only take attacks available from there. It still becomes tense rather than free—Haral reaches 12/40 HP and all five unnamed green defenders fall—but it is winnable.

**After-evidence:**

- Door result and turn-7 unit state: `/tmp/wn02-golden-door-result.json`.
- Lazy result and turn-7 unit state: `/tmp/wn02-golden-lazy-result.json`.
- Door victory outro: `/tmp/wn02-golden-door/sc_c2_defense_end-02.png`.
- Lazy victory outro: `/tmp/wn02-golden-lazy/sc_c2_defense_end-02.png`.

The corrected balance lives at `design/missions/village_defense.yaml:24,31-47` and `source/characters.yaml:52,83-88`: Moiraine is 36 HP/11 DEF, Haral is 40 HP/14 DEF in-mission, the southern pressure is repositioned, and the two-unit waves arrive on turns 4 and 6.

### Round 1 HIGH — “Moiraine fails the FE-map-design worst-case enemy-phase damage check”

**Fixed.** The compiled runtime starts Moiraine at 36 HP. In the lazy seed-5003 run she received three enemy contacts during the turn-3 enemy phase and entered turn 4 alive at 24 HP. She finished the turn-7 win at 24 HP. The direct pressure frame shows the crowded center without a one-phase mandatory-unit loss.

**After-evidence:** `/tmp/wn02-golden-lazy/moiraine-under-attack.png` and `/tmp/wn02-golden-lazy-result.json`.

The FE-map-design full-HP bound now passes for every mandatory unit against the strongest authored axe attacker (`19 ATK`):

| Mandatory unit | HP / DEF | Damage per strongest axe hit | Four legal melee hits | Survives at |
| --- | ---: | ---: | ---: | ---: |
| Lan | 40 / 12 | 7 | 28 | 12 |
| Moiraine | 36 / 11 | 8 | 32 | 4 |
| Haral | 40 / 14 | 5 | 20 | 20 |

Sources: `source/characters.yaml:47-58,83-88`, `design/gameplay.yaml:15`, and `design/missions/village_defense.yaml:24,31-42`.

### Round 1 HIGH — “Two-line scene boxes auto-scroll away the exact words that establish Bran and identify protected Luhhan”

**Fixed.** Every settled frame in the nine-beat opening and ten-beat briefing was visually reviewed. No line clipped or auto-scrolled its subject away. The critical stable frames now read:

- “At the inn, Bran al'Vere told Rand.” — `/tmp/wn02-golden-door/sc_c2_attack_begins-01.png`.
- “Haral Luhhan holds the inn approach.” — `/tmp/wn02-golden-door/sc_c2_mission_briefing-04.png`.
- “If Haral falls, the defense fails.” — `/tmp/wn02-golden-door/sc_c2_mission_briefing-05.png`.

The remaining briefing frames also settle as complete one- or two-row thoughts, including the six-turn instruction, the anti-surround warning, and the optional torchbearer instruction. Source: `design/scenes/village_defense/scenes.yaml:12-20,32-41`.

### Round 1 MED — “Failure feedback never says which condition ended the chapter”

**Fixed.** Both requested loss routes play a readable cause scene before the generic terminal screen:

1. **Luhhan death, seed 5002:** rescue all three civilians, withdraw Lan and Moiraine to the inn doorway, and issue no attacks. Haral reaches 0 HP on turn 6. The event trace records `sc_c2_failure_luhhan`, then `_lose_game`; the stable frame says “Haral Luhhan has fallen. The inn approach is lost.”
   - Cause: `/tmp/wn02-luhhan_loss-inside5002/sc_c2_failure_luhhan-01.png`.
   - Terminal screen: `/tmp/wn02-luhhan_loss-inside5002/game-over.png`.
   - Trace: `/tmp/wn02-luhhan_loss-inside5002-result.json`.
2. **Missed south rescue, seed 5004:** rescue west and east, move the southern villager beside Lan, use the ordinary Rescue command to carry her, and never deliver her to `inn_safe`. Lan, Moiraine, and Haral survive until turn 7 with 29/24/12 HP; `rescued_south` remains false. The event trace records `sc_c2_loss_south`, then `_lose_game`; the stable frame says “The southern villager never reached the inn before dawn.”
   - Cause: `/tmp/wn02-loss-door/sc_c2_loss_south-01.png`.
   - Terminal screen: `/tmp/wn02-loss-door/game-over.png`.
   - Trace: `/tmp/wn02-loss-door-result.json`.

Sources: failure-scene bindings at `design/missions/village_defense.yaml:10-16`, turn-7 missed-rescue events at `design/missions/village_defense.yaml:106-121`, and cause text at `design/scenes/village_defense/scenes.yaml:91-126`.

## Acceptance-point evidence

### Objective UI

The native Objective screen fits the requested win condition as three complete lines, with no clipping:

1. `Rescue villagers`
2. `Guard Haral`
3. `Hold six turns`

- Top of Objective screen: `/tmp/wn02-ui-step/objective-menu.png`.
- Scrolled loss section: `/tmp/wn02-ui-step/objective-menu-scroll-1.png`.
- Persistent map objective and named Haral hover: `/tmp/wn02-golden-door/luhhan-map-hover.png`.

The real-input scroll exposes the complete, non-duplicated loss text: “Lan, Moiraine / and Haral must / survive / All 3 villagers / must survive.” Source: `design/missions/village_defense.yaml:9-16`.

### Mission coherence trace

| State | Player-facing goal | Visible cue and public action | Feedback / next state |
| --- | --- | --- | --- |
| Opening | Understand whose account this is | Settled inn narration names Bran and Rand | Burning-Green briefing takes over |
| Turn 1 | Rescue villagers; guard Haral; hold six turns | Large light-green inn region, named Haral portrait/hover, player-controlled civilians | West/east civilians disappear into safety and each receives an inn scene |
| Turn 2 | Complete the outward rescue while holding the center | South civilian advances to the same highlighted region | South rescue scene; all three rescue flags true |
| Turns 3–6 | Keep Haral and the two mandatory combat units alive | Converging red threats, fighting green line, turn-4 north wave, turn-6 flank wave | Combat, burning-roof escalation, and optional home-saved feedback |
| Turn 7, all rescued | Survive the stated duration | No hidden extra action | Win fires and Bran's account resolves in the inn outro |
| Turn 7, rescue missed | Understand why the defense failed | Cause-specific west/east/south scene | GAME OVER follows the explanation |
| Mandatory death | Understand which protected unit fell | Cause-specific death scene names Lan, Moiraine, Haral, or the civilian | GAME OVER follows the explanation |

No hidden action, contradictory instruction, silent gate, or soft-lock was observed.

### Greens, spectacle, and difficulty

- Green allies still initiate and counter in real combat. The retained frames show the line engaging red units and a green hunter fighting the arsonist: `/tmp/wn02-golden-door/enemy-phase-green-fight.png` and `/tmp/wn02-golden-door/green-arsonist-fight.png`.
- The chapter still reads as an epic village defense at native resolution: the burning-Green backdrop, multiple converging fronts, green casualties, the turn-4 roof-collapse beat (`/tmp/wn02-golden-door/sc_c2_unavoidable_damage-01.png`), the optional home-saved beat (`/tmp/wn02-golden-door/sc_c2_home_saved-02.png`), and Bran's victory account all survive the balance changes.
- The FE-map-design pressure is tense but fair. Across the two successful routes, the lowest observed mandatory HP was Lan 31/40, Moiraine 24/36, and Haral 12/40. Across every non-Luhhan-death route, Lan's low was 29/40 in the missed-rescue run. No ordinary route lost a mandatory unit, while the lazy route consumed the green screen and left Haral at 30% HP.
- The authored shape remains within the chapter's local targets: eight starting enemies for five player units, 34.25 walkable tiles per starting enemy, two two-unit waves, and a fixed six-turn window (`design/missions/village_defense.yaml:18-47,135`). The rescue requirement prevents a pure end-turn turtle, and the late waves keep the center under pressure through the final enemy phase.
