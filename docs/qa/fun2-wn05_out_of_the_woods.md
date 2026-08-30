# Fun review round 2 — `wn05_out_of_the_woods`

**Verdict: MOSTLY FUN — target met.** The implemented changes all work in the current compiled project: Luhhan's Talk gives Tam a real same-turn second litter move, the turn-4/6/8 fever barks make a stalled route acknowledge Tam's condition without creating a loss, and the both-Talks callback plays before Rand's any-price plea. The chapter remains an effective zero-pressure denouement rather than a tactical chapter. It does not reach FUN because its strict decision density is unchanged from baseline and the player's final map action is followed by a 55-page, noninteractive ending tail whose last card breaks the emotional release with an unfinished promotional message.

## Runtime evidence

- Gated compiled provenance: `build/winternight.ltproj`, report tree `a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a`
- Isolated tested copy: `/tmp/fun2-wn05-copy/winternight.ltproj`, compiled through `_compile_campaign_to`; tree hash **`a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a`** and content hash `66ae29c77499452da30f6abba3156f5ac0276e12c741047f9b7e98a8d3d51207`. The isolated tree is deterministic and content-identical to the gated tree.
- Pinned engine: `vendor/lt-maker`, commit `1820e585450f6f47605aebd686b2a3f13af181f0`, engine `2026.02.17a` (`engine.lock:2-3`)
- Method: the pinned engine loaded only the isolated `/tmp` project under dummy SDL video/audio. Both routes used posted pygame key-down/key-up input for movement, menus, Talks, Wait/End, scene advance, delivery, objective inspection, bonfire arrival, ending card, and title return. No event, flag, objective, unit, HP value, or project data was mutated.
- Golden run: `/tmp/fun2-wn05-golden/result.json`; native frames under `/tmp/fun2-wn05-golden/frames/`. Completion returned to the title on **turn 5** after 5,329 engine frames and 231 real inputs (173 Select, 14 Down, 5 Left, 19 Right, 8 Up, 4 Back). All **141** settled captures are 240x160.
- Dawdle run: `/tmp/fun2-wn05-loss/result.json`; fever frames under `/tmp/fun2-wn05-loss/frames/`; final recovery state `/tmp/fun2-wn05-loss/turn10-no-loss.png`. The run used public End through **turn 10** and remained controllable with no loss, damage, displacement, or consumed Talk.

## Dual-run fun protocol

### Golden / intended route

Route: burned-dawn handoff -> Rand Talks to Luhhan -> Tam crosses the Wisdom rows and hears Nynaeve's refusal -> Luhhan's one-shot assist refreshes Tam -> Rand Talks to Egwene -> Tam delivers at the inn -> objective flips -> Rand follows the fire landmark to the bonfires -> both-Talks callback -> any-price plea -> Moiraine's promise -> ending card -> title.

The mechanical core is **walk / deliver / ask for help**. Turns 1-3 retain a real scheduling choice between Rand, Tam, the optional Talks, and the inn delivery. Turns 4-5 are still a forced two-turn walk to the only relevant destination.

### Luhhan assist verification

The refresh is real and changes the litter route; it is not merely a flag:

1. Tam moves from `[2,8]` to `[5,8]` on turn 1 and finishes when the Wisdom-row interrupt starts (frame 868).
2. After Luhhan has been Talked to, `luhhan_help_used` becomes true and Tam is again **unfinished** at the same `[5,8]` on turn 1 (frame 1,400). The native movement overlay visibly returns: `/tmp/fun2-wn05-golden/luhhan-assist-refresh.png`.
3. With real input, Tam immediately moves a second time through `[6,8]` and `[7,8]` to `[8,8]` before turn 2 (frames 1,423-1,439). The full trace is `tam_status_trace` in `/tmp/fun2-wn05-golden/result.json`.

This saves one litter movement turn on the first leg: without the refresh Tam cannot cover those second three tiles until turn 2. It does **not** shorten this particular all-Talk run's raw chapter completion below turn 5 because the route deliberately holds delivery until Egwene's Talk; it instead front-loads Tam to the inn door and changes the two-unit ordering on turns 1-3. The causal source is `design/missions/out_of_the_woods.yaml:46-66`.

### Dawdle / weak route

Public End was selected repeatedly without moving either unit. The authored fever events fired exactly at turn start:

- Turn 4: “Tam shivers beneath the blankets. The inn is close.” — `/tmp/fun2-wn05-loss/frames/001_wn05_out_of_the_woods_fever_turn_4.png`
- Turn 6: “Tam's breathing turns ragged. Rand cannot stop now.” — `/tmp/fun2-wn05-loss/frames/002_wn05_out_of_the_woods_fever_turn_6.png`
- Turn 8: “Tam burns with fever. Rand must reach the inn.” — `/tmp/fun2-wn05-loss/frames/003_wn05_out_of_the_woods_fever_turn_8.png`

All three boxes fit at native 240x160. Turn 8 also repeats the inn objective and highlight. At turn 10, Rand remained 24/24 at `[1,8]`, Tam remained 20/20 at `[2,8]`, `tam_at_inn` remained false, both Talks remained available, and the game remained in free player control. This verifies the required escalation and the locked **never lose by dawdling** contract at `design/missions/out_of_the_woods.yaml:67-83`.

## Dead-turn ledger versus baseline

A dead turn uses the repository's strict choice-density definition: no risk, reward, ordering, route, or resource tradeoff. A condition bark can stop a stall from being silent without inventing a tactical decision.

| Route | Current natural / raw turns | Current dead turns | Baseline | Judgment |
| --- | ---: | ---: | ---: | --- |
| Golden, both Talks | 5 / 5 | **2/5 (40%)** | **2/5 (40%)** | Unchanged. Turns 1-3 schedule two units, two optional Talks, assist timing, and delivery. Turns 4-5 have only the bonfire route. |
| Dawdle | 10 / 10 observed | **10/10 (100%) strict**; **7/10 silent** | **10/10 (100%)**, all silent | Turns 4/6/8 now react to the stall, but still create no risk or alternate decision. The change improves feedback, not tactical density. |

The baseline reference is `docs/qa/fun-review.md:293-339`. The improvement succeeds on its intended axis: weak play is acknowledged without violating a nonlethal denouement. It should not be credited with choices it does not add.

## Tension curve and peak

**Burned village -> Luhhan shares the load -> Nynaeve closes ordinary help -> Bran and Thom name one last chance -> fire-line destination -> both village contacts echo in Rand's resolve -> “Any price” -> Moiraine rises despite exhaustion -> hope.** This is an emotional fall-and-rise rather than a danger curve, appropriate after `wn04`'s detection peak.

**Tension-peak frame:** `/tmp/fun2-wn05-golden/frames/108_wn05_out_of_the_woods_sc_c5_any_price.png`. Moiraine's “Any price.” lands immediately after Rand's plea and after the optional callback. The current event order is unambiguous: `sc_c5_bonfires` frame 3,637 -> `sc_c5_both_talks_callback` frame 3,945 -> `sc_c5_any_price` frame 3,973 (`/tmp/fun2-wn05-golden/result.json`). The wiring is `design/missions/out_of_the_woods.yaml:100-116`.

## Regression checks

| Contract | Result and evidence |
| --- | --- |
| First-leg objective is stated and actionable | **PASS.** Objective reads “Get Tam to inn”; the transient banner says “Bring Tam down the Green / Reach the marked inn door.” `/tmp/fun2-wn05-golden/initial-objective.png`; `design/missions/out_of_the_woods.yaml:14,34-45`. |
| Both optional Talks remain public and one-shot | **PASS.** Luhhan and Egwene both exposed `Talk`; captures: `/tmp/fun2-wn05-golden/luhhan-talk-menu.png` and `/tmp/fun2-wn05-golden/egwene-talk-menu.png`. Both flags were true and both Talk options absent before leg two. |
| Wisdom-row interruption | **PASS.** Tam's real movement into `[5,8]` fired `sc_c5_nynaeve` on turn 1 and returned control without blocking the route. |
| Luhhan assist | **PASS.** Tam changed from finished to unfinished at `[5,8]` and took a second three-tile move on turn 1; see the assist verification above. |
| Inn delivery and leg-two objective flip | **PASS.** Delivery fired the Dragon's Fang and Bran/Thom scenes, removed Tam, activated the bonfires, and changed both win/simple text to “Find Moiraine / At the bonfires”; loss became “Keep Rand alive.” `/tmp/fun2-wn05-golden/leg2-objective.png`; `design/missions/out_of_the_woods.yaml:88-99`. |
| Bonfire landmark and route readability | **PASS.** Three persistent animated fires sit immediately above the two passable arrival tiles, with Moiraine and Lan beside them. The landmark remains clear under the movement overlay. `/tmp/fun2-wn05-golden/leg2-map.png`, `/tmp/fun2-wn05-golden/bonfire-landmark-move.png`; `design/maps/emonds_field.yaml:71`. |
| Both-Talks callback before any-price | **PASS.** Callback frame `/tmp/fun2-wn05-golden/frames/098_wn05_out_of_the_woods_sc_c5_both_talks_callback.png` is followed by first any-price frame `099`; event frames are 3,945 then 3,973. The callback fits without clipping. |
| Win, outro, and title return | **PASS.** Bonfire arrival won on turn 5, `sc_c5_moiraine_heals` and the ending card completed, and one real Select returned to `/tmp/fun2-wn05-golden/return-to-title.png`. No soft-lock occurred. |
| Dawdle remains nonlethal | **PASS.** Fever events fired on 4/6/8; turn 10 remained free control with full HP. There is intentionally no public damaging action in this zero-enemy level. The formal unit-death loss hooks at `design/missions/out_of_the_woods.yaml:15-17` therefore cannot be exercised without forbidden mutation; no fake loss was manufactured. |
| Text fit at native resolution | **PASS for the changed and regression-risk surfaces.** The three fever barks, assist state, both-Talks callback, objective screens, bonfire landmark, any-price peak, final narration, and ending card were vision-inspected at 240x160. No glyph clipping, third-line overflow, lost opening clause, or automatic-scroll loss appeared. The ending card's problem is its authored content, not rendering. |
| Ending pacing and input hold | **FUNCTIONAL PASS, FUN FINDING.** The card remains in input wait, does not double-advance, and returns to title. However, the final bonfire input begins a 55-page sequence: bonfires 11 + callback 1 + any-price 15 + Moiraine 27 + card 1. See finding 2. |

## Findings, ordered by severity

### MAJOR — the final card replaces the dramatic ending with an unfinished promotional CTA

**Player consequence:** After Moiraine promises to hurry and the narration says help is coming, the campaign cuts to **“Want more? Ping me on X(@X_) with feedback.”** The placeholder-like `@X_` looks unfinished and the fourth-wall promotion discards the campaign's identity question at the exact release beat. This is not a clipping issue; the wrong text is fully legible.

**Repro:** Complete the golden route, advance the final “Help is coming” narration, and let the ending card settle.

**Evidence:** `/tmp/fun2-wn05-golden/ending-card-held.png` and `/tmp/fun2-wn05-golden/frames/141_wn05_out_of_the_woods_sc_c5_ending_card.png`.

**Causal source:** `design/scenes/out_of_the_woods/scenes.yaml:255-264`, specifically line 264. It also conflicts with the approved `ending_question_card` decision at `source/adaptation_rules.yaml:33`, which says the ending should hold on Rand's unanswered **“Light, who am I?”**

**Smallest remedy:** Replace only the ending-card text at line 264 with the approved question; retain the same asset, input wait, close transition, and title-return wiring. Verify the replacement in a native held frame and a real-input title return.

### MEDIUM — 55 mandatory pages after the final playable action blunt the release

**Player consequence:** Reaching the bonfires is the last gameplay decision, but title return requires 55 settled text/card advances. The callback is correctly placed and earns its single page; the accumulation around it makes the final promise feel delayed rather than immediate. This, together with two route-only turns, is why the chapter remains MOSTLY FUN rather than FUN.

**Repro:** Enter `[13,14]` on turn 5 and count settled boxes until title input: 11 bonfire + 1 callback + 15 any-price + 27 Moiraine + 1 ending card. `/tmp/fun2-wn05-golden/result.json` records all 141 chapter boxes and the per-scene order.

**Causal source:** `design/scenes/out_of_the_woods/scenes.yaml:155-264`, especially repeated adjacent pleas at `:200-214` and the 27-page promise/walk-back scene at `:227-253`.

**Smallest remedy:** On a later narrative-fit pass, trim repeated adjacent statements while retaining four locked beats: Rand offers any price, Moiraine refuses a false promise, she rises to help, and the party starts back toward the inn. Keep every resulting page inside the current 240x160 text budget. No tactical or event wiring change is needed.

No blocking soft-lock, objective, landmark, callback-order, fever-timing, loss, or text-overflow finding was observed.
