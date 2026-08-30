# Winternight story pass

This is the authoritative narrative record for the shipped six-chapter book-text
campaign. It implements the scope, ordering authority, and ending decision in
[`docs/story-plan-v2.md`](story-plan-v2.md). The playable boundary is *The Eye of
the World* Chapters 1–7: it begins with the Quarry Road cart and ends when Moiraine
agrees to go to Tam. It does not show the healing or continue beyond Chapter 7.

Direct dialogue uses short, trimmed lines from `source/private/eotw/`. Narration
compresses prose into original scene text rather than copying paragraphs. Every
scene and mission references stable beat IDs, and every departure from direct
chronology or action is marked `inferred` or `gameplay_invention` in
`source/story_beats.yaml` and `source/adaptation_rules.yaml`.

## Throughline

1. **An Empty Road — attachment before danger.** Rand and Tam's cider cart, Mat's
   pranks, cellar work, friends on the Green, a gleeman, and Bel Tine make Emond's
   Field worth fearing for. The black rider is an intrusion Rand cannot prove.
   Fain's war news and the watching raven widen that private unease, but Tam still
   takes Rand home through a world that feels ordinary.
2. **Winternight — home ruptured.** Chores, stew, and doors that never needed locks
   narrow the story to Rand and his father. Tam takes out a sword from a life he
   will not explain. Trollocs break the door, Tam's old skill gets Rand into the
   woods, and the wound he calls a scratch puts responsibility on the untested son.
3. **The Village Burns — communal cost.** The campaign interleaves the attack on
   Emond's Field while Rand is away. Lan and Moiraine help hold the Green and the
   inn becomes shelter, but not every roof can be saved. Bran's later Chapter 7
   account supplies the direct frame. The playable defense inside that frame stays
   explicitly inferred or invented.
4. **The Ruined Farm — care instead of glory.** Rand returns alone through fog to a
   house that is no longer home. The dead flock, ruined kitchen, waterbag, clean
   cloth, and blankets make every interaction about Tam. Narg's lunge is survived
   by fear and luck, not sudden mastery. Rand treats the wound, builds a litter from
   the cart, and turns east.
5. **The Long Road — endurance and identity broken open.** Pulling Tam is the whole
   labor. Rand must stay beneath the trees while a Trolloc column passes and the
   black rider returns to search the road. Tam's fever moves from unknown wars and
   a cut Tree to Dragonmount, a dead woman, and a crying baby. Rand keeps walking
   after the question changes from whether Tam will live to who Rand is.
6. **Out of the Woods — arrival is not safety.** Gray dawn reveals smoke too heavy
   for hearths and half the village burned. Luhhan, Egwene, and Nynaeve make the
   cost personal before ordinary medicine fails. A Dhurran drags a blanketed
   Trolloc past the litter, the Dragon's Fang marks the surviving inn, and Bran and
   Thom expose one last chance. Rand runs to former festival bonfires now burning
   Trolloc dead, offers any price, and walks back beside an exhausted Moiraine who
   has promised only to do what she can.

The emotional line is warmth → rupture → communal cost → lonely responsibility →
endurance with identity shattered → help carrying an unnamed price.

## Chapter feeling and place state

| Chapter | Feeling | Place state |
| --- | --- | --- |
| `wn00_tutorial` — An Empty Road | Warmth, mischief, then an unconfirmed chill | Quarry Road in winter daylight; whole festival Green; warm Winespring Inn |
| `wn01_farm_escape` — Winternight | Intimate calm broken by panic and dependence | Whole farmhouse at supper; breached house and night farmyard; Westwood refuge |
| `wn02_village_defense` — The Village Burns | Shared courage that cannot prevent shared loss | Green burning on Winternight; Winespring Inn as refuge; homes already threatened |
| `wn03_return_to_farm` — The Ruined Farm | Isolation, dread, and deliberate care | Fogged farm approach; wrecked house and dead flock; quiet Westwood beside Tam |
| `wn04_long_road` — The Long Road | Physical exhaustion, held breath, then identity shock | Root-caught Westwood at night; Quarry Road occupied and watched |
| `wn05_out_of_the_woods` — Out of the Woods | Despair closed door by door, then costly hope | Emond's Field at burned dawn; intact inn amid ruins; Bel Tine fires burning the dead |

The repeated locations are part of the story. The whole farm becomes a breached
yard and then a fogged ruin. The festival Green becomes a defense map and then a
gray-dawn field of ashes and repair. Reuse must reveal changed place state, not
stand in for it.

## Voices

- **Rand** begins ordinary-minded, frightened, and untested. His language reaches
  for home, his father, and the next concrete task. He does not become a warrior
  overnight. His courage is carrying, searching, binding a wound, holding still,
  and asking for help after every familiar answer fails.
- **Tam** is spare, competent, and protective while lucid. The sword and his past
  remain unexplained. Fever loosens memories but never supplies confirmation or
  denial from the healthy man.
- **Mat** jokes before admitting fear. **Perrin** observes and answers slowly.
  **Egwene** is already organizing the day in Chapter 0, then runs bandages through
  smoke in Chapter 5 and allows herself one fierce, helpless hug.
- **Nynaeve** is blunt because people depend on the accuracy of her judgment. Her
  refusal is devastating precisely because her hands are gentle and she knows both
  what her medicines can do and when they cannot.
- **Haral Luhhan** is exhausted, burned, and still the person who takes the other
  end of a load. **Bran** sounds harried because he is counting a damaged village,
  then becomes the Mayor who identifies the last chance.
- **Thom** performs wonder in daylight and measures danger when the stories become
  real. At the inn he makes Bran arrive at the Aes Sedai answer instead of claiming
  authority as a stranger.
- **Moiraine** spends words carefully, with composure that survives visible
  exhaustion. She refuses false promises but rises to help. **Lan** spends even
  fewer words, protects her without softness, and names the price Rand is too
  desperate to weigh.
- **Fain** turns news into spectacle and leaves unease behind. His disappearance is
  reported without extending the campaign into a new claim about his fate.

## Adaptation marks

| Scope | Marked adaptation | Narrative guardrail |
| --- | --- | --- |
| Chapter 0 | `road_as_scene`, `tutorial_errands`, `cider_cellar`, `raven_tutorial` | Portrait travel and tutorial interactions carry direct material without inventing a bandit fight. |
| Chapter 1 | `farmhouse_opening_split`, `scripted_tam_wound` | Calm, sword, breach, and escape are separated for play, but Tam's wound never depends on player failure. |
| Chapter 2 | `village_parallel_battle`, `village_defense_rules`, `named_circle_absent`, `green_defenders`, `bran_account_framing` | The battle is inferred and its objectives are invented. Bran's account is direct. No named friend's death is invented. |
| Chapter 3 | `ruined_farm_fog`, `dead_flock_interrupt`, `supply_regions`, `sword_search_reorder`, `wounded_trolloc_fairness`, `narg_lunge_exchange`, `cart_litter_outro_split` | Search order and tactical staging change, not the care items, Narg's lunge, Rand's inexperience, or the litter outcome. |
| Chapter 4 | `litter_as_rescue_traveler`, `long_road_hide` | Rescue weight and watched-road failure turn prose endurance into play. Detection remains failure, never an invented victory. |
| Chapter 5 | `walk_leg_split`, `c5_green_talk_staging`, `ending_question_card` | Litter and running legs, optional Green Talks, and the final hold are staging. Direct encounters, refusal, plea, and promise retain their book order and meaning. |
| Campaign | `two_layout_reuse`, `boundary_extension` | State variants show damage across time. The last story-bearing scene remains `sc_c5_moiraine_heals`. |

The Chapter 2 framing does not convert its unseen tactical details into direct
canon. The Chapter 5 Egwene Talk compresses her bandage run and later hug, so its
playable timing may shift without claiming a different event. The ending card is
not an epilogue: it repeats Rand's Chapter 6 question, “Light, who am I?”, after the
Chapter 7 promise and adds no story beyond the locked boundary.

## Playable handoffs

- Chapter 0 teaches movement, `Talk`, repeated destination interaction, and attack
  selection through story actions. Required `Item` and `Equip` words remain
  narration, not dialogue.
- Chapter 1 hands flight to the player only after the breach makes the objective
  clear. Chapter 3 makes water, cloth, blankets, and the sword readable as care
  before Narg can block the escape.
- Chapter 4 pairs litter-borne Tam with Rand and makes the road itself the danger.
  Chapter 5 removes Tam only after the litter reaches the inn, then opens the
  bonfire destination for Rand alone.
- `sc_c5_moiraine_heals` closes on Moiraine, Lan, and Rand walking toward the inn.
  `sc_c5_ending_card` may hold the prior question, but it may not carry dialogue,
  action, or consequence beyond that close.
