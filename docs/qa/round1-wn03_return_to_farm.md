# Round 1 QA — `wn03_return_to_farm`

**Chapter:** The Ruined Farm
**Coherence:** Partially coherent. The full mission loop is playable and both terminal paths fire, but several required dialogue beats overflow the two-row text treatment; the earliest material break is in the chapter-centerpiece Narg exchange.
**Build tested:** `build/winternight.ltproj`, tree `92946fb39eee3b164c83858bd189b1522d9ba6524029e4ab3cfa70af0ee9b35a`

## Coverage and observed route

All play was against the already-compiled project through posted pygame key events with SDL's dummy video/audio drivers. Frames below are native 240×160 engine surfaces and were visually inspected.

- Golden route completed: tested the west exit before the encounter, took the sheep-pen interrupt, reached the farmhouse, searched water → clean cloth → blankets, recovered and equipped Tam's sword, fought and defeated Narg, returned west, and completed both outro scenes. The optional detour and early-exit check still finished on turn 12.
- Deliberate loss completed: after Narg's first attack, equipped Rand's Hunting Bow so he could not counter at range 1, waited, and let Narg reduce Rand from 11 HP to 0. The runtime set `_lose_game`, entered `game_over`, and displayed GAME OVER on turn 9.
- Optional interactions: the chapter offers no Talks; the sheep pen is its optional Visit and was exercised.

## Findings

### MED — Required dialogue overflows the two-row box, including Narg's centerpiece quote

**Player consequence:** At the settled prompt, the opening of an overlong line has already scrolled out of the box. The player cannot reread the full sentence before advancing, and Narg's key line visibly begins with the lowercase fragment `sometime.` rather than `Narg know some come back sometime.` This makes the centerpiece look clipped even though the words appeared transiently during the text scroll. The same problem weakens the three supply-search lines that are meant to establish Rand's care for Tam.

**Repro:**

1. Start `wn03_return_to_farm` and reach the farmhouse.
2. Search the water, cloth, and blankets; recover Tam's sword.
3. Let each dialogue box finish drawing and stop at its advance prompt.
4. In Narg's second spoken box, observe that the settled box starts `sometime. Narg wait. You no need sword. Put sword down.` The opening clause is no longer visible.
5. The settled water, cloth, and blanket dialogue boxes likewise start mid-thought: `clean the cut...`, `cut, bind it...`, and `the wind...`.

**Frame evidence:**

- `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_trolloc_appears-03.png`
- `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_water-02.png`
- `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_bandages-02.png`
- `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_blankets-01.png`

**Suspected source:**

- `design/scenes/return_to_farm/scenes.yaml:112` — overlong Narg dialogue beat.
- `design/scenes/return_to_farm/scenes.yaml:58`, `:70`, and `:81` — overlong care dialogue beats.

**Smallest source-level remedy:** Split each cited dialogue beat at a sentence boundary so every settled bubble retains a complete thought. Preserve Narg's words verbatim; split after `Narg know some come back sometime.` rather than rewriting his speech.

**Check after remedy:** Replay the real input path at 240×160 and capture every resulting split bubble at its advance prompt. Each frame should begin at a sentence boundary and retain the complete text being presented.

## Checks that passed

- **Fog opening and radius:** Radius 3 is restrictive but playable. The intro names the farmhouse as east, the west edge and blocked terrain constrain the opening route, and the large colored markers become legible as Rand advances. No blind enemy attacks occur before Narg's scripted reveal. Evidence: `/tmp/wn03-fog-opening.png`, `/tmp/wn03-golden-frames-v4/map-fog-opening-free.png`.
- **Sheep-pen dread:** Entering the pen interrupts movement and fires the only optional Visit. The five beats escalate from unnatural silence to the dead sheep, land `They kill for fun.`, then restore direction with `Keep low and reach the farmhouse.` It reads as dread, not filler. Evidence: `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_dead_flock-01.png` through `-05.png`.
- **Search care and progression:** The Search action is explicit on the blue markers; the writing consistently connects water, cloth, and blankets to cooling Tam's fever, binding his wound, and keeping him warm. The care intent survives despite the overflow finding. Evidence: `/tmp/wn03-golden-frames-v4/menu-water-4-(7,_10).png`, `/tmp/wn03-golden-frames-v4/menu-bandages-6-(10,_5).png`, `/tmp/wn03-golden-frames-v4/menu-blankets-7-(12,_7).png`.
- **Narg presentation:** Apart from the overflow above, the broken speech, punctuation, speaker sides, Rand portrait, and Narg portrait render correctly. The short boxes (`Narg no hurt.`, `You put sword down.`) are especially clean. Evidence: `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_trolloc_appears-02.png` through `-12.png`.
- **Combat fairness:** Narg's first enemy-phase strike took Rand from 24 to 11 HP; Rand's sword counter took Narg from 15 to 2 HP. Rand then had a full player phase and a guaranteed displayed 13-damage, 100-hit finishing attack. He is not one-rounded, and the encounter can instead be escaped after the first combat as intended. Evidence: `/tmp/wn03-golden-frames-v4/combat-01.png`, `/tmp/wn03-golden-frames-v4/combat-forecast.png`.
- **Escape gate:** Before the encounter, standing on the west exit offered only `Item` and `Wait`; `Escape` was not exposed. After the combat quote set the encounter flag, returning to the green west edge won the mission and started the outro. Evidence: `/tmp/wn03-golden-frames-v4/menu-early_escape-1-(0,_7).png`, `/tmp/wn03-golden-frames-v4/menu-escape-11-(1,_7).png`.
- **Loss path:** Rand reached 0 HP, `_lose_game` was set, and the real engine entered its GAME OVER screen. Evidence: `/tmp/wn03-loss-frames-v2/game-over.png`.
- **Outro pacing:** Four concise cart-shaft beats resolve the previously mentioned cart, then the background changes to the Westwood for Tam's fever and Rand's care. The two-part chain is long but purposeful, has a clear visual midpoint, and ends with forward motion toward Emond's Field. No portrait mismatch or clipped edge was observed. Evidence: `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_cart_shafts-01.png` through `-04.png`; `/tmp/wn03-golden-frames-v4/event-wn03_return_to_farm_sc_c3_rejoin_tam-01.png` through `-11.png`.
- **Soft-lock review:** Required flags advanced in order, the sword marker activated after all three supplies, Narg spawned and acted, both defeat and evasion remained viable after the encounter, and the west exit completed the chapter.

## Verdict

**FAIL** — mechanics, fog route, optional scene, combat balance, win/loss paths, and outro are coherent, but the player-facing dialogue overflow affects the required search scenes and the chapter's signature Narg exchange.
