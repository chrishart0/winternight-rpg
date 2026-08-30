# Round 1 QA — `wn02_village_defense`

**Mission coherence: partially coherent.** The map-level rescue loop is readable, but the earliest comprehension break is the first intro box: at the wait prompt it has already scrolled away the words that say Bran is telling Rand this story. The larger release blocker is tactical: repeated real-input routes rescued all three civilians but lost Haral Luhhan or Moiraine before turn 7.

**Verdict: FAIL**

## Test scope and evidence

- Compiled project: `build/winternight.ltproj`
- Project tree: `92946fb39eee3b164c83858bd189b1522d9ba6524029e4ab3cfa70af0ee9b35a`
- Engine commit: `1820e585450f6f47605aebd686b2a3f13af181f0`
- Runtime: pinned LT engine, `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`, native 240×160 output, real posted pygame key input.
- Deterministic seeds exercised: 5000, 5002, and 5003.
- Golden-route attempts rescued west and east on turn 1 and south on turn 2, then tried four player-readable defenses: nearest-threat attacks, Luhhan-first attacks, direct body-blocking at `[7,9]`/`[8,8]`, and Lan at `[7,9]` with Moiraine supporting from the inn doorway at `[9,7]`. The final route still lost Luhhan on turn 4 with all three rescue flags and `home_saved` true.
- Deliberate-loss attempt rescued west/east, moved the south civilian beside Lan, used the ordinary Rescue command to carry her without delivering her to `inn_safe`, and kept `rescued_south` false. This correctly created the missed-rescue state, but Luhhan or Moiraine died on turn 3–4 before the turn-7 missed-rescue check could fire.
- The chapter offers no optional Talk or Visit. The optional arsonist/home branch was exercised.

## Findings

### BLOCKER — The authored defense cannot reliably reach turn 7 even after all three civilians are rescued

**Player consequence:** The stated golden path is pre-empted by an earlier protected-unit loss. The defense outro and actual victory transition are unreachable under the tested first-time-player routes; the deliberate missed-rescue timer is likewise pre-empted by a different death.

**Repro:**

1. Start the chapter and bring all three civilians into the large green inn region. The runtime sets `rescued_west`, `rescued_east`, and `rescued_south` by turn 2.
2. Follow the briefing literally: keep Lan beside Luhhan at `[7,9]` and use Moiraine from the doorway at `[9,7]` so she can cover the eastern approach without abandoning the inn.
3. Kill adjacent attackers and the arsonist when in range. Observe the five unnamed green defenders fight, then fall.
4. Luhhan takes repeated enemy-phase attacks: west raider on turns 2 and 3, south raider on turn 3, then south/northwest pressure on turn 4. He reaches 0 HP and the chapter goes directly to GAME OVER. In the retained run, Lan had 34 HP, Moiraine had 16 HP, all three civilians were rescued, and `home_saved` was true.

**Frame evidence:**

- Enemy pressure and green combat: `/tmp/wn02-golden/enemy-phase-green-fight.png`
- Luhhan/bodyguard geometry and visible objective: `/tmp/wn02-golden/luhhan-map-hover.png`
- Final generic failure screen: `/tmp/wn02-golden/game-over.png`

**Suspected spec:**

- `design/missions/village_defense.yaml:24` — stationary, mortal Luhhan receives only `HP: +6`.
- `design/missions/village_defense.yaml:31-42` — eight starting pursuers plus four reinforcements converge on the same center.
- `design/missions/village_defense.yaml:45-47` — the north wave arrives on turn 3 and the flank wave on turn 5, despite the green screen collapsing by turns 2–3.
- `source/characters.yaml:88` — Luhhan has 30 base HP and 8 DEF; the mission bonus raises him to 36 HP but does not prevent accumulated focus fire.

**Bounded remedy:** Keep Luhhan mortal, reduce simultaneous threat overlap at `[7,8]`, and retest a formation that lets Lan and Moiraine cover the legal approach tiles. Do not hide the tuning failure behind a one-HP floor.

### HIGH — Moiraine fails the FE-map-design worst-case enemy-phase damage check

**Player consequence:** A reasonable attempt to contest the east side can lose a mandatory unit in one enemy phase. This makes experimentation with the arsonist and eastern rescue materially unsafe before the map has taught the player how many attackers will overlap.

**Repro:**

1. Rescue the east civilian, then move Moiraine toward the east-side raider/arsonist pressure.
2. On turn 2, allow the arsonist and northeast raider to attack her in the same enemy phase.
3. In the observed aggressive route, two ordinary axe hits reduced Moiraine from 27 HP to 1 HP; later pressure ended the chapter. Strong `STR: +1` axe variants are worse.

**Worst-case math:**

| Mandatory unit | HP / DEF | Strong axe ATK | Damage per hit | Enemy-phase result |
| --- | ---: | ---: | ---: | --- |
| Lan | 40 / 12 | `10 STR + 1 bonus + 8 might = 19` | 7 | Four legal melee hits total 28; passes from full HP. |
| Moiraine | 27 / 5 | 19 | 14 | Two hits total 28; **fails** from full HP. |

Enemy SPD is 5–6 versus Moiraine's 10 and Lan's 14, so the failure does not require an enemy double. It only requires two overlapping attackers.

**Frame evidence:** `/tmp/wn02-golden/moiraine-under-attack.png`

**Suspected spec:**

- `source/characters.yaml:52` — Moiraine has 27 HP and 5 DEF.
- `design/gameplay.yaml:15` — Crude Axe has 8 might.
- `design/missions/village_defense.yaml:33,39,41` — several axe attackers add `STR: +1`; the placements and waves permit overlap.

**Bounded remedy:** Remove the two-attacker overlap on Moiraine's required defend/rescue lane rather than merely increasing her stats. Retest the east approach with both hits landing and no crits.

### HIGH — Two-line scene boxes auto-scroll away the exact words that establish Bran and identify protected Luhhan

**Player consequence:** At the stable wait prompt, a fast-text player sees neither “Bran al'Vere told Rand” in the opening nor “Haral Luhhan” in the critical protection briefing. The told-story device therefore does not land at the intro, and the briefing's strongest protected-unit warning becomes a pronoun without an antecedent. The map UI later mitigates the Luhhan problem, but it does not repair the intro framing.

**Repro:**

1. Start the chapter with the runner's fast text setting.
2. Let the first intro narration finish typing. The wait frame reads only “Winternight broke across the Green.”
3. Advance to the second briefing narration. Its wait frame reads only “holds the inn approach. If he falls, the defense fails.”
4. Advance to Lan's next line. Its wait frame reads only “the Trollocs from surrounding him.”

**Frame evidence:**

- Bran intro after overflow: `/tmp/wn02-golden/sc_c2_attack_begins-01.png`
- General objective after overflow: `/tmp/wn02-golden/sc_c2_mission_briefing-01.png`
- Luhhan warning after overflow: `/tmp/wn02-golden/sc_c2_mission_briefing-02.png`
- Lan's warning after overflow: `/tmp/wn02-golden/sc_c2_mission_briefing-03.png`
- Outro first beat: `/tmp/wn02-bran-outro.png` — this still retains “a story Bran could tell Rand,” so the outro half of the device lands.

**Suspected spec:** `design/scenes/village_defense/scenes.yaml:12,28-30,117`. These narration/dialogue strings exceed the stable capacity of their 240×160 boxes.

**Bounded remedy:** Split each affected sentence at a natural clause into two explicit beats/pages so every critical subject remains on a wait frame. Do not rely on transient auto-scrolling text for “Bran,” “Rand,” or “Luhhan.”

### MED — Failure feedback never says which condition ended the chapter

**Player consequence:** Luhhan can die amid several expendable green deaths, but the only terminal feedback is a generic `GAME OVER`. A first-time player is not told whether Haral, Lan, Moiraine, or a civilian caused the loss. The authored turn-7 missed-rescue events have the same direct-to-loss shape and would not identify the unrescued civilian either.

**Repro:**

1. Let unnamed green units die; play continues.
2. Let Luhhan fall during the crowded enemy phase.
3. Observe an immediate generic GAME OVER with no preceding loss line.

**Frame evidence:** `/tmp/wn02-golden/game-over.png`

**Suspected spec:**

- `design/missions/village_defense.yaml:10-16` — death failures have no authored failure scene.
- `design/missions/village_defense.yaml:110-121` — each missed-rescue event calls `lose` directly without explanatory feedback.

**Bounded remedy:** Play one short condition-specific line before `lose` (for example, that Luhhan fell or a villager remained outside) and then show GAME OVER.

## Acceptance-point observations

- **Bran framing:** Partial. The inn background and outro work, but the intro's stable frame loses the Bran/Rand clause to overflow.
- **Luhhan telegraphing:** Readable on the map despite the briefing overflow. Hovering `[7,8]` shows Haral's unique portrait/name and the full map objective “Rescue 3 villagers, protect Haral Luhhan and defend for 6 turns.” His unit page is also distinct: `/tmp/wn02-golden/luhhan-unit-info.png`. He does not read as an unnamed expendable once hovered.
- **Rescue region:** Obvious. The inn floor is covered by a large light-green 4×3 highlight visible at chapter start and in `/tmp/wn02-golden/luhhan-map-hover.png`. Rescue completion removes the civilian and produces clear inn dialogue; see `/tmp/wn02-golden/sc_c2_rescue_woman-02.png`.
- **Green allies fighting:** Yes. Green units visibly attack/counter during enemy/other phases. `/tmp/wn02-golden/enemy-phase-green-fight.png` shows the hit flash at native resolution.
- **Arsonist/green kill credit:** Green Hunter B visibly engages the arsonist (`/tmp/wn02-golden/green-arsonist-fight.png`). No tested deterministic run produced the green final blow; Lan or Moiraine took it. The event is killer-agnostic (`design/missions/village_defense.yaml:82-86`), and the resulting line—“The torchbearer is down. That roof may stand.”—does not claim player credit (`design/scenes/village_defense/scenes.yaml:94`), so a green final blow would not make the credit line wrong.
- **Home branch:** `home_saved` fired and the feedback was readable: `/tmp/wn02-golden/sc_c2_home_saved-01.png`.
- **Defense end:** Could not be reached through combat because of the blocker. The compiled scene was separately rendered through the real engine at `/tmp/wn02-bran-outro.png`; that is scene-render evidence, not victory-path evidence.
- **Win/loss/soft-lock:** No soft-lock was observed. Loss fires promptly, but the golden win and turn-7 missed-rescue loss were both pre-empted by earlier mandatory-unit deaths.
