# `wn02_village_defense` epic redesign

**Status:** implementation-ready design only. This document does not authorize edits to generated LT data.
**Mission title:** *The Village Burns*
**Core verb:** **race outward, bring people home, then hold the inn**.
**Fixed duration:** eight complete player/enemy turns; resolution occurs at player-phase start on turn 9.

## 1. Executive design decision

This redesign keeps the current chapter's proven structure instead of replacing it with a generic large battle. The Winespring Inn remains the gravitational center, six village defenders still make the battle look bigger than the blue roster, and Haral's changing HP still gives every formation decision a human cost. The new scale comes from four simultaneous house clocks, three Talk recruits, four directly controlled evacuees, three finite reinforcement waves, and a map that visibly deteriorates every other turn.

The player begins with only Lan and Moiraine. Mat, Egwene, and Nynaeve are green units clustered around the inn and can become blue through Talk. Four occupied houses sit on the north, west, east, and south spokes. A designated torchbearer marches toward each door, but **any** enemy ending an action on an unresolved door ruins that house. A blue unit reaching the door first closes the house, spawns its resident as a blue civilian, and turns the resident's trip back through the inn door into the second half of the rescue.

Victory requires both clauses:

1. return at least **three of four** residents to the inn; and
2. prevent an enemy from entering the inn threshold through the end of turn 8.

Three is the right quota. Requiring all four would turn a single early route error into a delayed restart and erase the chapter's successful “victory with visible cost” character. Requiring two would let a player ignore half the map. Three forces a real split, allows one roof to be lost, keeps the intended active blue roster around six to eight units on most turns, and leaves saving the fourth house as mastery rather than hidden necessity.

The intended tension shape is an outward race on turns 1–3, crossing escort lines on turns 3–5, re-formation on turns 5–6, and an inn-defense peak on turns 7–8. The last wave appears on turn 7, far enough away that it cannot be killed immediately, so it receives both the turn-7 and turn-8 enemy phases before resolution.

## 2. Locked contracts preserved

The later implementation must preserve all of these. They are not balance knobs.

- **Bran's Chapter 7 account remains the frame.** The inferred battle opens and closes inside the direct `c2_bran_account` telling.
- **The battle remains explicitly inferred.** Its exact rescues, recruits, routes, house outcomes, and wave timings are not presented as directly depicted book events.
- **The inn remains the anchor.** It is the only return region and the only breach-loss region.
- **Outward pull remains mandatory.** Holding the doorway without visiting houses cannot win.
- **Six original green defenders remain:** Haral, two hunters, and three militia. Mat, Egwene, and Nynaeve are additional temporary green recruits, not replacements for the spectacle line.
- **Haral remains the human stake.** He begins visibly injured, stands at the approach, and is the target of Nynaeve's guided first heal.
- **Unnamed green losses remain legal.** Their deaths change the visible cost and the ending callback but never cause a mission loss.
- **Success with visible cost remains possible.** One occupied house can be lost, background roofs burn regardless, and a legal win may leave no unnamed green defender alive.
- **Total annihilation is never required.** The chapter ends on the defense state, not enemy count.
- **Village damage is partly unavoidable.** Perfect tactics can save all four occupied households but cannot save every building.
- **Reinforcements remain finite, telegraphed, player-phase-safe, and at most two units per actual wave.**
- **No fog.** A house race plus escorts requires complete information.
- **Nynaeve provides ordinary battle aid only.** Her herbs can close combat wounds; they do not rival Moiraine's later true Healing or imply that Nynaeve could cure Tam's fever.
- **Named playables are mortal.** A death removes that unit from later playable deployment, preserves independent story portraits, and offers Restart or Continue once.

## 3. FE8 research translated into this mission

The brief names Chapter 5 and Bone together, but the FE8 chapter data separates those examples: Bone is the boss of Chapter 2, *The Protected*; Chapter 5, *The Empire's Reach*, is led by Saar. This design deliberately combines the useful parts of both rather than carrying the chapter-name mismatch forward.

| FE8 source | Concrete source facts | What `wn02` imports | What `wn02` rejects |
| --- | --- | --- | --- |
| [The Protected](https://fireemblemwiki.org/wiki/The_Protected) | 15×15; 6 player units plus 2 green NPCs; 6 starting enemies plus 2 turn-3 reinforcements; 3 villages. Wounded Ross starts at 5 HP, Moulder supplies the early healing lesson, and green Ross/Garcia become player units through Talks. | A wounded ally creates immediate healer demand; green recruits become directly controlled through Talk; a small enemy group races threatened homes; all information is visible. | A rout objective and autonomous green survival roulette. Our named greens have survival floors, and the objective is house return plus defense. |
| [The Empire's Reach](https://fireemblemwiki.org/wiki/The_Empire%27s_Reach) | 15×21; 16 starting enemies plus 7 reinforcements; 4 villages; visiting all 4 earns the extra Guiding Ring. Natasha joins as a level-1 healer, while enemy Joshua is recruited by Natasha's Talk. Reinforcement pairs arrive on turns 2, 6, and 8. | Four spatially separated visits, a visible all-houses mastery reward, a healer who immediately has a support job, and spaced two-unit waves rather than a continuous spawn treadmill. | Its lack of a turn limit and its “visit for item” reward. Here a Visit creates a vulnerable person and an urgent return route. |
| [Village mechanic](https://fireemblemwiki.org/wiki/Village) | A player Visit closes and saves the gate; an eligible enemy entering an open village destroys it and changes it to ruins, losing the reward. | The first side to reach a door permanently resolves that house, with a saved or ruined map state. | Class-specific hidden rules. Every enemy can ruin a still-open `wn02` door, and the briefing says so plainly. |
| [Last Hope](https://fireemblemwiki.org/wiki/Last_Hope) | 29×25; protect Mansel for 13 turns or defeat Riev; 25 starting enemies plus 72 reinforcements; 10 green NPCs; keeping at least 6 alive earns a Light Brand. Waves pressure multiple entrances from turns 2–12. | A late defense peak, multi-edge pressure, an anchor that must not be breached, and a visible reward/callback for preserving greens without making all of them mandatory. | Fog, 97 enemies, 13 turns, and reward-driven green babysitting. `wn02` uses 10 starters and at most 6 actual reinforcements over 8 turns. |
| [Reinforcement timing](https://fireemblemwiki.org/wiki/Reinforcement) | *The Sacred Stones* spawns reinforcements at turn start before player phase, unlike same-turn enemy-phase ambush games. | `turn_start` → LT `turn_change`; spawn, focus the on-screen agent, warn, then return control. | Enemy-phase spawns and untelegraphed edge attacks. |

The important FE8 lesson is not “add more enemies.” It is that a threatened village converts distance into a comprehensible clock, a Talk recruit converts a vulnerable green into player agency, and a defend map stays alive when different entrances become urgent at different times.

## 4. Map decision

### Recommendation: a dedicated fifth layout

Create a dedicated **`emonds_field_battle`** layout, 22×18, and raise `design/campaign.yaml` `unique_map_layouts_max` from 4 to 5. Update the campaign-spec assertions that lock the old cap and template set.

This chooses option **(b)**. The owner requires a larger battle map, and the current shared `emonds_field` is already 20×16. Enlarging that shared template would force coordinate and topology changes through the warm `wn00` tutorial and the quiet `wn05` denouement, relock every variant hash, and either add empty border acreage to those chapters or redesign two already-played routes for no benefit. A dedicated layout spends one explicit campaign exception but isolates the battle's high-pressure geometry. It also lets burn overlays exist only where runtime destruction is needed.

The 22×18 map is 396 total tiles, 24% larger in footprint than 20×16. The sketch below has **284 walkable tiles** and 112 blocked tiles, versus 274 walkable tiles on the current battle variant. With 10 starting enemies, density is **28.4 walkable tiles per starting enemy**, inside the 18–35 target. The design intentionally violates the local 320-total-tile ceiling because the owner explicitly requires a larger map; it prevents the usual empty-acreage failure by keeping walkable density in range and assigning every spoke a house clock, spawn lane, or return route.

### 0-based tactical sketch

Each character represents one tile. This is the topology contract; final art may change visual variants but not passability, door coordinates, or route costs.

```text
   0000000000111111111122
   0123456789012345678901
00 #####^^########^^#####
01 #........HHHH........#
02 #........HHHH........#
03 #......~~.d=.~~......#
04 #.........==.........#
05 #.......IIIIII.......#
06 #.HHH.~.IiiiiI.~.HHH.#
07 ^.HHH.~.IiiiiI.~.HHH.^
08 ^====d==IiiiiI==d====^
09 ^=======IIAAII=======^
10 ^.........==.........^
11 #.........==.........#
12 #.........==.........#
13 ^.hhh..~~.==.~~..hhh.^
14 ^.hhh.....=d.....hhh.^
15 #........HHHH........#
16 #........HHHH........#
17 #####^^########^^#####
```

Legend:

- `.` grass, cost 1.
- `=` road, cost 1; the exposed fast route.
- `~` forest/rubble, cost 2; the single slower bypass around each outer throat.
- `H` occupied house wall, blocked.
- `d` occupied house door/Visit region, cost 1 until resolved.
- `h` already-evacuated background structure, blocked; its sparse overlays ignite and collapse on turns 2/4/6/8.
- `I` inn wall, blocked.
- `i` inn floor and `inn_safe`, cost 1.
- `A` the two-tile inn threshold/door, cost 1 and the breach-loss region.
- `^` visible edge road/spawn gate, cost 1.

### Stable coordinates and route costs

| Object | Coordinate / extent | Cost and purpose |
| --- | --- | --- |
| `house_west` | walls x2–4/y6–7; facade door **[3,7]** | The resolved resident exits to road **[3,8]**; resident-to-inn path cost 11. |
| `house_north` | walls x9–12/y1–2; facade door **[10,2]** | The resolved resident exits to road **[10,3]**; resident-to-inn path cost 15, making this the mastery rescue. |
| `house_east` | walls x17–19/y6–7; facade door **[18,7]** | The resolved resident exits to road **[18,8]**; resident-to-inn path cost 11. |
| `house_south` | walls x9–12/y15–16; facade door **[12,16]** | The resolved resident exits to grass **[13,16]** and wraps around the east wall; resident-to-inn path cost 11. |
| `inn_safe` | **[9,6]**, size **[4,3]** | Only civilian return region. The walls force north/east/west residents around to the south doors instead of granting a trivial straight line. |
| `inn_threshold` | **[10,9]**, size **[2,1]** | Any enemy ending an action here triggers `sc_c2_failure_inn_breach` and `lose`. |
| player start cluster | Lan [7,9], Moiraine [12,8] | Both are near recruits, not already placed on the optimal outer routes. |
| recruit cluster | Mat [7,8], Egwene [6,8], Nynaeve [11,8] | Mat/Egwene are on the west apron; Nynaeve begins inside the inn. |
| Haral | **[11,10]** | One move and range-1 herb use from Nynaeve; immediately outside the threshold. |

The west, east, and south residents each have an 11-cost return route; north is longest at 15. Visit/spawn and return each end movement, so every rescue still consumes distinct unit actions and player phases. The fixed eight-turn window remains longer than every required return route without creating travel-only filler.

### Chokepoints and bypasses

1. **West house approach:** the facade door at [3,7] has one walkable neighbor, road [3,8], on the exposed west spoke.
2. **North house approach:** the facade door at [10,2] has one walkable neighbor, road [10,3], at the top of the central spoke.
3. **East house approach:** the facade door at [18,7] has one walkable neighbor, road [18,8], on the exposed east spoke.
4. **South house approach:** the facade door at [12,16] has one walkable neighbor, grass [13,16], reached around the east wall.

The two-tile inn threshold is an objective gate, not a house approach. The four one-tile doorstep pockets make the Visit locations visually unambiguous without changing the visit-house, walk-resident-into-inn rescue rule.

Every non-grass tile has a verb: roads accelerate exposed rescues, cost-2 tiles buy safer alignment at a one-turn tax, buildings channel, doors carry Visit/ruin state, inn floors define safety, and edge roads reveal reinforcement sources.

## 5. Objective, win, and loss contract

Mission metadata:

```yaml
objective:
  type: defend_rescue
  display_text: "Return 3,Hold inn 8 turns"
  survive_turns: 8       # review metadata; not relied upon for runtime
  rescue_count: 3        # review metadata; not relied upon for runtime
  region: inn_safe
target_play:
  minimum_turns: 8
  maximum_turns: 8
  expected_minutes: [20, 28]
```

Both objective display lines fit the 16-character persistent Objective-screen limit. The briefing explicitly expands “Return 3” to “Visit occupied doors, then move three residents into the inn.”

Runtime state is explicit because `survive_turns` and `rescue_count` do not compile victory logic:

- `residents_returned` starts at 0 and increments when a specific resident interacts with `inn_safe`.
- `houses_ruined` starts at 0 and increments when an enemy resolves an open door.
- Each house owns mutually exclusive `house_X_saved` / `house_X_ruined` flags and one active door region.
- `inn_breached` starts false and is set immediately before the breach failure scene.
- Turn-start 9 event with `residents_returned >= 3` and `inn_breached == false` performs `win`.
- Turn-start 9 event with `residents_returned <= 2` performs `sc_c2_failure_quota` then `lose`.
- The second ruined occupied house (`houses_ruined >= 2`) immediately performs `sc_c2_failure_quota_impossible` then `lose`; the player never spends five turns in an unwinnable state.
- Any active rescued civilian's death performs its short cause-specific failure scene then `lose`.
- Any enemy ending an action in `inn_threshold` performs `sc_c2_failure_inn_breach` then `lose`.
- Named playable deaths are not automatic mission failures. Each offers Restart or Continue; continuing preserves the death.

Resolution at turn-start 9 means the player receives exactly eight enemy phases. There is no boss-kill shortcut and no mercy win.

## 6. House system: exact state machine

### Player wins a door

Each door is an active, one-tile, `only_once`, `interrupt_move` event region. `region_interact` is already a player interaction, so no player-team condition is required.

For `house_north`, the content pattern is:

```yaml
trigger: {type: region_interact, region: house_north_door}
condition: {flag_false: house_north_ruined}
actions:
  - {type: set_flag, target: house_north_saved, value: true}
  - {type: deactivate_region, target: house_north_door}
  - {type: show_layer, target: house_north_saved}
  - {type: spawn_group, target: resident_north_group}
  - {type: change_ai, target: torch_north, value: pursue}
  - {type: play_scene, target: sc_c2_house_north_opened}
```

The hidden group contains one `team: player`, `starts_on_map: false`, directly controllable civilian. `add_group ... closest` places the resident beside the occupied door if the exact group coordinate is occupied by the visitor. The saved overlay closes the doorway with an intact barred-door tile. The assigned torchbearer abandons `march` and begins `pursue`, so winning the race changes the next tactical state rather than deleting pressure.

### Enemy wins a door

The ruin event listens to `unit_wait` and uses the proposed narrow triggering-unit condition:

```yaml
trigger: {type: unit_wait}
condition:
  flag_false: house_north_saved
  trigger_unit_in_region: {team: enemy, region: house_north_door}
actions:
  - {type: set_flag, target: house_north_ruined, value: true}
  - {type: increment_flag, target: houses_ruined, value: 1}
  - {type: deactivate_region, target: house_north_door}
  - {type: show_layer, target: house_north_ruined}
  - {type: change_ai, target: torch_north, value: pursue}
  - {type: play_scene, target: sc_c2_house_north_ruined}
```

This gives the directive its literal semantics: any enemy, not merely the assigned torchbearer, can ruin an unresolved door. The ruined overlay replaces roof and door tiles with fire/rubble. The resident never spawns. A separate counter comparison loses immediately on the second ruined occupied house.

### Resident returns

Each resident gets a specific existing `region_interact` event against the reusable `inn_safe` region:

```yaml
trigger: {type: region_interact, unit: resident_north, region: inn_safe}
condition: {flag_false: resident_north_returned}
actions:
  - {type: remove_unit, target: resident_north}
  - {type: set_flag, target: resident_north_returned, value: true}
  - {type: increment_flag, target: residents_returned, value: 1}
  - {type: play_scene, target: sc_c2_resident_returned}
```

The resident is blue from spawn to return. No follower AI, teleport, implicit carry, or autonomous pace is involved. Entering the inn removes that temporary body, which is why normal play peaks around six to eight blue units even though a deliberate all-four simultaneous rescue can momentarily place nine blue units on the map.

### Progressive burning

Burn progression has two sources:

1. **Reactive:** every occupied-house loss immediately shows that house's `*_ruined` layer.
2. **Unavoidable:** sparse background-building layers show on turns 2, 4, 6, and 8: west roof catches, west roof collapses, southeast roof catches, southeast roof collapses. These buildings contain no rescue target and cannot be saved.

The progression is monotonic, so the mission needs `show_layer` but not `hide_layer`. Fire/rubble changes both visible sprite and topmost terrain; a burned door becomes cost-2 rubble, while a saved door becomes blocked/closed. The current compiler can emit `show_layer`, but the map adapter authors only the base layer. Section 13 specifies the required source-map layer addition. If that addition is declined, the honest fallback is flags plus `emonds_burning` scene cards and sound cues. That fallback is mechanically valid but **does not satisfy the owner's request for progressive on-map burn visuals** and should not be represented as equivalent.

## 7. Full unit roster

### Blue start and green Talk recruits

| ID | Team at start | Position | Gear / role | Recruitment and death |
| --- | --- | ---: | --- | --- |
| `lan` | player | [7,9] | Power-wrought Sword (unbreakable), Field Dressing; mobile blocker/interceptor | Mortal; death offers Restart or Continue. |
| `moiraine` | player | [12,8] | Weave of Air, Ball Lightning, Weave of Spirit; ranged pressure/triage | Mortal; death offers Restart or Continue. |
| `mat_c2` | other | [7,8] | Hunting Bow, Thrown Stone; runner and ranged pressure | Egwene Talk → player and refresh. Mortal once recruited. |
| `egwene_c2` | other | [10,8] | Healing Herbs; runner/secondary triage | Nynaeve Talk → player and refresh. Mortal once recruited. |
| `nynaeve_c2` | player | [11,8] | Healing Herbs, 8 HP × 3 uses at range 0–1 | Recruits Egwene, then receives the guided Haral-heal prompt. Mortal. |

Talk setup at level start uses existing `add_talk`. The turn-1 chain is Nynaeve→Egwene, then Egwene→Mat; each recruit changes to player and refreshes. Players may break the chain to reposition Nynaeve or send another unit toward a house, so recruitment order remains a tactical choice.

#### Moiraine's weave kit

Bran's account is the only channeling the book gives Moiraine on Winternight, and it names exactly one weave, so her three equipped actions are Weave of Air, Ball Lightning, and Weave of Spirit. `Weave of Air` is authored first so LT equips the range-1–2 weave and she still counterattacks adjacent raiders. `Ball Lightning` is range 2–3, might 12, hit 85, five uses, and plays its own `BallLightning` strike animation; `Weave of Spirit` is her only spell-action heal at 14 HP × 3 uses, range 1–2. Both decisions are recorded in `source/adaptation_rules.yaml` as `moiraine_ball_lightning_weave` (gameplay_invention) and `moiraine_heals_by_weave_not_herbs` (inferred).

Ball Lightning damage is MAG 13 + might 12 − RES 1 = **24**, which deliberately keeps the map's kill thresholds readable:

| Target | HP in mission | Result of one Ball Lightning hit |
| --- | ---: | --- |
| Plain jagged-spear raider | 24 | Dies outright — the weave's identity. |
| Plain crude-axe raider | 26 | Survives at 2; always needs a follow-up. |
| Door torchbearer (HP +2) | 26 / 28 | Survives; the four house clocks are never trivialized. |
| Turn-7 final pair (HP +3) | 27 / 29 | Survives; the late peak stays dangerous. |

Removing Healing Herbs from her costs 24 HP of triage; the upgraded weave returns 42 across the same three actions, so the mission's healing budget rises by 18 HP while the number of heal actions is unchanged.

### Green defenders

| ID | Position | AI / purpose | Fate rule |
| --- | ---: | --- | --- |
| `luhhan_defender` | [11,10] | Patrols the south approach; HP +8, DEF +2; current HP set to 28/40 | Mortal; never a named-character loss condition. |
| `hunter_west` | [7,7] | radius-3 patrol anchored west; bow spectacle and door cover | May die; alive flag feeds victory callback. |
| `hunter_east` | [14,7] | radius-3 patrol anchored east | May die; alive flag feeds victory callback. |
| `militia_west` | [6,10] | radius-3 patrol anchored west approach | May die; alive flag feeds victory callback. |
| `militia_east` | [15,10] | radius-3 patrol anchored east approach | May die; alive flag feeds victory callback. |
| `militia_south` | [10,12] | radius-3 patrol anchored south road | May die; alive flag feeds victory callback. |

These patrols use the existing `patrol` behavior with a destination and detection radius. They attack nearby threats but return toward their authored post instead of chasing to an edge. Five boolean alive flags start true and clear on the corresponding `unit_death`. If any remains true, the resolution inserts a short green-survivor acknowledgment before Bran's direct frame. There is no item reward and no loss for failing this mastery goal.

### Background rider (optional encounter)

| ID | Position | AI / purpose | Fate rule |
| --- | ---: | --- | --- |
| `rider_watch` | [1,1] | `do_nothing`; the `myrddraal` template with a Black Sword so it can answer a blow. Far top-left grass, clear of every door, the inn regions, all reinforcement spawns, and every other unit's start tile. | Optional. Not in the rescue quota, any reinforcement group, or any win/loss condition. |

It begins completely inert: LT compiles `do_nothing` to three all-`None` behaviours, and `AIController.think` skips a `None` action outright, so it never moves, seeks, or attacks on any enemy phase regardless of adjacency or turn count. Counterattack legality is decided by `combat_calcs.can_counterattack`, which never consults AI, so it answers a strike immediately when range permits.

`rider_wakes_when_struck` is a `combat_end` event conditioned on `unit2.nid == 'rider_watch'` **and** `unit.team == 'player'`, `only_once`. It plays `sc_c2_rider_wakes` and emits `change_ai;rider_watch;pursue`. Cursor hover, entering its range, an enemy-initiated combat, and turn changes cannot fire it. Level 8 with no stat bonus makes killing it a real reward for a real risk: Lan needs three connected rounds, and its speed 13 doubles the lighter recruits.

### Spawned residents

| ID / group | House | Character template | Mission tuning | Return rule |
| --- | --- | --- | --- | --- |
| `resident_west` / `resident_west_group` | west | `villager_woman` | player, off-map, no item, HP +10, DEF +4 | Remove in `inn_safe`, increment counter. Death loses. |
| `resident_north` / `resident_north_group` | north | `villager_man` | same | Same. |
| `resident_east` / `resident_east_group` | east | `villager_woman` | same | Same. |
| `resident_south` / `resident_south_group` | south | `villager_man` | same | Same. |

The +10 HP/+4 DEF mission tuning produces 28 HP/6 DEF. It represents a resilient evacuee token and, more importantly, prevents the new escort lesson from being erased by one unlucky enemy phase. It does not make the residents fighters: they have no item and spend every useful action moving.

### Starting enemies

| ID | Type / position | Initial AI | Tactical job |
| --- | --- | --- | --- |
| `torch_west` | axe [1,2] | `seek_house_west` march → [5,8] | Two-turn west clock; overlaps `raider_nw`. |
| `torch_north` | spear [18,1] | `seek_house_north` march → [10,3] | Three-turn north clock; overlaps northeast threats. |
| `torch_east` | axe [20,1] | `seek_house_east` march → [16,8] | Three-turn east clock. |
| `torch_south` | spear [20,16] | `seek_house_south` march → [11,14] | Three-turn south clock; overlaps southeast threat. |
| `raider_nw` | spear [4,2] | `pursue` | Forces a blocker/visitor split on west/north. |
| `raider_ne` | axe [17,3] | `pursue` | Punishes sending Moiraine east alone. |
| `raider_west` | axe [1,10] | `pursue` | Pressures the west green post and return lane. |
| `raider_east` | spear [20,10] | `pursue` | Pressures the east green post and return lane. |
| `raider_sw` | axe [6,16] | `pursue` | Moves toward south road/inn, not an unused corner. |
| `raider_se` | spear [15,16] | `pursue` | Pairs with `torch_south`/`raider_sw` around the south throat. |

All start at level 2. Torchbearers receive HP +2 so intercepting one is a commitment rather than a free deletion; they do not attack while marching. Resolving their house by either outcome switches the assigned marcher to `pursue`. Six of the ten starters belong to explicit overlapping-threat pairs, exceeding the one-third requirement.

Starting enemy ratio is **10:5 = 2.0** against the full recruitable non-civilian blue roster. Counting only the two initial blue units would misrepresent the turn-1 Talk conversion; counting directly controlled but unarmed evacuees would misrepresent kill capacity. During ordinary escort play, 6–8 blue bodies are active, but only Lan and Moiraine are reliable attackers; six green defenders offset the higher raw enemy count until their line begins to collapse.

## 8. Reinforcement schedule and telegraphs

| Turn | Units / coordinates | Telegraph and reaction space | Job |
| ---: | --- | --- | --- |
| 3 | `north_wave_a` axe [5,0], `north_wave_b` spear [16,0] | North roads are named in the opening. At turn start: spawn → focus/highlight `north_wave_a` → one-page warning → control. Nearest expected visitor at [10,3] is 8/9 Manhattan tiles away. | Crosses the far resident's return lane and prevents the north rescue from being a free mastery lap. |
| 5 | Full branch: axe [0,13] and spear [21,13]. All-four-saved branch: only the farther axe at [0,13]. | Both flank roads are visible from turn 1; turn-start spawn → focus actual unit → warning. Spawn is at least 10 tiles from any house door. | Re-formation test. Saving all four houses changes the immediate tactical state by removing one flank attacker. |
| 7 | `final_south_a` axe [5,17], `final_south_b` spear [16,17], HP +3/STR +1/DEF +1 | Turn 6 gives a south-edge warning. Turn 7 stages spawn → focus agent → warning → control. Spawns are at least 8 tiles from the south-door area. | Late peak. They cannot be killed on spawn turn by a MOV-6/range-1 or MOV-5/range-2 unit and therefore receive enemy phases 7 and 8. |

Maximum actual reinforcements are 6, below the 10-unit starting count. Every actual wave is 1–2 units. Turn 7 is the last spawn. All use `turn_start`, which the current compiler maps to LT `turn_change` before player phase.

## 9. Turn-by-turn tension curve

| Turn | Burning clock | Expected player location and decision | Pressure state |
| ---: | --- | --- | --- |
| **1 — people before positions** | Existing firelit base state; all four occupied doors highlighted once. | Inn apron. Choose recruit order versus sending a veteran immediately outward. Preferred chain recruits Mat/Egwene/Nynaeve; Egwene can win west while Nynaeve heals Haral. | Four marchers visibly establish the clocks. West is urgent first. No reinforcement. |
| **2 — the first roof** | West background roof catches via overlay. | West/south spokes. Bring the west resident around the inn wall, send Nynaeve or Lan south, and start Mat/Moiraine toward north/east. | West torch resolves if ignored; green posts make first contact. North edge warning lands. |
| **3 — split at maximum stretch** | Any unresolved door may visibly fall. | All four spokes. Decide whether to save the mastery fourth house or escort/brace. | North wave spawns with reaction time. North and east/south clocks resolve after player phase. This is the route-planning peak, not the battle peak. |
| **4 — crossing lines** | West background roof collapses. | Residents converge around the inn's south entrance while veterans are still outside. | No new wave. Existing north pressure and collapsing green HP make target, heal, escort order, and lane choice matter. One occupied-house loss is a legal, visible cost. |
| **5 — reform or be cut apart** | Map holds its current damage so the new agents read clearly. | First residents should return; the far north resident remains exposed. | Conditional flank wave: one if all four homes are saved, otherwise two. Saving the optional fourth house now pays off tactically. |
| **6 — warning from the south** | Southeast background roof catches. | Inn approaches and final escort leg. Choose Nynaeve's limited heal target, preserve a green, or accelerate the last resident. | Flank receives a second phase; final edge is announced. No spawn means the warning does not compete with a new unit set piece. |
| **7 — the line bends** | Existing fires remain; no text lock before the peak. | South apron/inn threshold. Last delivery competes directly with intercepting the final pair. | Final south pair spawns, is focused, and cannot be reached immediately. Green line and Haral should be at their lowest credible state. |
| **8 — dawn is one phase away** | Southeast roof collapses; half the background structures are visibly lost even on a perfect route. | Inn threshold and any final resident. Choose kill versus body-block versus heal versus return. | No new bodies. The turn-7 pair receives its second enemy phase. Inn breach or missing quota loses; turn-start 9 resolves success. |

This produces a rising defense curve: turn 3 is the spatial stretch, turn 5 is the re-formation test, and turns 7–8 are the tactical/emotional peak. Burning is the clock the player can read without opening a menu.

## 10. Nynaeve guided-heal introduction

Nynaeve begins player-controlled at [11,8], beside green Egwene; Haral begins at [11,10] with 28/40 HP. Nynaeve's Talk recruits and refreshes Egwene, then shows one stable tutorial page:

> Move Nynaeve beside Haral. Item: Healing Herbs.

Nynaeve moves to [10,10] and chooses the top-level Item action, Healing Herbs, Use, and Haral. Herbs are a physical remedy, so they carry LT's `usable` component and never touch the spell pathway; the range-0–1 remedy restores 8 HP to 36/40 and can also target its wounded user. A `combat_end` event for Nynaeve and `luhhan_defender` sets `nynaeve_guided_heal_done`, restores the main objective banner, and plays one short Haral thanks/Nynaeve triage exchange.

The heal remains relevant after the lesson. Healing Herbs have three uses, grant 11 EXP, and remain weaker than Moiraine's 14-HP range-1–2 Weave of Spirit. Egwene and Moiraine provide alternate aid, but every heal consumes an action that could attack, Visit, or move an escort.

Lore language is fixed: “herbs,” “bandage,” “battle wound,” and “tend” are permitted. “Healing” as the capitalized story-unique act, curing the Trolloc fever, or equating Nynaeve's pouch with Moiraine's later intervention is prohibited.

## 11. Worst-case one-enemy-phase math

Use the strongest authored late attacker: axe Trolloc attack = base STR 10 + Crude Axe might 8 + late-wave STR 1 = **19**. Weapons have 0 crit in `design/gameplay.yaml`. Trolloc speed 5–6 does not double any listed mandatory unit under the engine's four-speed threshold. The map has no ranged enemies; attack-slot counts come from the specified one-/two-wide geometry.

| Mandatory unit | HP / DEF in mission | Maximum simultaneous melee hits on intended tile/route | Raw maximum phase damage | Raw margin / protection conclusion |
| --- | ---: | ---: | ---: | --- |
| Lan | 40 / 12 | 4 at a two-wide outer throat | 4 × 7 = 28 | 12 HP on the intended exposure; lethal overextension remains possible. |
| Moiraine | 36 / 11 | 4 at a two-wide outer throat | 4 × 8 = 32 | 4 HP on the intended exposure; lethal overextension remains possible. |
| Mat | 20 / 3 | 2 while running behind a visitor/blocker | 2 × 16 = 32 | The second hit is lethal; continuing preserves his playable death. |
| Egwene | 19 / 2 | 2 | 2 × 17 = 34 | The second hit is lethal; continuing preserves her playable death. |
| Nynaeve | 22 / 3 | 2 | 2 × 16 = 32 | The second hit is lethal; continuing preserves her playable death. |
| Haral, before guided heal | 28 current (40 max) / 12 | 3 at the one-tile approach face | 3 × 7 = 21 | 7 HP before herbs, 15 after the first 8-HP heal; further neglect can kill him. |
| Each resident | 28 / 6 | 2 on the walled return route | 2 × 13 = 26 | 2 HP. A resident can survive one worst-case phase but dies to repeated neglect, preserving escort stakes. |

Named playables have no hidden HP floor. A death prompt explains that Continue removes the unit from play but leaves story scenes intact; Restart routes through LT's chapter-start save.

Healing supply is substantial, but action economy is the counterweight. Nynaeve has 24 possible HP, Moiraine's Weave of Spirit has 42, and Herb Pouches/Field Dressing consume actions on a map with four clocks and an inn threshold. The +1 STR/HP/DEF on only the turn-7 pair is enough to keep the late peak dangerous without making early resident routes brittle.

## 12. Dead-turn analysis by design

Target: **0/8 dead turns** for both the all-content route and any successful three-house route. This is a design prediction to be verified by the later dual-run fun review, not a claim of playtest evidence.

| Turn | Why it is not dead for a successful route |
| ---: | --- |
| 1 | Talk ordering, west-door speed, and Haral's heal compete for actions. |
| 2 | South/west residents and north/east visitors require route and blocker choices while greens enter combat. |
| 3 | The player chooses the fourth house versus escort safety while a visible north pair opens a new front. |
| 4 | Crossing residents, Haral/green HP, and no fresh wave create a target/heal/order turn rather than a spawn spectacle. |
| 5 | The saved-houses branch changes wave size; return count competes with flank interception. |
| 6 | Final escort, limited healing, green preservation, and the south warning demand re-formation. |
| 7 | The last pair is out of immediate kill reach; last delivery versus threshold defense is the late peak. |
| 8 | The final pair receives a second phase. Body-block, heal, attack, preserve-green, and return choices remain live until dawn. |

A pure inn turtle is not a slow alternate win: two occupied houses are ruined by turn 3 and `houses_ruined >= 2` loses immediately. A player who returns three residents and then retreats still faces the conditional flank, the two-phase final wave, the breach region, changing Haral HP, and the visible cost of green casualties. The turn-8 wave cannot be cleared on turn 7 because its spawn distance exceeds maximum move-plus-range.

Mandatory pre-control text budget is **12 A-press pages maximum** against eight natural turns (1.5 pages/turn): a shortened Bran frame, the threat-agent/map reveal, and the objective. Recruit and healer exchanges occur after control and each wave warning is one page. Direct Bran quotations remain exact short book lines; inferred and invented scenes use original text. All final boxes obey the scene writer's conservative 56-character box target and the hard illegal-character rules.

## 13. Compiler and engine feasibility audit

### Verified available now

| Mechanic | Source vocabulary and exact emission |
| --- | --- |
| Recruit green through Talk | `add_talk`/`talk`, then `change_team {target: unit, value: player}`. `EventActionSpec` already accepts `change_team`; `event_compiler.py` emits `change_team;<unit>;player`. LT `event_commands.py` `ChangeTeam` explicitly documents recruiting an enemy through Talk. Use `refresh_unit` → `reset;<unit>` so the new blue unit can act. |
| Saved/ruined layer reveal | `show_layer {target: layer_nid}` already emits `show_layer;<nid>;immediate`. LT exposes both `show_layer` and `hide_layer`; this monotonic design needs only show. The missing piece is authoring non-base layers, listed below. |
| Door-seeker movement and switch | Four existing `march` AI profiles with fixed door destinations. House resolution uses existing `change_ai` to `pursue`. No new composite AI behavior is required. |
| Player Visit | Active `region_interact` regions with `only_once`/`interrupt_move`, followed by `deactivate_region`. |
| Spawn and return | Existing `spawn_group`, `remove_unit`, `increment_flag`, and per-unit `region_interact`. |
| Fixed-duration waves | `turn_start` → LT `turn_change`; `spawn_group` → `add_group ... immediate;closest`. |
| Tutorial heal confirmation | `tutorial_text`, `combat_end`, LT's `usable` item component reached from the top-level Item action, and a fixed heal with range 0–1. |
| Named playable death | LT Classic permadeath, `unit_death`, `choice`, and `lose_game`; Restart uses LT's chapter-start restart save, Continue preserves the dead unit. |
| Objective and failure | Existing `change_objective` `both`/`loss`, `win` → `win_game`, `lose` → `lose_game`, plus cause-specific scenes. |

### Minimal compiler additions required

Production-size estimates exclude focused tests/schema lines but include model and compiler/adapter work. None requires an engine patch.

1. **Source-authored sparse tilemap layers — required for progressive on-map burning.**
   - Add `MapLayerSpec {id, initially_visible=false, foreground=false, tiles: dict["x,y", legend_symbol]}` and `MapVariantSpec.layers`.
   - Validate unique layer IDs, bounds, and legend symbols in `MapLayoutSpec.validate_grid`.
   - In `campaign_lt_adapter.compile_campaign_resources`, import LT `LayerGrid`, append one layer per spec, set `visible`, populate `sprite_grid` and `terrain_grid` with the same deterministic visual-variant hash used for base tiles.
   - **Emission target:** serialized LT `TileMapPrefab.layers`. Runtime reveal uses the already-verified LT `show_layer;Layer;LayerTransition` command. LT `hide_layer` also exists but is not required.
   - **Estimated production size:** 70–100 lines; focused model/adapter contract tests approximately 60–90 lines.

2. **`trigger_unit_in_region` event condition — required for literal “any enemy reaches a door.”**
   - Add `TriggerUnitInRegionSpec {team: player|enemy|other, region: str}` to `EventConditionSpec`.
   - Compile only on a unit-bearing trigger such as `unit_wait` to: `unit and unit.team == 'enemy' and '<region>' in game.level.regions and game.level.regions.get('<region>').contains(unit.position)`.
   - Validate the referenced region and reject use on triggers without a `unit` context.
   - **Emission target:** LT `EventPrefab.condition` Python expression; no event command is needed. The trigger remains existing LT `unit_wait`.
   - **Estimated production size:** 25–40 lines; focused compile/validation tests approximately 30–45 lines.

3. **Numeric level-variable comparison — required for `>=3 returned`, `<=2 returned`, and second-house early failure.**
   - Add a single condition object `level_var_compare: {name, op: ge|le|eq, value: int}` rather than separate one-off fields.
   - Compile to `game.level_vars.get('<name>', 0) >= 3` (or the selected operator).
   - **Emission target:** LT `EventPrefab.condition`; no engine command. Counters continue to use existing `inc_level_var` from `increment_flag`.
   - **Estimated production size:** 20–30 lines; focused tests approximately 25–35 lines.

4. **`set_current_hp` action — required to make Haral legally healable on turn 1 without a fake pre-battle combat.**
   - Add `set_current_hp {target: unit_id, value: positive_int}` to `EventActionSpec`, validate the unit and value, and compile to `set_current_hp;<unit>;<hp>`.
   - LT `event_commands.py` verifies `SetCurrentHP`, keywords `Unit` and `HP`, and optional `damage_numbers`.
   - **Emission target:** verified LT `set_current_hp` command.
   - **Estimated production size:** 12–20 lines; focused compile/runtime contract tests approximately 15–25 lines.

No engine patch is needed for Item-menu heal targeting, Classic permadeath, player choice, or title-screen Restart Level; the compiler emits those pinned-LT contracts directly.

## 14. Adaptation and beat ledger cutover

The owner directive supersedes the current `named_circle_absent` decision. The later implementation must make a clean cutover; it must not retain contradictory absent/present entries.

### Story-beat changes

- **Revise `c2_village_defense` (inferred):** Lan and Moiraine hold the inn while village defenders, including owner-directed Mat, Egwene, and Nynaeve, act around it and residents flee from occupied houses. Keep `no_total_victory`, `inn_as_refuge`, and `explicitly_inferred`.
- **Revise `c2_defense_objective` (gameplay invention):** eight turns, four house races, return at least three residents, and prevent inn breach. Replace `survive_six_turns` with `survive_eight_turns`.
- **Retire `c2_unseen_circle` and replace it with stable `c2_named_villagers_join` (inferred):** Mat, Egwene, and Nynaeve are present and may join the playable defense; Perrin remains unshown and no fate is invented for him.
- **Revise `c2_homes_threatened` (gameplay invention):** four occupied doors may be saved or ruined while background buildings are unavoidably lost.
- **Add `c2_nynaeve_battle_aid` (inferred):** Nynaeve uses ordinary village remedies on Haral's combat wounds; this neither depicts nor approaches true Healing.
- **Keep `c2_bran_account` unchanged (direct).** It remains the only direct source for the battle frame.

### Replacement adaptation decisions

| ID | Status | Decision | Rationale / canon effect |
| --- | --- | --- | --- |
| `village_parallel_battle` | inferred, revised | Include Lan, Moiraine, the six defenders, and owner-directed Mat/Egwene/Nynaeve in the unseen parallel defense. | Bran/Thom establish that villagers fought, but exact named participation is not directly shown. `unseen_parallel_sequence_constructed`. |
| `village_defense_rules` | gameplay_invention, revised | Hold the inn for eight turns, resolve four occupied house doors, and return at least three residents. | Creates the requested large defend/rescue loop without claiming a village-wide victory. `objective_and_tactical_detail_invented`. |
| `named_villagers_join_defense` | inferred, replaces `named_circle_absent` | Mat, Egwene, and Nynaeve join the playable defense; Perrin is not shown. | Owner directive supersedes the absence decision; playable death does not delete independent later story portraits. `unseen_named_participation_inferred`. |
| `talk_recruitment_staging` | gameplay_invention | Convert the three green units to blue through specific Talk chains and immediate refresh. | FE-style player agency and tutorial pacing; the exact conversations/timing are invented. `recruitment_mechanic_added`. |
| `household_rescue_race` | gameplay_invention | First side to each door resolves it; a player Visit spawns a controlled resident who must enter the inn, while an enemy creates ruins. | Turns “homes were burned” into a fair, legible tactical clock. `house_outcomes_and_escort_detail_invented`. |
| `progressive_village_burning` | gameplay_invention | Background roofs ignite/collapse on turns 2/4/6/8 regardless of house results. | Preserves unavoidable damage and visually connects to the direct burned-dawn state; exact roofs and timing are invented. `presentation_and_timing_invented`. |
| `nynaeve_battle_aid` | inferred | Nynaeve tends Haral with ordinary herbs during the defense. | Consistent with her Wisdom role and later inability to cure Tam; no claim of true Healing. `plausible_unseen_care_inferred`. |
| `guided_heal_staging` | gameplay_invention | Recruitment focuses wounded Haral and teaches one player-performed Herb Pouch use. | Teaches the healer role through immediate safe demand. `tutorial_interaction_added`. |
| `green_defenders` | inferred, revised | Preserve Haral plus five unnamed mortal defenders; surviving defenders earn a resolution callback. | Keeps the proven spectacle and visible cost without making their deaths automatic mission failures. `inferred_participants_preserved`. |
| `dedicated_battle_layout` | gameplay_invention | Use `emonds_field_battle` and raise the unique-layout cap to 5. | Isolates the owner-required larger battle from the tutorial and denouement. `presentation_only`. |

## 15. Scene and beat plan

No direct scene may paraphrase the book. Direct dialogue/narration must use short contiguous quotations from `source/private/eotw/`, trimmed to box limits; invented connective text belongs only in inferred/invented scenes.

| Scene ID | Status | Stable beat IDs | Function |
| --- | --- | --- | --- |
| `sc_c2_attack_begins` | direct | `c2_bran_account` | Shortened Bran account opens the frame; retain the clear-night lightning line and hand off quickly to the map. |
| `sc_c2_mission_briefing` | gameplay_invention | `c2_defense_objective`, `c2_homes_threatened` | Explain occupied-door race, blue resident return, quota 3, eight turns, and inn breach in no more than 5 pages. |
| `sc_c2_recruit_mat` | inferred | `c2_named_villagers_join`, `c2_village_defense` | Mat chooses to help; exact Talk timing is staged gameplay. |
| `sc_c2_recruit_egwene` | inferred | `c2_named_villagers_join` | Egwene takes runner/triage responsibility. |
| `sc_c2_recruit_nynaeve` | inferred | `c2_named_villagers_join`, `c2_nynaeve_battle_aid` | Nynaeve joins and immediately identifies Haral as the urgent wound. |
| `sc_c2_nynaeve_first_heal` | inferred | `c2_nynaeve_battle_aid` | One thanks/triage exchange after the player performs the heal; never calls it true Healing. |
| `sc_c2_house_{west,north,east,south}_opened` | gameplay_invention | `c2_defense_objective`, `c2_homes_threatened` | One short resident orientation page; control returns with the resident selected/highlighted and inn indicated. |
| `sc_c2_house_{west,north,east,south}_ruined` | gameplay_invention | `c2_homes_threatened` | One cause page after the on-map layer change; second loss goes directly to quota-impossible failure. |
| `sc_c2_resident_returned` | gameplay_invention | `c2_defense_objective` | Confirms safety and re-highlights unresolved doors or the threshold; no long repeated dialogue. |
| `sc_c2_north_wave`, `sc_c2_flank_wave`, `sc_c2_final_wave` | gameplay_invention | `c2_village_defense`, `c2_defense_objective` | One-page, agent-first spatial warnings after spawn/focus. |
| `sc_c2_unavoidable_damage_{west,east}` | gameplay_invention | `c2_homes_threatened` | Sparse roof-collapse consequence; exact buildings are invented. |
| `sc_c2_failure_inn_breach` | gameplay_invention | `c2_defense_objective` | States that the refuge is no longer safe, then loses. |
| `sc_c2_failure_quota` / `sc_c2_failure_quota_impossible` | gameplay_invention | `c2_defense_objective`, `c2_homes_threatened` | Distinguish dawn shortfall from losing a second occupied house early. |
| resident death failure scenes | gameplay_invention | `c2_defense_objective` | Cause-specific, one page, immediate loss. |
| `sc_c2_defense_tally` | inferred/gameplay-invention branches | `c2_village_defense`, `c2_homes_threatened`, `c2_named_villagers_join` | Briefly acknowledges four-house mastery and/or any unnamed green survivor before the direct frame. |
| `sc_c2_defense_end` | direct | `c2_bran_account` | Preserve Bran/Thom's short direct account that Lan, Moiraine, and other defenders all mattered. |

Lan/Moiraine combat quotes remain gameplay inventions. Add one Nynaeve heal bark and one Mat/Egwene first-danger bark, each `only_once`; do not attach a scene to every ordinary action.

## 16. Implementation acceptance ledger

The later implementation is complete only when all of the following are simultaneously true in source specs and a tmp-compiled runtime probe:

- Dedicated 22×18 map, exact four door coordinates, exact inn regions, 284 walkable tiles, 10 starting enemies, and 28.4 walkable/start-enemy density.
- Campaign layout cap explicitly changes to 5; `wn00` and `wn05` keep their current shared-map coordinates and topology.
- Eight enemy phases occur; success/failure resolves at turn-start 9 and cannot resolve early through kills.
- Three returned residents plus a held threshold wins; two or fewer loses.
- A second ruined occupied house loses immediately; one ruined house remains compatible with victory.
- Any enemy can ruin an unresolved door; any player unit can resolve a door first.
- Every player-resolved door spawns a directly controlled resident, and only entering `inn_safe` increments the quota.
- Saved/ruined door states and turns 2/4/6/8 background damage visibly alter the tactical map.
- Mat and Egwene start other/green, recruit through Talk, and refresh as blue; Nynaeve starts player-controlled.
- Haral begins at 28/40 and is mortal; Healing Herbs use the Item action at range 0–1 and restore exactly 8 HP.
- Named playable deaths offer Restart or Continue instead of silently stopping at 1 HP; story portraits remain available.
- All-four-house mastery reduces the turn-5 wave from two enemies to one; any surviving unnamed green receives a visible resolution callback.
- Waves are actual sizes 2/1-or-2/2 on turns 3/5/7, telegraphed, edge-safe, and the final pair receives two enemy phases.
- Natural and deliberately weak successful playthroughs target 0/8 dead turns; pure turtling loses promptly rather than waiting for dawn.
- Bran's direct frame remains exact quotation; every other tactical line is labeled inferred or gameplay invention with the stable beats above.
