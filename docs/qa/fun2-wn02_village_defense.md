# Fun review 2 — `wn02_village_defense`

## Verdict

**MOSTLY FUN — target missed.** The redesigned chapter is the campaign's strongest battle once the three-house route is established: recruiting changes the roster immediately, the resident return lines cross real enemy pressure, the map visibly deteriorates, and turns 7–8 remain live because the final southern pair reaches the inn approach before dawn. Both successful reviewed strategies had **0/8 dead turns**, preserving the old chapter's **0/6** golden and weak baseline while adding two decision-bearing turns.

It is not yet the campaign's unqualified best mission. The reviewed all-four mastery attempts both fell back to the legal three-house win, the formal Loss Conditions screen contradicts the quota, the guided-heal page scrolls away the words that say who must move beside whom, and repeated public-input neglect did not produce the required Haral-death cause path. Those are player-facing comprehension/expression failures, not style notes.

## Provenance and method

- Gated report tree: `a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a`.
- Isolated deterministic QA compile tree: the same `a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a`; manifest content hash `66ae29c77499452da30f6abba3156f5ac0276e12c741047f9b7e98a8d3d51207`.
- Engine pin: `1820e585450f6f47605aebd686b2a3f13af181f0`.
- Every cited run used SDL dummy video/audio and posted real pygame key-down/up events. No run invoked a mission event, warped a unit, changed HP/flags, or edited the compiled project.
- Reviewed PNGs are native 240×160 frames and were opened with vision.
- Mandatory pre-control text: **11 settled A-press pages / 8 natural turns = 1.375 pages per turn**, under the 4:1 budget. Contact sheet: `/tmp/fun2-wn02-opening-contact.png`.

## Dual-run fun protocol

### Run 1 — intended recruitment/heal/three-house recovery

Artifact: `/tmp/fun2-wn02-golden-result.json`.

The run used the preferred Lan→Mat→Egwene and Moiraine→Nynaeve chain, performed Nynaeve's guided Herb Pouch use on Haral, sent Egwene west, Mat north, Nynaeve south, and attempted Moiraine east. West and south residents returned on turn 2; north was saved on turn 3 and returned on turn 6; the east house was ruined. The quota became 3 before turn 7, then the party held through both final enemy phases and won at turn-start 9. Haral remained 36/40 in the turn snapshots.

**Dead-turn ledger: 0/8.**

| Turn | Live choice that prevents a dead turn |
| ---: | --- |
| 1 | Recruit order, west Visit, exact heal tile, and resident first move compete. |
| 2 | North/south/east races compete with attacks and the first two returns. |
| 3 | North Visit, failed east race, wave reaction, and north-resident routing split attention. |
| 4 | North escort, center formation, targets, and the first collapsed roof compete. |
| 5 | The flank wave arrives while the north resident is still outside. |
| 6 | Deliver north versus attack/heal/re-form; the south warning announces the next obligation. |
| 7 | Quota is complete, but the final pair appears and the threshold line must be set. |
| 8 | Attack, body-block, and preserve-green choices remain live through the final enemy phase. |

### Run 2 — swapped east/south mastery attempt

Artifact: `/tmp/fun2-wn02-mastery-result.json`.

This legitimate alternate swapped the long assignments after the same recruit/heal opening: Nynaeve went east and Moiraine south. It also recovered to a legal three-house win at turn-start 9 rather than reaching the authored all-four tally. The result proves useful tactical expression—different runners and center timing still win—but it does **not** prove the all-four branch. Neither reviewed all-four attempt set all four `house_*_saved` flags or played `sc_c2_defense_tally_mastery`.

**Dead-turn ledger: 0/8.** The alternate changed who was exposed on the long spoke and who could support the inn, while retaining the same turn-by-turn decision categories above. Raw and natural turn counts were both 8; QA-only camera tours did not consume unit actions or turns.

**Baseline comparison:** old golden **0/6 → 0/8**; old weak **0/6 → 0/8** for both successful redesigned strategies. The ratio remains 0%, but the redesign adds two non-dead late turns and substantially more route/ordering expression.

## Tension and visual evidence

- **Core verb:** race outward, bring people home, then hold the inn.
- **Curve:** turn 1 recruitment/heal; turns 2–3 maximum spatial stretch; turns 4–6 escort and re-formation; turns 7–8 defense peak.
- **Tension peak:** `/tmp/fun2-wn02-golden/tension-peak-turn8.png`. The final southern pair has reached the crowded inn apron; blue, green, and enemy bodies contest the same two approach columns while the objective still reads `Return 3 / Hold inn 8 turns`.
- Final pair placement before contact: `/tmp/fun2-wn02-golden/turn7-final-wave.png`.
- Turn-6 advance warning: `/tmp/fun2-wn02-golden/turn6-sc_c2_south_warning-01.png`.
- Turn-7 agent warning: `/tmp/fun2-wn02-golden/turn7-sc_c2_final_wave-01.png`.
- North wave warning: `/tmp/fun2-wn02-golden/turn3-sc_c2_north_wave-01.png`.
- Burn progression, actually viewed: `/tmp/fun2-wn02-burn-progression-contact.png` (turn-2 west fire → turn-4 west rubble → turn-6 east fire → turn-8 east rubble). The fire/rubble states are visually distinct at native resolution.
- Door states, actually viewed: `/tmp/fun2-wn02-door-states-contact.png`. Open doors retain the green Visit brackets, saved doors lose the active bracket and close, and ruined doors become unmistakable flame/rubble. The ruin state is much stronger than the saved-state tile, but the action cue plus resident-spawn feedback kept the race readable.

## Regression checks

| Contract | Result | Evidence |
| --- | --- | --- |
| Objective stated before control | **PASS** | Five concise briefing pages in `/tmp/fun2-wn02-opening-contact.png`; persistent map objective visible in door/burn/peak frames. |
| Recruits telegraphed and satisfying | **PASS** | `/tmp/fun2-wn02-recruits-contact.png`; all three convert to blue and act in the same turn through refresh. Mat names north, Egwene names west, Nynaeve points to Haral. |
| Guided item targeting works | **PASS mechanically / text finding below** | `/tmp/fun2-wn02-alternate/guided-heal-item-menu.png`, `/tmp/fun2-wn02-alternate/guided-heal-targeting.png`; the target panel shows Haral at 28/40 and Herb Pouch, followed by the Haral/Nynaeve acknowledgment. |
| `mending_weave` exposed | **PASS** | `/tmp/fun2-wn02-mending-result.json`, `/tmp/fun2-wn02-mending/mending-weave-spell-menu.png`, and `/tmp/fun2-wn02-mending/mending-weave-targeting.png`; real `Spells` input selected Mending Weave, targeted Haral at 36/40, and restored him to 40/40. |
| Four-house race / door states | **PASS for quota route; FAIL for mastery proof** | Saved/ruined layers and cause scenes fire; however `/tmp/fun2-wn02-golden-result.json` and `/tmp/fun2-wn02-mastery-result.json` both win with east ruined, and neither plays the mastery tally. |
| Progressive burn layers | **PASS** | `/tmp/fun2-wn02-burn-progression-contact.png`. |
| Waves telegraphed and player-phase-safe | **PASS** | Turn-3, turn-5, turn-6, and turn-7 event traces plus the warning frames above; final pair receives enemy phases 7 and 8. |
| No unwinnable tail | **PASS** | Successful runs reach quota before the final wave and still have meaningful defense through turn 8; pure waiting loses on the second ruin at turn 3 rather than stalling. |
| Second-house-ruin loss cause | **PASS** | `/tmp/fun2-wn02-loss_second_ruin-result.json`; `/tmp/fun2-wn02-loss_second_ruin/turn3-sc_c2_failure_quota_impossible-01.png` says exactly why three can no longer return. |
| Quota-miss loss cause | **PASS** | `/tmp/fun2-wn02-loss_quota-result.json`; `/tmp/fun2-wn02-loss_quota/turn9-sc_c2_failure_quota-01.png` says “Dawn comes with fewer than three residents inside” after two returns and eight enemy phases. |
| Haral-death loss cause | **NOT DEMONSTRATED** | Multiple public-input neglect/exposure attempts either won with Haral still at 24/40 or triggered a resident/second-ruin loss first. No Haral-death frame is claimed. This is a finding because the assignment requires a real reachable cause path. |
| Win resolution | **PASS** | Both successful runs play the level-end frame and win at turn-start 9, after exactly eight enemy phases. |
| Text fit | **PASS except guided page** | Eleven opening pages, recruit scenes, wave warnings, house scenes, failure scenes, and outro fit 240×160. Guided tutorial defect below. |

## Findings, ordered by severity

### HIGH — the all-four mastery reward is not demonstrated by either intended public-input route

**Player consequence:** the chapter advertises all-four mastery as the expression ceiling and conditions the smaller turn-5 wave and tally on it, but both reviewed attempts—Moiraine east/Nynaeve south and the swapped assignment—lost the east door and recovered to the ordinary three-house win. The two victories therefore have less outcome expression than the redesign promises.

**Repro:** recruit all three and complete the guided heal on turn 1; save west; send Mat north; try Moiraine east/Nynaeve south, then repeat with those two assignments swapped. Continue with public movement/Visit/Return inputs. In both retained winning traces, east ruins and `sc_c2_defense_tally_mastery` never fires.

**Evidence:** `/tmp/fun2-wn02-golden-result.json`, `/tmp/fun2-wn02-mastery-result.json`, `/tmp/fun2-wn02-golden/turn4-east-ruined.png`.

**Suspected source:** `design/missions/village_defense.yaml:38` (east torch start/clock), `:56` (east door), `:65-68` (waves that compound the route), and `:416-420` (mastery callback). The intended route/clock claim is documented at `docs/design/wn02-epic-redesign.md:112,245,304-308`.

**Smallest implementation-ready fix:** delay only `torch_east` by one player phase: start it as `do_nothing`, then add a turn-2 `change_ai: seek_house_east` event with an east-road warning. Preserve every other clock, the three-resident quota, and the turn-5 one-unit all-saved branch. Verify both authored assignment orders can set all four saved flags and that the mastery tally and one-unit flank actually appear.

### HIGH — Haral is nominally mortal, but the required Haral-death cause path was not reproducible

**Player consequence:** Haral is presented as the human stake, yet repeated no-heal/withdrawal runs left him alive (as low as 24/40) while expendable greens, a resident, the inn threshold, or the house quota failed first. His mortality therefore reads more as objective text than a credible tactical risk, and the cause-specific loss regression remains unproved.

**Repro:** recruit and save the quota, decline the guided heal, withdraw blue attackers toward/inside the inn, and spend remaining actions waiting while preserving the threshold. Haral survives the reviewed full-duration neglect line; more aggressive neglect causes a different loss first.

**Evidence:** `/tmp/fun2-wn02-loss_haral-result.json` (latest attempted public-input route); successful/no-heal run trace recorded Haral at 28→24→24 through turns 1–8. No Haral-death PNG is cited because none was observed.

**Suspected source:** `design/missions/village_defense.yaml:24-29` (Haral and surrounding green geometry), `:42-45` (pursuers), and `:51-52` (final pair). The cause scene itself is correctly authored at `design/scenes/village_defense/scenes.yaml:324-332`; the problem is reaching it before another condition.

**Smallest implementation-ready fix:** give one existing late attacker an explicit Haral/inn-approach job rather than adding a body: place `final_south_b` on the Haral-side lane and route it to the eastern threshold approach while leaving `final_south_a` on the western lane. Preserve two-unit wave size and player-phase warning. Verify a no-heal, no-intercept run produces `sc_c2_failure_luhhan`, while a guided-heal/body-block run still wins.

### MEDIUM — the guided-heal tutorial scrolls away its subject and movement verb

**Player consequence:** the stable wait frame reads only “Haral, choose Items, then choose Herb Pouch.” The beginning—“Nynaeve can use…” and “Move beside…”—has already scrolled away. A first-time player sees the correct item and target after selecting them, but the page they must learn from no longer says who moves or that adjacency is required.

**Repro:** recruit Nynaeve, wait for the tutorial card to settle, and read the final 240×160 frame before pressing anything.

**Frame:** `/tmp/fun2-wn02-alternate/turn1-recruit_nynaeve-01.png`.

**Suspected source:** `design/missions/village_defense.yaml:142`.

**Smallest implementation-ready fix:** replace the 107-character tutorial string with one stable box, for example: `Move Nynaeve beside Haral. Choose Items, then Herb Pouch.` Verify the settled frame retains both `Nynaeve` and `Move beside` and the same real targeting flow still restores Haral.

### MEDIUM — the formal Loss Conditions screen contradicts the three-of-four quota

**Player consequence:** the mission teaches that one house may be lost and only three residents must return, but scrolling the Objective screen shows `All 4 villagers must survive`. That reads as a hidden all-four requirement and undercuts the deliberately forgiving quota.

**Repro:** open Objective at turn 1 and scroll the Loss Conditions panel once.

**Frames:** `/tmp/fun2-wn02-ui/objective-menu.png`, `/tmp/fun2-wn02-ui/objective-menu-scroll.png`.

**Suspected source:** `design/missions/village_defense.yaml:11-14`; four resident `failure_conditions` synthesize the formal loss text even though an unvisited/ruined house never spawns its resident.

**Smallest implementation-ready fix:** move the four resident-death losses from declarative `failure_conditions` to explicit `unit_death` mission events that play the existing cause scene then `lose`; retain Haral as the sole declarative loss condition. The Objective screen will then say only `Haral must survive`, while active resident deaths remain fatal. Verify all four resident-death scenes and the formal Objective text.

## Top three ranked fixes

1. **Make the east mastery clock achievable and prove the all-four branch** by delaying only `torch_east` activation to turn 2; preserve quota-3 recovery and all wave caps.
2. **Create one deterministic Haral-side late approach** using the existing final spear, then prove both Haral-death and protected-Haral outcomes with real input.
3. **Repair the two misleading UI contracts together:** shorten `village_defense.yaml:142` to a stable guided-heal sentence, and migrate resident death handling out of declarative failure conditions so the Objective screen no longer claims all four are mandatory.
