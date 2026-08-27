from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

from .build_report import tree_hash
from .lt_runtime import generated_component_system
from .runtime import isolated_engine_runtime


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def verify_title_new_game_flow(
    project: Path,
    engine_root: Path,
    evidence_path: Path,
    entry_chapter: str,
) -> dict[str, Any]:
    """Use real SELECT key events to enter the declared campaign entry chapter."""
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import config, driver, engine, game_state

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            sprite_catalog.reset()
            RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
            DB.load(project, CURRENT_SERIALIZATION_VERSION)
            # Keep the runtime non-standalone so engine termination returns to
            # this verifier and can persist evidence after the real title flow.
            driver.start(DB.constants.value("title"), from_editor=True)
            config.SETTINGS["text_speed"] = 0
            game = game_state.start_game()
            original_screenshot = driver.save_screenshot
            frame = 0
            pressed_states: list[str] = []
            pressed_keys: list[str] = []
            state_timeline: list[str] = []
            last_state = None
            pending_key_up: int | None = None
            reached_first_chapter = False

            def title_hook(raw_events, surface):
                nonlocal frame, last_state, pending_key_up, reached_first_chapter
                frame += 1
                import pygame

                state = game.state.current()
                if state != last_state:
                    state_timeline.append(state)
                    last_state = state
                if pending_key_up:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pending_key_up))
                    pending_key_up = None
                state_object = game.state.current_state()
                internal_state = getattr(state_object, "state", None)
                ready = state == "title_start" or (
                    state in {"title_main", "title_mode", "title_new"}
                    and internal_state in {"normal", "difficulty_wait", "death_wait", "growth_wait"}
                )
                if ready and state not in pressed_states and not pending_key_up:
                    key = pygame.K_s if state == "title_start" else pygame.K_x
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
                    pressed_states.append(state)
                    pressed_keys.append(pygame.key.name(key))
                    pending_key_up = key
                if game.level_nid == entry_chapter and state in {
                    "start_level_asset_loading",
                    "event",
                    "free",
                }:
                    reached_first_chapter = True
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif frame >= 1800:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

            driver.save_screenshot = title_hook
            try:
                driver.run(game)
            finally:
                driver.save_screenshot = original_screenshot
                engine.terminate()

    result = {
        "verification_kind": "real_pygame_title_input",
        "input_driven": True,
        "engine_commit": (project / "ENGINE_COMMIT").read_text().strip(),
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(
            (project / "build_manifest.json").read_bytes()
        ).hexdigest(),
        "pressed_states": pressed_states,
        "pressed_keys": pressed_keys,
        "state_timeline": state_timeline,
        "first_level": game.level_nid,
        "reached_first_chapter": reached_first_chapter,
        "frames": frame,
    }
    required = {"title_start", "title_main", "title_new"}
    if not reached_first_chapter or not required.issubset(pressed_states):
        raise RuntimeError(f"title new-game input flow failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
