from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

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


def verify_campaign_journey(
    project: Path,
    engine_root: Path,
    chapter_order: list[str],
    evidence_path: Path,
) -> dict[str, object]:
    """Drive real LT win/outro/next-level states across the complete campaign."""
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import driver, engine, game_state
        from app.events import triggers

        RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
        DB.load(project, CURRENT_SERIALIZATION_VERSION)
        success_events = {
            "wn00_tutorial": "tutorial_finish",
            "wn01_farm_escape": "farm_escape_success",
            "wn02_village_defense": "defense_win",
            "wn03_return_to_farm": "return_escape",
        }
        prerequisites = {
            "wn00_tutorial": {"delivered_cider": True},
            "wn01_farm_escape": {"tam_wound_started": False},
            "wn02_village_defense": {
                "rescued_west": True,
                "rescued_east": True,
                "rescued_south": True,
            },
            "wn03_return_to_farm": {
                "water_found": True,
                "bandages_found": True,
                "blankets_found": True,
                "sword_found": True,
            },
        }
        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            sprite_catalog.reset()
            driver.start(DB.constants.value("title"), from_editor=True)
            game = game_state.start_level(chapter_order[0])
            original_screenshot = driver.save_screenshot
            visited: list[str] = []
            forced: list[str] = []
            frame = 0
            reached_title = False
            held_key: int | None = None
            last_save_state: object | None = None

            def journey_hook(raw_events, surface):
                nonlocal frame, reached_title, held_key, last_save_state
                frame += 1
                import pygame

                if held_key is not None:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=held_key))
                    held_key = None
                    return
                level_id = game.level_nid
                if level_id and level_id not in visited:
                    visited.append(level_id)
                state = game.state.current()
                if state == "event":
                    state_object = game.state.current_state()
                    if getattr(state_object, "event", None):
                        state_object.event.skip(super_skip=True)
                elif state in {"in_chapter_save", "title_save"}:
                    state_object = game.state.current_state()
                    if (
                        state_object is not last_save_state
                        and getattr(state_object, "menu", None)
                        and not getattr(state_object, "wait_time", 0)
                    ):
                        last_save_state = state_object
                        held_key = pygame.K_x
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=held_key))
                elif state == "free" and level_id in success_events and level_id not in forced:
                    game.level_vars.update(prerequisites[level_id])
                    suffix = success_events[level_id]
                    prefab = next(
                        event
                        for event in DB.events
                        if event.level_nid == level_id and event.nid.endswith(f" {suffix}")
                    )
                    game.events._add_event(prefab, triggers.GenericTrigger())
                    forced.append(level_id)
                elif state == "title_start" and forced == chapter_order:
                    reached_title = True
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                if frame >= 3600:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

            driver.save_screenshot = journey_hook
            try:
                driver.run(game)
            finally:
                driver.save_screenshot = original_screenshot
                engine.terminate()

    result = {
        "verification_kind": "forced_event_campaign_transition_runtime",
        "input_driven": False,
        "engine_commit": (project / "ENGINE_COMMIT").read_text().strip(),
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(
            (project / "build_manifest.json").read_bytes()
        ).hexdigest(),
        "chapter_order_expected": chapter_order,
        "chapter_order_visited": visited,
        "success_events_forced": forced,
        "returned_to_title_after_final_chapter": reached_title,
        "frames": frame,
    }
    if visited != chapter_order or forced != chapter_order or not reached_title:
        raise RuntimeError(f"campaign journey failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
