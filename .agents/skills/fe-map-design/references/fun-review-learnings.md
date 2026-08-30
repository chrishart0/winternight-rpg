# Fun-review learnings

Use this reference with [`../SKILL.md`](../SKILL.md). It separates **repo-earned** rules from **imported** patterns so future authors do not mistake outside examples for Winternight playtest evidence.

## Evidence base

**Repo-earned.** The primary source is the full [Winternight fun review](../../../../docs/qa/fun-review.md), run against compiled report tree `624deb7b28bf24d1ee32629ef8215204631cf3805f01414eec00c74d30ae22f5` with the pinned engine. Its driver sent real pygame key events; it did not invoke events or edit unit, flag, HP, position, or objective state. Native 240×160 captures support the spatial and emotional findings.

### Fun review method

Run each mission twice:

1. **Golden run:** play the intended route, exercise all authored optional content, and finish naturally.
2. **Deliberately weak run:** use only public player inputs but under-engage the mission's core verb—stall, hold a lazy formation, choose a bad loadout, or take the exposed route. Do not corrupt state or manufacture a failure.

Use this verdict scale:

- **FUN:** the core verb stays decision-bearing through the target window; remaining changes are expression or polish.
- **MOSTLY FUN:** the core verb works, but a tail, wave, payoff, or alternate route collapses.
- **FLAT:** the chapter is coherent and may be pleasant, but mandatory play is dominated by foregone inputs.
- **NOT FUN:** fair play repeatedly produces frustration, arbitrariness, or a collapsed core verb. The 2026 review needed no `NOT FUN` verdict.

A review must cite:

- the compiled report-tree hash and pinned engine;
- artifact paths for both runs and the exact natural completion turn;
- a turn-by-turn state or input ledger, with QA-only probes separated from natural play;
- the dead-turn numerator, denominator, and rationale for every counted turn;
- at least one native-resolution peak frame and, when available, a weak-route failure or stall frame;
- the mission/map/scene source lines that caused the behavior;
- the core player verb, tension curve, verdict, and contracts that a proposed fix must preserve.

The review's run ledger is in its [Scope and method](../../../../docs/qa/fun-review.md#scope-and-method) section. Representative weak-run artifacts were `/tmp/wn01-timeoutfar.json`, `/tmp/wn02-golden-lazy-result.json`, `/tmp/wn03-round3-loss-result.json`, `/tmp/wn04-f1-loss-evidence.json`, and `/tmp/wn05-round2-loss/result.json`.

## Dead-turn metric

**Repo-earned.** A **dead turn** is a player turn with one credible action and no risk, reward, ordering, route, or resource tradeoff. Count the entire player turn, not button presses or unit actions.

Counting rules:

1. Use the natural route from gaining control through victory.
2. Count a destination turn as dead when reaching the destination is the sole safe action.
3. Count forced interaction and travel turns when no credible alternative changes state.
4. Do not count extra QA-only menu checks, deliberate door probes, or input verification; report those only in the raw completion turn.
5. Report `dead turns / natural turns` and annotate any deliberate weak-run waits separately.
6. Treat the ratio as a diagnostic, not a universal pass line. Placement matters: a three-turn dead tail can invalidate an objective even when its whole-run ratio looks lower than another mission's.

Observed ratios:

| Mission archetype | Intended run | Weak or mandatory-only run | Evidence-backed reading |
| --- | ---: | ---: | --- |
| Tutorial talk/carry (`wn00`) | 7/13 (54%) | 7/7 mandatory-only (100%) | Optional Talks create all route ordering; mandatory play is marker-following. |
| Escape (`wn01`) | 2/4 (50%) | 3/8 (38%), all on turns 6–8 | The lower weak-run ratio is misleading: the dead tail wins without escaping. |
| Defend/rescue (`wn02`) | 0/6 (0%) | 0/6 (0%) lazy formation | Haral HP, green losses, targets, healing, and formation keep changing risk even when positioning demand is low. |
| Search/escape (`wn03`) | 7/11 (64%) | loss route had a legible bad choice, not a soft wait | Ordered searches and Narg work; the forced search endpoints and four-turn post-kill return do not. |
| Stealth/carry (`wn04`) | 4/9 (44%) | exposed-road route loses on turn 7 | Lane choices work, but four maximum-east turns play themselves. |
| Zero-pressure denouement (`wn05`) | 2/5 (40%) | 10/10 (100%) stall | Scheduling and Talks work early; the last walk and indefinite End turns have no state response. |

Do not compare ratios without archetype and placement. `wn02` proves a fixed hold can sustain 0% dead turns. `wn01` proves a stall route can be structurally worse despite a lower aggregate ratio. See each mission section in the [review](../../../../docs/qa/fun-review.md).

## Earned mission rules

### Optional content must change the next tactical state

**Repo-earned.** Texture alone did not create campaign-wide player expression. Use one small, visible payoff per chapter:

| Chapter pattern | Tactical payoff |
| --- | --- |
| Prologue Talks | Put Talks on competing useful approaches so choosing them changes route efficiency. |
| Chapter 1 Clean Cloth | Keep the item as a speed-versus-preparation resource choice. |
| Chapter 2 threatened home / green defenders | Saving the home reduces the next flank; preserving greens earns a visible resolution callback without becoming required. |
| Chapter 3 sheep pen | Trade one detour turn for information by increasing the next fog-planning radius. |
| Chapter 4 hide choice | Let the selected shelter set the next safe state instead of merely changing text. |
| Chapter 5 Luhhan Talk | Refresh the litter after its first move so accepting help changes the immediate carry schedule. |

Reject optional content whose only result is an isolated line and unchanged position, HP, inventory, information, action economy, pressure, route, or later callback. Preserve optionality: the payoff may improve or alter the route, but must not silently become required.

### Objective verbs and tension peaks

**Repo-earned unless marked imported.** Place the peak to fit the verb:

| Objective shape | Peak placement |
| --- | --- |
| Tutorial | Let optional social routing carry warmth; end with one brief player-performed chill, not a long control lock. |
| Escape | Peak near the playable midpoint, while route and cover choices remain. A door breach is setup, not the peak; keep pressure alive on the final approach. This agrees with the imported RandomWizard escape-map analysis already cited by the skill. |
| Defend/rescue | Build late; every final wave must receive enough enemy phases to change a player decision before victory. |
| Search/care | Peak at the authored reveal or resource test, then shorten the resolved return tail. |
| Stealth/carry | Peak at the detection set piece after route mastery is established, then sustain pressure briefly before release. |
| Denouement | Peak emotionally near the final plea or consequence; do not create a new danger peak after the campaign climax. |

**Set-piece staging:** show the threat agent on screen before highlighting the danger it causes. In `wn04`, highlighting the watched road while the returning rider remained off-screen weakened the spatial relationship. The corrective sequence is `spawn/show agent → focus or marker → scene → highlight danger zone → return control`.

### Mercy timeout is objective erasure

**Repo-earned.** A timeout that grants victory after the player stalls converts the displayed verb into optional flavor. In `wn01`, Rand could remain at `[7,7]`, Tam could clear every Trolloc by turn 5, and turn 8 still awarded victory. That route made **escape** unnecessary. A movement-objective timeout must lose, change into another explicit objective that still demands play, or not exist. Never use a mercy win to conceal an overlong or soft map.

### Text-concentration budget

**Repo-earned.** Record mandatory A-press pages before first control beside natural mission turns. For short chapters, treat more than **4 pre-control pages per natural gameplay turn** as over budget unless a played review earns the exception. `wn01` shipped at 22 pages before a four-turn escape (5.5 pages/turn); the review's bounded correction was 16 pages (4.0 pages/turn). Merge redundant pages and dead travel before deleting story beats. Also inspect total settled frames around very short missions: `wn05` had five gameplay turns among 140 settled text/card frames.

### Zero-pressure denouement

**Repo-earned + imported.** Keep a zero-enemy denouement zero-enemy. Do not add a hard timeout or lethal failure to make it “tactical.” Respond to stalls with nonlethal escalation: short condition barks, changed objective language, repeated highlights, visible environment progression, or callbacks to optional actions. Escalation must acknowledge urgency without changing the chapter into combat or implying ordinary village treatment can cure a story-unique condition.

## Imported research, translated for this repo

### Introduce healers through an immediate safe heal

**Imported.** Fire Emblem repeatedly pairs an early healer with immediate role demand:

- *The Blazing Blade* Chapter 5 forces Serra's recruitment, places Erk already injured, forces Serra to heal him, then releases the player. [Beyond the Borders](https://fireemblemwiki.org/wiki/Beyond_the_Borders)
- *The Sacred Stones* Chapter 5 adds level-1 Cleric Natasha automatically with Mend and uses her for a guided support verb—Talk to recruit Joshua—on Easy Mode. [Natasha](https://fireemblemwiki.org/wiki/Natasha)
- *Awakening* adds level-1 Cleric Lissa automatically in the prologue with Heal; she is the only early healer, so ordinary early damage supplies repeated staff use. [Lissa](https://fireemblemwiki.org/wiki/Lissa)
- Staff use awards experience by the staff used rather than by enemy level; basic healers can progress without taking kills. [Staff](https://fireemblemwiki.org/wiki/Staff)

Apply only the actionable pattern:

1. Introduce the healer within one move of a pre-injured ally and outside immediate lethal threat.
2. Guide exactly one valid heal, show HP and any staff EXP change, then release full control.
3. Ensure later turns offer heal-versus-position/order choices; do not create a one-action tutorial prop.
4. Keep an unpromoted dedicated healer fragile and support-focused, but give the player direct control rather than defensive AI babysitting.
5. Tune a weak heal to preserve attrition and formation choices. Distinguish combat HP recovery from story-locked illness: ordinary village care must not read as capable of curing what only Moiraine's later Healing can address.

### Make escort/carry a controlled tradeoff, not AI babysitting

**Imported.** General escort analysis identifies three recurring failures: the mechanic is bolted onto the core game, an autonomous NPC controls the pace, and infinite waves turn early damage into an attrition spiral. It recommends player control over pace and finite pressure. [Game Developer, “Can we Fix Escort Mission Game Design?”](https://www.gamedeveloper.com/design/can-we-fix-escort-mission-game-design-)

Fire Emblem's Rescue command instead makes carrying an explicit player action: the traveler is protected and inactive, the carrier pays skill/speed or movement penalties, and allies can Give/Take/Drop the traveler. [Rescue command](https://fireemblemwiki.org/wiki/Rescue_(command)) XCOM likewise puts a non-offensive VIP under direct player control rather than autonomous pathfinding. [UFOpaedia, Escort](https://www.ufopaedia.org/index.php/Escort_(EU2012))

For this repo:

- Give the player deterministic control of the carrier or escorted unit and its pace.
- Make carrying change movement, action economy, route, exposure, or handoff options on the next turn.
- Keep threats finite, telegraphed, and timed to the carrier's actual progress.
- Let the protected traveler remain inactive; do not add unreliable follower AI.
- Do not make a carry unit only an extra loss condition. If removing the cargo leaves the same optimal route and formation, redesign the mission.

### Design falling action as consequence, not a second climax

**Imported.** The Level Design Book recommends alternating highs and lows, treats low-intensity areas after hard encounters as rewards, and warns that a maximum-intensity final encounter can rob the climax of impact. [Pacing](https://book.leveldesignbook.com/process/preproduction/pacing) Fire Emblem commonly reflects supports, survival, and route choices in ending dialogue and cards. [Multiple endings](https://fireemblemwiki.org/wiki/Multiple_endings)

For a playable tactics denouement:

- Keep the mechanical pressure below the prior climax and the critical path short.
- Spend interaction budget on immediate consequences, returns to changed places, and callbacks to optional actions.
- Preserve agency through route/order/Talk choices, not a surprise enemy or punishment timer.
- End soon after the emotional peak; do not append a foregone traversal tail.

## Source index

### Repository evidence

- [Winternight fun review](../../../../docs/qa/fun-review.md), especially “Scope and method,” each mission's decision-density/tension sections, and “Campaign-wide judgment.”

### External research

- Fire Emblem Wiki, [Beyond the Borders](https://fireemblemwiki.org/wiki/Beyond_the_Borders), [Natasha](https://fireemblemwiki.org/wiki/Natasha), [Lissa](https://fireemblemwiki.org/wiki/Lissa), [Staff](https://fireemblemwiki.org/wiki/Staff), [Rescue command](https://fireemblemwiki.org/wiki/Rescue_(command)), and [Multiple endings](https://fireemblemwiki.org/wiki/Multiple_endings).
- Josh Bycer, [“Can we Fix Escort Mission Game Design?”](https://www.gamedeveloper.com/design/can-we-fix-escort-mission-game-design-), *Game Developer*.
- [“Escort (EU2012)”](https://www.ufopaedia.org/index.php/Escort_(EU2012)), UFOpaedia.
- [“Pacing”](https://book.leveldesignbook.com/process/preproduction/pacing), *The Level Design Book*.
