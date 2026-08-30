# Fun review round 3 — `wn05_out_of_the_woods`

## Verdict

**MOSTLY FUN — target met.** Both round-2 findings are closed. The held ending card now asks the approved **“Light, who am I?”** with no call to action, handle, URL, or promotional copy. The mandatory tail after the last playable map input is exactly **35 settled pages**, down from 55 and on the requested approximately-35-page target. The complete both-Talks route still plays the callback before Rand's plea, continues through the full ending, and returns to the title. A separate dawdle run still presents all three fever barks without causing a loss or soft-lock.

The chapter appropriately remains MOSTLY FUN rather than FUN: it is a zero-pressure denouement with unchanged tactical decision density, and 35 pages is still a substantial noninteractive release after the final map action. Those are limits of the intended chapter shape, not failed round-3 targets.

## Runtime evidence and provenance

- Gated tree supplied for this review: `a6b14053ed28e56217cb10704868a1f918655f646381a8ed32875364cf3bbebe`.
- Independently compiled project: `/tmp/fun3-wn05-copy/winternight.ltproj`, compiled through the same `compile_campaign_project` Python API pattern as `tests/conftest.py::_compile_campaign_to` / `compiled_campaign`.
- Independent `/tmp` project tree hash: **`a6b14053ed28e56217cb10704868a1f918655f646381a8ed32875364cf3bbebe`**. It exactly matches the gated hash. Compile provenance: `/tmp/fun3-wn05-copy/provenance.json`.
- Pinned engine: `vendor/lt-maker`, commit `1820e585450f6f47605aebd686b2a3f13af181f0`, engine `2026.02.17a` (`engine.lock:2-3`).
- Method: the pinned engine loaded only the isolated `/tmp` project under dummy SDL video/audio. The driver posted real pygame key-down/key-up events for movement, menus, both Talks, Wait/End, every scene advance, the inn delivery, bonfire arrival, the held ending card, and title return. No event, flag, objective, unit, HP value, or project data was mutated.
- Golden run: `/tmp/fun3-wn05-golden/result.json`; 4,769 engine frames; 203 real inputs (153 Select, 14 Down, 5 Left, 19 Right, 8 Up, 4 Back); completion `returned_to_title` on turn 5; 121 settled native 240×160 frames under `/tmp/fun3-wn05-golden/frames/`.
- Dawdle run: `/tmp/fun3-wn05-loss/result.json`; 1,291 engine frames; 50 real inputs; completion `no_public_loss_through_turn_10`; fever captures under `/tmp/fun3-wn05-loss/frames/`; final controllable state `/tmp/fun3-wn05-loss/turn10-no-loss.png`.

## Finding-by-finding closure

### CLOSED — prior MAJOR: promotional CTA replaced the dramatic ending

**PASS.** After the final **“Rand matches their stride. Help is coming.”** narration, the ending card settled and was deliberately held before another real Select input. It displayed only **“Light, who am I?”** The text is complete and unclipped, and no CTA, `@` handle, URL, feedback request, or foreign copy is present.

- Held native frame: `/tmp/fun3-wn05-golden/ending-card-held.png`.
- Settled-page frame: `/tmp/fun3-wn05-golden/frames/121_wn05_out_of_the_woods_sc_c5_ending_card.png`.
- Source now rendered: `design/scenes/out_of_the_woods/scenes.yaml:235-244`, specifically the approved text at `:244`.
- Governing adaptation decision: `source/adaptation_rules.yaml:33`.
- Terminal regression: the next real Select completed the close/save transition and reached `/tmp/fun3-wn05-golden/return-to-title.png`.

The prior causal line is no longer faulty; this finding is fully closed.

### CLOSED — prior MEDIUM: 55-page post-input tail

**PASS — target met exactly.** The final playable map input resolved Rand's move onto the bonfire region. From the first settled bonfire page through the held card, the run recorded exactly **35** settled pages:

| Ending segment | Settled pages | Frame indices |
| --- | ---: | --- |
| `sc_c5_bonfires` | 7 | 087-093 |
| `sc_c5_both_talks_callback` | 1 | 094 |
| `sc_c5_any_price` | 9 | 095-103 |
| `sc_c5_moiraine_heals` | 17 | 104-120 |
| `sc_c5_ending_card` | 1 | 121 |
| **Total after final playable input** | **35** | **087-121** |

This is 20 pages fewer than the round-2 count of 55. The runtime count comes from `/tmp/fun3-wn05-golden/result.json`, not from static beat inference. The corresponding source spans are `design/scenes/out_of_the_woods/scenes.yaml:155-244`; the page-bearing beats are at `:167-173`, `:184`, `:196-204`, `:217-233`, and `:244`. Event order remains wired at `design/missions/out_of_the_woods.yaml:100-121`.

The 35-page target is achieved without removing the locked callback, any-price offer, refusal of a false promise, Moiraine rising to help, walk back toward the inn, or closing question. This finding is closed.

## Whole-chapter foreign-text and fit scan

**PASS.** I visually inspected every one of the **121 settled 240×160 frames**, in order, using contact sheets `/tmp/fun3-wn05-golden/sheets/sheet-01-001-006.png` through `/tmp/fun3-wn05-golden/sheets/sheet-21-121-121.png`. The held ending frame was also inspected separately at native resolution.

No settled frame contains promotional copy, a social handle, a URL, a feedback request, a CTA, or other text foreign to the chapter. A corroborating scan of all 121 recorded settled-page text values found no `http://`, `https://`, `www.`, handle-shaped `@name`, or promotional terms. The ending card is rendered by its card action rather than the recorded text-box metadata, so the visual inspection—not the metadata scan—is the decisive evidence for that page.

No inspected page showed clipped glyphs, lost opening text, third-line overflow, or text escaping its 240×160 dialogue/narration box.

## Regression checks

| Contract | Result and evidence |
| --- | --- |
| Both optional Talks remain usable | **PASS.** Rand selected public `Talk` with Luhhan on turn 1 and Egwene on turn 3. Native menu frames: `/tmp/fun3-wn05-golden/luhhan-talk-menu.png`, `/tmp/fun3-wn05-golden/egwene-talk-menu.png`. Both scenes appear in the settled-frame run and both flags were set before bonfire arrival. Source: `design/missions/out_of_the_woods.yaml:42-60`. |
| Both-Talks callback precedes the plea | **PASS.** Runtime event entry order was bonfires at frame 3,637, callback at 3,833, and any-price at 3,861. The callback is settled frame 094: `/tmp/fun3-wn05-golden/frames/094_wn05_out_of_the_woods_sc_c5_both_talks_callback.png`; the plea begins at frame 095. Source ordering: `design/missions/out_of_the_woods.yaml:100-107`. |
| Full ending reaches title | **PASS.** All 35 ending pages settled in order, the card held for input, and the next real Select reached `/tmp/fun3-wn05-golden/return-to-title.png`. Completion is `returned_to_title` with no deadline or planner failure. |
| Dawdle barks fire | **PASS.** Turn 4: `/tmp/fun3-wn05-loss/frames/001_wn05_out_of_the_woods_fever_turn_4.png`; turn 6: `/tmp/fun3-wn05-loss/frames/002_wn05_out_of_the_woods_fever_turn_6.png`; turn 8: `/tmp/fun3-wn05-loss/frames/003_wn05_out_of_the_woods_fever_turn_8.png`. All three fit at native resolution. Source: `design/missions/out_of_the_woods.yaml:67-83`. |
| Dawdling does not create a loss or soft-lock | **PASS.** After repeated public End inputs, turn 10 remained in `free` control. Rand was alive at 24/24 on `[1,8]`; Tam was alive at 20/20 on `[2,8]`; both Talks remained available; `tam_at_inn` remained false. Evidence: `/tmp/fun3-wn05-loss/turn10-no-loss.png` and `/tmp/fun3-wn05-loss/result.json`. The only authored loss hooks are unit-death conditions at `design/missions/out_of_the_woods.yaml:15-17`, and this zero-enemy chapter exposes no public action that can force either death. No forbidden state mutation was used to manufacture a loss. |

## Findings, ordered by severity

No blocking, major, medium, or minor player-facing finding remains in this focused round. Both prior findings are closed, and no promotional-text, callback-order, ending-transition, bark-timing, clipping, or soft-lock regression was observed.

## Final chapter verdict

**MOSTLY FUN — target met.** The approved question now owns the final held frame, the CTA is gone, the post-input tail is exactly 35 settled pages, both optional Talks still earn their callback, the full ending returns to title, and dawdling remains acknowledged but nonlethal.
