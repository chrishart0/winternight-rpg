---
name: mission-coherence
description: Review one complete playable mission for agreement between narrative setup, player goals, map readability, available actions, objective progression, feedback, and win or loss conditions. Use when a level or tutorial feels confusing, its core loop is unclear, or it needs an end-to-end clarity review; do not rewrite or rebalance the mission unless asked.
---

# Mission Coherence

Review the level as one continuous first-time-player journey, from the last setup beat before control through the outro or retry path. Do not infer coherence from individually valid specifications, reachable coordinates, passing triggers, or an automated driver that already knows the solution.

At every required mission state, determine whether a player can answer four questions from information the game actually presents:

1. What must I do now?
2. Where is the relevant person, object, tile, or exit?
3. How do I perform the action with the controls and action names the game exposes?
4. What changed, and what should I do next?

## Keep the review bounded

- Review authored mission intent, player-facing communication, and observed runtime behavior together.
- Distinguish mandatory progression, optional activity, tutorial practice, and scenery.
- Report problems and bounded remedies. Change specifications, compiler code, tests, or assets only when the user asks for implementation.
- This review does not replace mission authoring or build verification. If the repository provides `tactical-mission-designer` or `game-verifier` skills and the user also requests that work, use them; otherwise complete the coherence review without them.
- Follow `AGENTS.md` and the current phase in `EXEC_PLAN.md`. Never patch `build/` or `vendor/lt-maker` to make a finding disappear.

## Reconstruct the actual level

Read the mission, map, scenes, gameplay rules, relevant compiler or adapter path, and current runtime evidence. Trace the public actions and state gates required to finish, including:

- entry scene and handoff to player control;
- each objective text and the condition that replaces it;
- camera position, units, regions, props, markers, and action-menu labels;
- inventory or equipment assumptions;
- optional branches and how they are labeled;
- win, loss, timeout, retry, and outro behavior.

Write the route in player verbs such as “move beside Mat and choose Talk,” not internal verbs such as “set `talked_to_mat`.” Note any hidden prerequisite or hard-coded coordinate the game never communicates.

## Build the coherence trace

For every required state transition, record:

| State | Player-facing goal | Visible target or cue | Available public action | Completion feedback and next goal |
| --- | --- | --- | --- | --- |
| Mission start | What the game asks now | What the player can identify at native resolution | Exact movement, control, and menu verb | What visibly changes after success |

Treat a blank or contradictory cell as a finding. Review the following relationships explicitly:

- **Fiction and mechanics:** Objects described in dialogue must be identifiable as already carried, inventory items, map props, abstract deliveries, or scenery. Do not let prose imply a pickup that does not exist.
- **Goal and action:** Objectives must name the recognizable target and use, teach, or clearly lead to the engine's actual action. Explain adjacency, standing on a region, opening a menu, equipping an item, or ending a turn when the player cannot reasonably infer it.
- **Goal and space:** Required targets need a legible identity and persistent cue at native resolution. Inspect the relevant camera framing, contrast, occlusion, marker size, and whether ordinary terrain or unrelated units compete with the cue.
- **Prompt and gate:** Do not expose a prompt before its action exists or silently unlock an action without announcing it. When a prerequisite changes availability, review the frame, objective, and action menu on both sides of that gate.
- **Task list and victory:** The stated mandatory work must match the actual win condition. Name specific required conversations or collections when category language would conceal the count. Mark optional combat, exploration, and rewards as optional.
- **Action and feedback:** Completion must acknowledge success, remove or transform the old cue, and present the next goal. A flag changing or a region disappearing is not sufficient player feedback by itself.
- **Failure and recovery:** A player who walks to the wrong tile, visits a gate early, dismisses a tutorial, or returns after a turn should receive useful direction rather than a silent no-op or soft lock.

## Gather player-relevant evidence

Prefer the smallest evidence that tests the uncertain boundary, then broaden only where assembly matters.

- Use static tracing to establish the intended state graph and find contradictions.
- Inspect the compiled objective strings, region conditions, action labels, and event transitions when an existing build is current. A review request alone does not authorize replacing the build.
- Capture the native-resolution map at mission start and after every meaningful gate. For interaction problems, also capture the cursor on the target, the available action menu, and the immediate result. Enlargements may aid inspection but do not replace the native frame.
- Exercise the route with real input when practical. Record what a player can observe, not only the internal flags reached.
- Treat scripted playthroughs that contain target IDs, coordinates, or preselected actions as reachability evidence only. They cannot prove discoverability or clarity.
- Do not make human-usability, timing, or difficulty claims from headless checks. Identify the exact remaining human question.

Automate durable contracts below the full journey—for example, that an objective names the canonical action and location after a gate, or that an unlocked required region has a visible cue. Avoid screenshot hashes or OCR as the primary proof of subjective readability; retain reviewed screenshots as evidence.

## Report the review

Lead with `coherent`, `partially coherent`, or `incoherent`, followed by the earliest point where player understanding breaks. Include:

1. the intended loop and the actual required route;
2. the completed coherence trace;
3. findings ranked `blocking`, `major`, or `minor`, each tied to observed evidence;
4. the smallest source-level remedy for each material finding, without editing generated output;
5. checks that would demonstrate the remedy works;
6. remaining human playtest questions.

Do not bury the central failure beneath polish notes. Prefer a small sequence correction or explicit cue over adding prose everywhere, and preserve the mission's narrative and tactical purpose unless the user authorizes a redesign.
