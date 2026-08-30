# Winternight fun review

## Scope and method

This is a fun review, not a fourth correctness round. I reviewed the already-compiled
`build/winternight.ltproj` at report tree
`624deb7b28bf24d1ee32629ef8215204631cf3805f01414eec00c74d30ae22f5` with the pinned
engine. The completed runs used SDL dummy video/audio and posted real pygame key
down/up events; no driver invoked an event directly or changed a unit, flag, HP value,
position, or objective. I inspected the cited native 240x160 PNGs with vision.

The two-run ledger is:

| Mission | Golden / intended run | Deliberately weak run |
| --- | --- | --- |
| `wn00_tutorial` | Complete route with all five optional Talks and explicit inn entry; `/tmp/round2-wn00/golden-run.json`, `/tmp/round2-wn00/golden-summary.json` | Entered the inn approach early, spent four turns waiting/re-entering, then recovered and reached Mat; `/tmp/round2-wn00/early-run.json`, `/tmp/round2-wn00/early-summary.json` |
| `wn01_farm_escape` | Westwood escape on turn 4; `/tmp/wn01-golden.json` | Rand stayed at `[7,7]`, Tam killed every Trolloc by turn 5, then both waited for the turn-8 mercy win; `/tmp/wn01-timeoutfar.json` |
| `wn02_village_defense` | Door/bodyguard defense, all rescues, turn-7 win; `/tmp/wn02-golden-door-result.json` | All rescues, but Lan and Moiraine stayed on their starting tiles after the opening; still won at turn 7; `/tmp/wn02-golden-lazy-result.json` |
| `wn03_return_to_farm` | Sheep pen, all searches, Narg kill, west return, and chapter save; `/tmp/wn03-fun-golden-result.json` | Equipped the Hunting Bow beside Narg and waited; Rand died and Game Over appeared on turn 9; `/tmp/wn03-round3-loss-result.json`, `/tmp/wn03-round3-loss/game-over.png` |
| `wn04_long_road` | Stayed in the trees, no combat, east-edge win on turn 9; `/tmp/wn04-f1-golden-evidence.json` | Moved onto the pale road and waited; the caught scene and Game Over fired on turn 7; `/tmp/wn04-f1-loss-evidence.json` |
| `wn05_out_of_the_woods` | Both optional Talks, Nynaeve interrupt, inn delivery, bonfire leg, ending on turn 5; `/tmp/wn05-round2-golden/result.json` | Used public End through turn 10 without moving; no pressure, state change, or loss occurred; `/tmp/wn05-round2-loss/result.json` |

A **dead turn** is a player turn with one credible action and no risk, reward, ordering,
route, or resource tradeoff. I exclude extra QA-only menu checks and door-crossing probes
from the ratio, but list them when they changed the raw completion turn. A destination
turn counts as dead when reaching the destination is the sole safe action. This is a
strict decision-density measure, not a correctness judgment.

The authored campaign emotion and teaching goals are warmth/attachment -> rupture ->
communal cost -> lonely responsibility -> endurance/identity shock -> costly hope
(`docs/story-plan-v2.md:41-47`; `docs/story-pass.md:15-50`). The review below judges how
well play creates that curve.

## `wn00_tutorial` — An Empty Road

**Verdict: FLAT.** The festival is likable and does the campaign's most important
emotional work: Mat, the village crowd, the two cider deliveries, and the raven make the
Green feel worth losing. The raven sidestep is the correct small chill rather than a
contrived fight (`/tmp/round2-wn00/scenes/golden-085-sc_c0_raven_attack.png`). As a level,
however, almost every required turn is marker-following with one unit. The cask loop
repeats cart -> cellar twice, the raven sequence removes control for five consecutive
scenes, and optional Talks offer character texture rather than tactical consequences
(`design/missions/tutorial_emonds_field.yaml:63-122`). The weak run proved that dawdling
is harmless and recoverable, as a tutorial should be, but also that waiting creates no
new state (`/tmp/round2-wn00/critical/early-repeat-entry.png`). The mechanical verb is
warm, story-appropriate **talk/carry**, but it is exhausted before the chapter ends.

**Decision density:** **7 dead turns / 13 natural all-content turns (54%)**. The actual QA
completion was turn 17 because four explicit door-crossing/wait probes were added after
the raven (`/tmp/round2-wn00/golden-summary.json`). The seven dead turns are Mat, four
mandatory cask interactions, raven, and final inn entry; the six non-dead turns are the
five optional Talks plus the route-order choice they collectively create. A mandatory-
only player gets a much flatter 7/7 sequence.

**Tension curve:** warmth peaks in the optional village contacts; unease peaks at the
scripted raven miss and sidestep, which matches the intended attachment-then-chill shape.
**Peak frame:** `/tmp/round2-wn00/scenes/golden-085-sc_c0_raven_attack.png`.

### Top improvements by fun per effort

1. **Turn the optional Talks into a compact route-planning choice.** Move Egwene, Perrin,
   and Ewin from the map corners onto three different one-turn approaches between the
   cart and cellar, so a player can fold one or two Talks into either cider circuit but
   cannot take all three without a detour. Touch unit positions at
   `design/missions/tutorial_emonds_field.yaml:17-21`; retain the cart/cellar targets at
   `:26-27`. Expected effect: the same canon conversations become a choice between the
   shortest errand route and fuller village attachment, reducing empty acreage without
   adding a mechanic. **Locked contract:** all five Talks remain optional; Mat remains the
   only required Talk; both cider trips remain required.
2. **Compress, do not delete, the repeated cask geometry.** Move `cider_cart` and
   `inn_cellar` one tile closer so either trip fits within one normal 5-MOV selection,
   while retaining four distinct pickup/delivery interactions and both between-trip
   scenes. Touch region coordinates at
   `design/missions/tutorial_emonds_field.yaml:26-27` and the matching festival map
   doorway/road cells only if needed (`design/maps/emonds_field.yaml:20-35`). Expected
   effect: two trips still establish work and friendship, but the second feels like a
   callback rather than another traversal tax. **Locked contract:** two canon cider
   trips, the cellar destination, and zero combat remain.
3. **Make the raven the promised input lesson, but keep it non-combat and scripted.** At
   `design/missions/tutorial_emonds_field.yaml:106-122`, return control for one target-
   selection/confirm interaction against a temporary non-damaging raven target, force
   the authored miss, remove the target, and resume Moiraine's entrance. This requires a
   narrow compiler/adapter addition because the current mission action vocabulary cannot
   stage a harmless scripted forecast. Expected effect: the chapter ends with one
   memorable act the player performed, and Chapter 1 no longer introduces the entire
   attack UI under lethal pressure. **Locked contract:** no enemy battle, no damage, two
   scripted misses, and the raven escaping are inviolable.

## `wn01_farm_escape` — Winternight

**Verdict: MOSTLY FUN.** The rupture works immediately: the player has one fragile runner
and one capable father, and the optional Clean Cloth creates the campaign's first clean
speed-versus-preparation choice (`design/missions/farm_escape.yaml:23-42`). Turns 1-2 ask
who Tam intercepts while Rand chooses direct escape or the kit. The level then loses its
threat: in the turn-4 win, Tam had already killed all three starting Trollocs while the
turn-3 wave remained far behind; the reviewed mid-escape frame contains Rand, Tam, and a
large empty west half rather than a closing pursuit (`/tmp/wn01-mid-escape.png`,
`/tmp/wn01-golden.json`). Worse for fun, the weak run killed all five Trollocs by turn 5,
waited on empty turns 6-7, and received victory from `[7,7]` on turn 8
(`/tmp/wn01-timeoutfar.json`). The fiction bridge is now coherent
(`/tmp/wn01-timeoutfar-dialogue/025-wn01_farm_escape_sc_c1_tam_wounded.png`), but the
mechanical verb **escape** is optional in the route that most thoroughly tests it.

**Decision density:** golden **2/4 dead turns (50%)**: turns 1-2 contain target/kit/route
tradeoffs; turn 3 is simply continue west after the distant wave; turn 4 is the forced
exit. Weak route **3/8 dead turns (38%)**, all after every enemy is dead (turns 6-8).

**Tension curve:** the playable peak is turns 1-2 at the breached house, earlier than an
escape map's desired midpoint. The turn-3 wave does not catch the golden route, so the
curve falls before the Westwood (`/tmp/wn01-mid-escape.png`). **Peak frame:**
`/tmp/wn01-golden-dialogue/023-wn01_farm_escape_sc_c1_pursuit.png`.

### Top improvements by fun per effort

1. **Make turn 8 a visible loss, not a mercy win.** Replace `farm_timeout_success` at
   `design/missions/farm_escape.yaml:60-67` with a turn-8 caught scene and `lose`; add
   `Reach Westwood by dawn` to the initial/turn-3 objective at `:35` and `:48`. Keep the
   wound flags and `sc_c1_tam_wounded` exclusively in `farm_escape_success` at `:52-59`.
   Expected effect: running west is once again mandatory, stalling cannot dominate by
   killing the map, and the optional cloth has a real tempo cost. **Locked contract:**
   Tam's wound remains scripted and performance-independent on successful escape; his
   survival floor remains; the story still proceeds only after Rand reaches safety.
2. **Move the pursuit beat into the actual middle.** Change the two-unit wave from turn
   3 to turn 2 (`design/missions/farm_escape.yaml:20-26,43-48`) and add one explicit east-
   edge warning to the last breach page (`design/scenes/farm_escape/scenes.yaml:55-58`).
   Keep both spawn tiles at least six Manhattan tiles from Tam's plausible turn-2
   position and retain turn-start timing. Expected effect: the new pack enters while
   Rand still has two movement turns left, forcing Tam to choose between covering Rand,
   the cloth lane, and himself. **Locked contract:** no ambush spawn, two-unit wave cap,
   east-edge telegraph, and hopeless standing fight remain.
3. **Cut the pre-control sequence from 22 pages to 16.** Merge the split sword sentence
   and remove redundant command/escalation pages across
   `design/scenes/farm_escape/scenes.yaml:14-58`, preserving calm -> locked door -> sword
   -> breach -> “run west.” Expected effect: the first combat begins before the player
   has spent longer clicking than moving, while the domestic calm still makes the
   rupture matter. **Locked contract:** sword reveal, kettle throw, Tam killing two,
   and the scripted escape handoff remain.

## `wn02_village_defense` — The Village Burns

**Verdict: FUN.** This is the campaign's tactical high point. Three outward rescues pull
attention away from the inn, Lan and Moiraine have target/heal/formation choices every
turn, the green line creates spectacle, and Haral's falling HP gives those choices a
human stake. The door formation won with Lan/Moiraine/Haral at 31/31/15 HP; the
intentionally lazy formation also won but consumed all five unnamed greens and left
Haral at 12/40 (`/tmp/wn02-golden-door-result.json`,
`/tmp/wn02-golden-lazy-result.json`). That is a good “success with visible cost” result.
The one weakness is expression: both player formations win, the arsonist branch resolves
on the normal combat line, and the turn-6 flank units are still alive near the extreme
edges when victory fires at turn 7. Thus the final wave reads more as spectacle than a
new decision (`design/missions/village_defense.yaml:39-47,98-109`). The mechanical verb
**rescue/hold** matches communal cost for all six turns and does not collapse into a pure
turtle.

**Decision density:** **0/6 dead turns (0%)** in both reviewed wins. Even when Lan and
Moiraine held their starting tiles, each turn retained attack/heal/target choices while
Haral and green casualties changed the risk. The lazy win exposes low positional demand,
not empty turns.

**Tension curve:** pressure builds correctly: outward rescue on turns 1-2, green losses
and converging enemies on turn 3, north wave plus unavoidable roof collapse on turn 4,
and Haral at his lowest as the final phase resolves. The emotional peak is the roof loss;
the tactical peak is the green line collapsing around Haral.
**Peak frame:** `/tmp/wn02-golden-lazy/enemy-phase-green-fight.png` (supporting story beat:
`/tmp/wn02-golden-lazy/sc_c2_unavoidable_damage-01.png`).

### Top improvements by fun per effort

1. **Give the flank wave two enemy phases.** Move `flank_wave` from turn 6 to turn 5 at
   `design/missions/village_defense.yaml:41-47,98-100` and add a one-page edge warning in
   the same turn-start event. Do not change its two-unit size or edge tiles. Expected
   effect: the wave reaches a lane the player must answer before turn-7 resolution,
   instead of ending alive at `[2,9]` and `[17,9]`; turns 5-6 become a reformation test.
   **Locked contract:** six-turn hold, fair player-phase reaction, two-unit wave cap, and
   six green allies remain.
2. **Make saving the threatened home reduce later pressure.** Split the flank into a
   one-unit `flank_saved` group and the current two-unit `flank_full` group. At turn 5,
   spawn the first when `home_saved` is true and the second when it is false; retain
   `arsonist_defeated` at `design/missions/village_defense.yaml:82-86` and `home_burns` at
   `:101-105`. Expected effect: sending Lan or Moiraine toward the torchbearer becomes a
   concrete present-risk/future-safety tradeoff rather than scene-only credit. **Locked
   contract:** unavoidable village damage still occurs; this can save one home, not the
   village; total annihilation stays unnecessary.
3. **Reward, never require, preserving green defenders.** Set five `green_*_alive` flags
   at `defense_start` (`design/missions/village_defense.yaml:49-57`), clear the matching
   flag on each unnamed defender's death, and branch one short victory page before
   `defense_win` (`:106-109`) if any survives. Expected effect: the lazy fixed-position
   win remains legal, but mastery gains a visible goal that invites proactive formation
   changes and gives green HP real value. **Locked contract:** all five unnamed defenders
   may still fall without loss; Haral alone remains mortal and protected.

## `wn03_return_to_farm` — The Ruined Farm

**Verdict: MOSTLY FUN.** The house search is the campaign's best story-mechanic match:
water, cloth, blankets, and sword all mean care rather than loot; the player chooses the
three-supply order under radius-3 fog; the sheep pen is a strong optional dread beat; and
Narg is a fair, memorable spike. The golden run could kill him after surviving one hit,
while the bad loadout/wait run died promptly on turn 9. The Narg reveal is clean and
menacing at native resolution (`/tmp/wn03-fun-golden/event-wn03_return_to_farm_sc_c3_trolloc_appears-04.png`).
The weakness is that fog conceals no active tactical threat before the scripted spawn, so
it supplies atmosphere more than resource discipline. After Narg dies, the whole four-
turn west return is foregone movement. The verb **search/care** remains novel through the
sword, then becomes a long walk.

**Decision density:** **7/11 dead turns (64%)** for the natural all-content equivalent.
The exercised route also spent one deliberate early-exit probe turn and therefore used
12: excluded probe, then sheep visit, farmhouse, three orderable supplies, sword, Narg
fight, and four west-return turns (`/tmp/wn03-fun-golden-result.json`; mission gates at
`design/missions/return_to_farm.yaml:39-109`). The dead turns are farmhouse, the last
remaining supply, sword, and four post-kill return turns. The deliberate-loss route had
one bad but legible equipment choice followed by an immediate consequence, not a soft
wait.

**Tension curve:** quiet dread rises through the dead flock and care items, peaks sharply
at Narg's reveal/first strike, then collapses completely after his death. This matches
lonely responsibility until the empty return tail.
**Peak frame:** `/tmp/wn03-fun-golden/event-wn03_return_to_farm_sc_c3_trolloc_appears-04.png`.

### Top improvements by fun per effort

1. **Make the authored 12-turn maximum real.** Add a turn-10 Tam-fever warning and a
   turn-13 loss event to `design/missions/return_to_farm.yaml:106-126`, with the initial
   and farmhouse objectives briefly naming the deadline. Expected effect: supply order,
   rubble cost, sheep-pen detour, healing, fighting, and evasion finally share one scarce
   resource: time. **Locked contract:** the first-time expected route must remain
   survivable; Tam's story outcome is never produced by deliberate player failure; Narg
   still cannot one-round Rand.
2. **Reward defeating Narg with a shorter return; keep the long escape for evasion.** Add
   an inactive `westwood_quick_exit` region around `[4,5]`; activate it in
   `trolloc_defeated` at `design/missions/return_to_farm.yaml:101-105`. Keep the existing
   `[0,5]` exit and `narg_encountered` gate at `:23,106-109` for a player who leaves Narg
   alive. Expected effect: kill versus evade becomes mastery-versus-safety, and the kill
   route loses two to three empty westward turns. **Locked contract:** evasion remains
   legal, encounter remains required, and both branches return Rand west to Tam with all
   supplies.
3. **Give the sheep-pen detour information value.** After `sc_c3_dead_flock`, add
   `set_fog: 4` and `highlight_target: farmhouse_approach` to the event at
   `design/missions/return_to_farm.yaml:39-45`. Expected effect: the player spends one
   turn for story and a larger planning horizon, turning the optional Visit into a real
   information-versus-speed choice. **Locked contract:** the mandatory ruin remains
   fogged, radius never drops below 3, and no enemy attacks before Narg's authored reveal.

## `wn04_long_road` — The Long Road

**Verdict: MOSTLY FUN.** This is the campaign's most memorable concept and strongest
narrative tension: three-MOV litter travel, the marching column, sweepers, the returning
rider, and detection loss make the road itself the enemy. The golden route's end
positions `[4,6] -> [7,6] -> [9,7] -> [12,7] -> [15,7] -> [18,7] -> [20,6] -> [23,6] ->
[25,6]` show that deadfalls and blockers force lane changes; no combat occurred
(`/tmp/wn04-f1-golden-evidence.json`). The bad road position produces an immediate,
readable turn-7 failure (`/tmp/wn04-f1-loss/loss-road-turn6.png`). Yet the player never
actually hides: from turn 1 through turn 9 the correct verb is always “move maximum east
off road.” The returning rider changes the objective text and emotion, but not the input.
The watched-road frame also centers Rand while the rider remains off-screen, weakening
the set piece's spatial menace (`/tmp/wn04-f1-golden/watched-road-highlight.png`).

**Decision density:** **4/9 dead turns (44%)**. Turns 1-3 and 6-7 contain lane/deadfall or
exposure choices; turns 4-5, 8, and the turn-9 exit play themselves. This gives more route
mastery than a straight corridor, but only one unit and one cardinal objective keep the
ceiling low.

**Tension curve:** the column creates early unease, sweepers raise tempo on turn 5, and
the rider's return on turn 6 is the intended campaign gameplay peak. Pressure remains
high until release on turn 9, then the Dragonmount speech supplies the emotional peak.
**Peak frame:** `/tmp/wn04-f1-golden/watched-road-highlight.png`.

### Top improvements by fun per effort

1. **Restore a real hold-still hide decision.** Add two one-tile `Hide` regions in the
   lower tree lanes and activate them at `rider_halts`
   (`design/missions/long_road.yaml:66-81`). Entering one sets `rand_hidden`; on turn 7,
   failure fires if that flag is false. Change `sweep_a`/`sweep_b` to `do_nothing` during
   turns 6-8 and restore `pursue` in `rider_leaves` (`:82-96,104-108`). Expected effect:
   turns 4-6 become a choice of which shelter can be reached, followed by one earned held-
   breath pause instead of more east input. **Locked contract:** Tam stays carried,
   column/rider remain non-attacking, detection loses, and the canonical scripted hide
   and rider return remain.
2. **Start sweeper pressure one turn earlier, with warning.** Add a short west-edge bark
   on turn 3 and move `sweep_wave` from turn 5 to turn 4 at
   `design/missions/long_road.yaml:38-47,104-108`. Keep the same two units and turn-start
   timing. Expected effect: route-cost mistakes on turns 2-4 matter before the rider set
   piece, reducing two corridor turns that currently coast. **Locked contract:** no
   enemy-phase ambush, no combat objective, and the last spawn remains no later than turn
   6.
3. **Show the rider before showing the danger strip.** Add a one-tile inactive
   `rider_stop` marker at `[25,3]`; in `rider_halts`, highlight that marker immediately
   after spawning the rider, play the stop scene, then highlight `rider_watch` before
   returning control (`design/missions/long_road.yaml:40-42,66-81`). Expected effect: the
   player sees the agent of detection and its relationship to the road, making the
   campaign's mechanical peak spatially memorable. **Locked contract:** no attack AI or
   combat is added; the existing pale-road warning remains.

## `wn05_out_of_the_woods` — Out of the Woods

**Verdict: MOSTLY FUN.** As tactics this is deliberately light; as a denouement it earns
its place. Rand and Tam can be scheduled independently, Luhhan/Egwene Talks make speed
versus closure optional, Nynaeve's refusal interrupts the route, and the second leg turns
the old festival Green into a walk toward funeral fires. The golden route fits all of
that into five turns and lands the emotional peak cleanly
(`/tmp/wn05-round2-golden/frames/109_wn05_out_of_the_woods_sc_c5_any_price.png`). The weak
run exposes the cost of having no soft pressure: ten End turns leave every unit, Talk,
objective, and HP value unchanged (`/tmp/wn05-round2-loss/turn10-no-loss.png`). That must
not be “fixed” with enemies or a lethal timer, but it does make the mechanical verb
**walk/ask for help** inert if the player refuses to participate.

**Decision density:** golden **2/5 dead turns (40%)**: turns 1-3 let the player schedule
two units and two optional Talks around delivery; turns 4-5 are the sole route to the
bonfires. Weak route **10/10 dead turns (100%)** after the player chooses to stall, with no
escalation. A public-input death path does not exist, correctly, because the locked
zero-enemy denouement has no damaging action (`design/missions/out_of_the_woods.yaml:15-18,32,83-89`).

**Tension curve:** this is an emotional falling-and-rising curve, not a danger curve:
burned-dawn reveal -> Nynaeve closes the ordinary-help door -> Bran/Thom name the last
chance -> “any price” at the bonfires. It matches “arrival is not safety” and provides the
necessary release after Chapter 4.
**Peak frame:** `/tmp/wn05-round2-golden/frames/109_wn05_out_of_the_woods_sc_c5_any_price.png`.

### Top improvements by fun per effort

1. **Make Luhhan's help mechanical as well as textual.** In `luhhan_talk`, set a one-shot
   `luhhan_helped` flag (`design/missions/out_of_the_woods.yaml:43-48`). Add a one-shot
   `unit_wait` event for `tam_litter`, conditioned on that flag, which refreshes Tam after
   his first move. Expected effect: moving Tam before Rand detours to Luhhan earns one
   assisted extra litter move, so story-first routing can match the direct route and
   Luhhan visibly takes the other end of the load. **Locked contract:** no enemy, damage,
   or invented fate; Tam remains delivered to and removed at the inn.
2. **Add nonlethal fever escalation for dawdling.** Add short turn-start barks on turns 4,
   6, and 8 while `tam_at_inn` is false, with the turn-8 event repeating the inn highlight
   and objective (`design/missions/out_of_the_woods.yaml:34-70`). Never call `lose`.
   Expected effect: empty End turns acknowledge Tam's condition and keep the story clock
   moving without turning the denouement into punishment. **Locked contract:** zero
   enemies, no hard timeout, and ordinary medicine still fails before Moiraine is sought.
3. **Pay off both optional Talks at the bonfire without changing canon.** Set explicit
   `talked_luhhan`/`talked_egwene` flags in the current events (`:43-54`) and, when both are
   true, play one concise callback narration before `sc_c5_any_price` at `:71-77`—for
   example, Rand arriving with the village's voices behind his decision, without new
   dialogue or lore. Expected effect: the optimized all-Talk route gains a visible
   mastery payoff and the final plea feels campaign-earned. **Locked contract:** no new
   lore claim, no scene after the ending boundary, and the any-price/promise order remains.

## Campaign-wide judgment

### Curve chart in prose

**P: low pressure / high warmth -> C1: sharp but short panic -> C2: sustained tactical
peak -> C3: atmospheric valley with one duel spike -> C4: narrative tension peak with
medium tactical density -> C5: near-zero pressure and emotional release.** That is a good
story curve and a less consistent strategy curve. The teaching ladder is readable:
move/Talk/interact, then attack/escape, then multi-unit rescue/hold, then fog/search/solo
resource risk, then carried movement/detection, then a no-enemy synthesis of movement and
Talk (`docs/story-plan-v2.md:44-47`). The objectives are unusually varied for six chapters
and no chapter uses filler rout.

The difficulty spike is Chapter 2, not Chapter 4: Chapter 2 is the only mission with
continuous per-turn target/heal/formation choices, while Chapter 4's threat is memorable
but usually solved by maximum east movement. Chapter 3's Narg hit is the campaign's best
small mastery check. Chapter 5 is an appropriate valley, provided it remains short.

The six authored minute windows sum to **62-100 minutes**, inside the campaign contract
`[60,100]` (`design/campaign.yaml:18-20`; mission `target_play` entries). The played turn
counts also fit the intended macro rhythm: natural tutorial about 7 mandatory / 13 all-
content turns, C1 4, C2 fixed 6, C3 about 11 natural all-content, C4 9, C5 5. The likely
pacing risk is not map length but mandatory text concentration: Chapter 1 has 22 pages
before its four-turn mission, while Chapter 5's five turns sit among 140 settled text/card
frames (`/tmp/wn01-golden.json`, `/tmp/wn05-round2-golden/result.json`). Keep the campaign
inside the target by trimming clicks and dead travel, not by removing story beats.

### Single highest-leverage cross-cutting change

**Make optional content change the next tactical state.** The campaign already authors
excellent optional material—the Clean Cloth, arsonist/home, sheep pen, hide route, village
Talks—but only the Clean Cloth presently changes the player's resources. Apply one small,
visible mechanical payoff per chapter: route-efficient Talks in P, cloth in C1, reduced
flank pressure/home and green-survivor acknowledgment in C2, information radius at the
sheep pen in C3, chosen shelter in C4, and Luhhan refreshing Tam in C5. This creates the
campaign-wide expression it currently lacks: speed versus preparation, safety versus
story, and mastery that is visible without adding filler enemies or contradicting canon.

### What already works and must not be touched

- **The emotional/place-state spine:** festival Green -> burning Green -> burned dawn, and
  whole farm -> breach -> fogged ruin. Reuse communicates loss better than another map
  would (`docs/story-pass.md:52-66`).
- **Objective variety and verbs:** talk/carry, escape, rescue/hold, search, hide/carry, and
  walk/ask for help. Do not normalize these into rout or defeat-boss maps.
- **Chapter 2's locked spectacle:** six green allies, mortal protected Haral Luhhan,
  expendable unnamed defenders, and unavoidable village cost. Improve incentives, not
  the contract (`design/missions/village_defense.yaml:126-135`).
- **Story-critical determinism:** Tam's wound remains scripted; Narg cannot one-round
  Rand; Chapter 4's column/rider remain non-combat detection threats; Chapter 5 remains
  zero-enemy; no recommendation should require player failure for canon.
- **Fair reinforcement timing:** all reviewed waves arrive at turn start with a player
  reaction phase. Keep that and telegraph every changed edge.
- **The repaired native presentation:** objectives and text now fit at 240x160, and the
  reviewed emotional peaks read cleanly. Add mechanics and shorten pacing without
  reopening the completed correctness fixes.
