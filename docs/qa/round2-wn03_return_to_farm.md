# Round 2 QA — `wn03_return_to_farm` / The Ruined Farm

## Verdict

**PARTIALLY COHERENT — FAIL.** The round-1 dialogue-overflow finding is fixed: every settled Narg quotation inspected begins at its authored first word, and all three Tam-care searches retain their complete opening words and thoughts. The real-input golden route, including the sheep-pen Visit, Narg fight, west return, cart-shaft scene, and Tam reunion, completed on turn 12. The deliberate Narg loss reached Game Over on turn 9.

The objective repair is incomplete in this chapter. All three requested map banners render unclipped, and the initial Objective screen correctly shows **“Reach the house / Through the fog.”** After progression, however, the formal Objective screen never changes: during **“Survive Narg. Gather the rest”** and **“Return west to Tam,”** it still says **“Reach the house / Through the fog.”** This gives a first-time player who opens the persistent reference screen an obsolete destination.

Tested against compiled tree `a666a9e750c52f07f28e4fdd0e2cd16e5f139f600f3f220962600bb5eea9753d` with engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`. Both runs launched the already-compiled `build/winternight.ltproj` through the pinned engine with dummy SDL video/audio and posted real pygame key events. The golden/objective run completed across 4,434 frames with 206 select inputs plus real directional/start/cancel inputs; the loss run completed across 3,207 frames with 122 select inputs plus real directional/start/cancel inputs. Every cited PNG is a native 240×160 engine capture and was visually inspected.

## Intended loop and observed route

1. The intro names the farmhouse to the east. The initial map banner and Objective screen both show **“Reach the house / Through the fog.”**
2. Before the encounter, Rand returned to the west edge. Its action menu exposed only `Item` and `Wait`, not `Escape`.
3. Rand crossed the sheep pen and chose `Visit`. The complete eight-box dread scene fired once, ending with **“Nothing has changed. Keep low and reach the farmhouse.”**
4. Rand entered the highlighted farmhouse approach, then followed the blue markers and chose `Search` for water, clean cloth, and blankets.
5. After all three supply flags were set, the sword marker became available. Rand searched it, recovered and equipped Tam’s sword, and saw the full Narg scene.
6. The map banner changed to **“Survive Narg. Gather the rest.”** Narg attacked on enemy phase; Rand survived at 11/24 HP and countered. The combat quote set the encounter flag and changed the map banner to **“Return west to Tam.”**
7. Rand used the next player phase to defeat Narg, returned to the green west edge, and triggered victory. The eight cart-shaft boxes and seventeen Tam-reunion boxes played, followed by the chapter-save transition on turn 12.
8. In the independent loss run, Rand equipped the Hunting Bow after Narg’s first attack so he could not counter at range 1, chose `Wait`, reached 0 HP on turn 9, set `_lose_game`, and entered the visible Game Over state.

## Coherence trace

| State | Player-facing goal | Visible cue and public action | Observed feedback / next goal |
| --- | --- | --- | --- |
| Start | Reach the house through the fog | Two-line banner, matching Objective screen, eastward visibility, highlighted farmhouse approach | Entering the approach plays the ruined-house scene and reveals blue search markers |
| Sheep pen (optional) | Investigate the silent pen | `Visit` appears on the pen | Eight settled boxes deliver the dead-flock beat, then explicitly restore the farmhouse direction |
| Farmhouse search | Find water, clean cloth, and blankets | Three blue markers each expose `Search` | Each search plays a Tam-care scene; after all three, the yellow sword marker becomes actionable |
| Sword / Narg reveal | Survive Narg and keep the supplies | Sword is equipped automatically; Narg appears visibly; map banner updates | Narg initiates combat but cannot one-round Rand; the encounter quote sets the west-return gate |
| Post-encounter | Return west to Tam | Map banner says `Return west to Tam`; west edge remains highlighted green | Entering the west region wins and starts both outro scenes |
| Persistent help after progression | Recheck the current goal | Map options → `Objective` | **Break:** Win Conditions remain `Reach the house / Through the fog` at the supply, Narg, return, and post-Narg stages |
| Loss | Keep Rand alive | Narg remains adjacent and attacks after Rand waits | Rand reaches 0 HP, `_lose_game` is true, and `GAME OVER` appears |

## Round-1 finding re-verification

### RESOLVED — Round 1 MED: required dialogue scrolled away its opening words

**Round-1 item:** `docs/qa/round1-wn03_return_to_farm.md:17-43`.

#### Narg centerpiece

All twelve settled quotation boxes in `sc_c3_trolloc_appears` were inspected. Their visible first words are, in order: **Others, Narg, Narg, Narg, You, Stay, Why, Put, Others, You, All, I’ll**. These match the authored box starts at `design/scenes/return_to_farm/scenes.yaml:130-141`. No box starts mid-scroll or loses an opening clause.

The formerly broken centerpiece now appears as two complete settled boxes:

- **“Narg know some come back sometime.”** — `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_trolloc_appears-04.png`
- **“Narg wait. You no need sword. Put sword down.”** — `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_trolloc_appears-05.png`

Full Narg after-evidence: `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_trolloc_appears-03.png` through `-14.png`.

#### Tam-care searches

The formerly overflowing care thoughts now settle at their authored openings and remain complete:

| Search | Settled visible starts | Evidence | Current source |
| --- | --- | --- | --- |
| Water | `Enough to cool his forehead,` / `and give him a drink.` | `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_water-03.png`, `-04.png` | `design/scenes/return_to_farm/scenes.yaml:70-71` |
| Clean cloth | `Easy around his ribs.` / `Wash the cut, bind it, then` | `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_bandages-03.png`, `-04.png` | `design/scenes/return_to_farm/scenes.yaml:84-85` |
| Blankets | `His coat was not enough` / `These might keep the fever` | `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_blankets-01.png`, `-02.png` | `design/scenes/return_to_farm/scenes.yaml:96-97` |

No cited care frame begins with the round-1 mid-thought fragments `clean the cut...`, `cut, bind it...`, or `the wind...`.

## Objective-string verification

The map overlays were allowed to settle before capture. All requested banner strings are complete and readable:

| Stage | Map banner result | Formal Objective-screen result |
| --- | --- | --- |
| Start | **PASS:** `Reach the house` / `Through the fog` — `/tmp/wn03-round2-objectives-v2/banner-initial.png` | **PASS:** matching Win Conditions, unclipped — `/tmp/wn03-round2-objectives-v2/objective-initial.png` |
| Narg reveal | **PASS:** `Survive Narg. Gather the rest` — `/tmp/wn03-round2-objectives-v2/banner-survive.png` | **FAIL:** still `Reach the house` / `Through the fog` — `/tmp/wn03-round2-objectives-v2/objective-survive.png` |
| Encounter complete | **PASS:** `Return west to Tam` — `/tmp/wn03-round2-objectives-v2/banner-return.png` | **FAIL:** still `Reach the house` / `Through the fog` — `/tmp/wn03-round2-objectives-v2/objective-return.png` |

The same stale-screen behavior is already present during the supply search (`/tmp/wn03-round2-objectives-v2/objective-supplies.png`) and persists after Narg is defeated (`/tmp/wn03-round2-objectives-v2/objective-take.png`). Runtime state evidence in `/tmp/wn03-round2-golden-details.json` confirms why: `simple` advances while `win` remains `Reach the house,Through the fog`.

## Findings

### MAJOR — The persistent Objective screen never advances past the opening goal

**Player consequence:** A first-time player who opens the Objective screen for durable guidance after reaching the house is told to reach the house again. During and after the Narg encounter this directly contradicts the current map banner and omits the required westward return to Tam. The route remains completable because the map banner and green west marker are correct, so this is not a soft lock, but the game’s formal help screen is materially misleading.

**Repro:**

1. Start `wn03_return_to_farm`, open map options, and choose `Objective`; observe `Reach the house / Through the fog`.
2. Reach the farmhouse, complete all three searches, recover the sword, and let the **“Survive Narg. Gather the rest”** banner settle.
3. Before ending the player phase, open `Objective` again; it still says `Reach the house / Through the fog`.
4. Let Narg attack and the encounter quote play. After the **“Return west to Tam”** banner settles, open `Objective` again; it still shows the opening goal.

**Frame evidence:**

- Correct Narg banner: `/tmp/wn03-round2-objectives-v2/banner-survive.png`
- Stale Narg Objective screen: `/tmp/wn03-round2-objectives-v2/objective-survive.png`
- Correct return banner: `/tmp/wn03-round2-objectives-v2/banner-return.png`
- Stale return Objective screen: `/tmp/wn03-round2-objectives-v2/objective-return.png`

**Exact suspected source:** `design/missions/return_to_farm.yaml:52`, `:85`, `:93`, `:100`, and `:105` author progression changes with `target: simple`, so only the map overlay changes. The two requested post-sword goals are specifically at `:85`, `:93`, and `:100`. The initial objective at `design/missions/return_to_farm.yaml:9` correctly populates both compiled slots and is not at fault.

**Smallest source-level remedy:** Change every required progression objective in this mission to the repository’s `target: both` mechanism, using comma-separated line breaks that keep every persistent Win Conditions line within its 16-character budget. Recompile outside QA, then replay the real input route and capture both the settled map banner and formal Objective screen at all five states.

## Required-path and regression checks

- **Golden victory: PASS.** All required supply flags, `sword_found`, `narg_encountered`, and `trolloc_defeated` became true; Narg reached 0 HP; Rand entered the west win region; both outro scenes played; chapter save followed. Evidence: `/tmp/wn03-round2-golden-result.json`, `/tmp/wn03-round2-golden-details.json`.
- **Sheep-pen beat: PASS.** The optional `Visit` fired once and all eight settled frames retained their starts and direction. Evidence: `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_dead_flock-01.png` through `-08.png`.
- **Early escape gate: PASS.** At the west edge before Narg, the action menu contained only `Item` and `Wait`. Evidence: `/tmp/wn03-round2-golden/menu-early_escape-1-(0,_7).png`.
- **Narg survival/fight: PASS.** Narg’s first attack left Rand at 11/24 HP; Rand remained controllable, defeated Narg on the next player phase, and could then return west. Evidence: `/tmp/wn03-round2-golden/combat-01.png`, `/tmp/wn03-round2-golden-details.json`.
- **Outro and terminal transition: PASS.** The cart-shaft and Tam-reunion scenes fired in order and the run reached `title_save` on turn 12. Evidence: `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_cart_shafts-01.png` through `-08.png`; `/tmp/wn03-round2-golden/event-wn03_return_to_farm_sc_c3_rejoin_tam-01.png` through `-17.png`.
- **Loss path: PASS.** The independent run recorded Rand at 0 HP with Hunting Bow equipped, `_lose_game: true`, and Narg still alive, then displayed Game Over on turn 9. Evidence: `/tmp/wn03-round2-loss-result.json`, `/tmp/wn03-round2-loss-details.json`, `/tmp/wn03-round2-loss/game-over.png`.
- **Soft-lock review: PASS on both terminal branches.** The complete required route reached chapter save, and deliberate Rand death reached Game Over. No required interaction became unavailable after its prerequisite.

## Final chapter verdict

**FAIL for round 2.** The round-1 dialogue overflow is resolved and both terminal paths remain healthy, but two critical requested objective states are absent from the formal Objective screen. The chapter is playable, yet its persistent guidance contradicts the current mission state after the farmhouse is reached.
