# Human playtest protocol

Automated verification proves that every required route can complete, but it cannot establish
human pacing, perceived difficulty, tutorial clarity, or the subjective music mix. Phase 5 closes
only after three complete human runs made after the final balance change.

## Run procedure

1. Start from the title screen with `make play` and choose **New Game**.
2. Start the timer when Chapter 0 begins. Record each chapter-transition time and stop at the
   **End of Winternight** card.
3. Play naturally. Do not use LT-Maker, debug commands, or the automated route.
4. Record restarts, losses, unclear objectives, and any point where progress appears blocked.
5. Listen for abrupt loops, clipping, dialogue/music imbalance, or a character/location track that
   feels tonally wrong.

## Results to record

| Run | Ch. 0 | Ch. 1 | Ch. 2 | Ch. 3 | Total | Losses/restarts | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 |  |  |  |  |  |  | pending |
| 2 |  |  |  |  |  |  | pending |
| 3 |  |  |  |  |  |  | pending |

For each run, note:

- whether movement, Talk, Visit, Item/Equip, combat range, and the objective were understandable;
- whether Tam felt powerful without making the escape objective irrelevant;
- whether Chapter 2 communicated rescue, defense duration, and unavoidable village damage;
- whether Chapter 3 communicated the farmhouse approach, three searches, sword, Trolloc, and exit;
- whether any chapter felt trivial, unfair, repetitive, or excessively slow;
- whether all three music roles were audible at a comfortable, consistent level;
- whether portraits, backgrounds, maps, transitions, victory, Game Over, and the ending rendered
  correctly on the player's real display.

The acceptance target is three soft-lock-free runs totaling 45–75 minutes each, with no repeated
clarity issue and no severe difficulty or audio defect. Record observations before changing
balance; after any balance change, restart the three-run count.
