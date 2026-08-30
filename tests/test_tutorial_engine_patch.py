from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from winternight_gen.engine_patch import verify_engine_patch
from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.mechanics import _chapter_tutorial, _working_directory
from winternight_gen.runtime import isolated_engine_runtime

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"


@pytest.fixture(scope="module")
def general_states():
    engine_path = str(ENGINE_ROOT)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    pygame.display.set_mode((1, 1))
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(ENGINE_ROOT):
        from app.engine import general_states

        yield general_states


def test_engine_patch_matches_tracked_patch():
    verify_engine_patch(ROOT, ENGINE_ROOT)


def test_engine_patch_ignores_external_diff_configuration(monkeypatch):
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", "false")
    verify_engine_patch(ROOT, ENGINE_ROOT)


def test_forced_tutorial_move_parses_unit_and_destination(monkeypatch, general_states):
    game = SimpleNamespace(
        level_vars={
            "_forced_move_unit": "rand",
            "_forced_move_position": "10,9",
        }
    )
    monkeypatch.setattr(general_states, "game", game)

    assert general_states._forced_tutorial_move() == ("rand", (10, 9))


def test_remaining_unit_count_ignores_finished_and_tile_units(
    monkeypatch, general_states
):
    units = [
        SimpleNamespace(position=(1, 1), finished=False, tags=[]),
        SimpleNamespace(position=(2, 2), finished=True, tags=[]),
        SimpleNamespace(position=(3, 3), finished=False, tags=["Tile"]),
        SimpleNamespace(position=None, finished=False, tags=[]),
    ]
    game = SimpleNamespace(get_player_units=lambda: units)
    monkeypatch.setattr(general_states, "game", game)
    monkeypatch.setattr(general_states.skill_system, "can_select", lambda unit: True)

    assert general_states._remaining_player_unit_count() == 1


def test_remaining_unit_prompt_names_count(general_states):
    assert general_states._remaining_units_prompt(1) == (
        "You still have 1 unit to move. "
        "Are you sure you want to end your turn?"
    )
    assert general_states._remaining_units_prompt(2) == (
        "You still have 2 units to move. "
        "Are you sure you want to end your turn?"
    )


def test_tutorial_lock_and_feedback_runtime(compiled_campaign):
    engine_path = str(ENGINE_ROOT)
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(ENGINE_ROOT):
        from app import sprites as sprite_catalog
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import driver, engine, game_state
        from app.events import triggers

        with isolated_engine_runtime(ENGINE_ROOT) as runtime_root, _working_directory(
            runtime_root
        ):
            sprite_catalog.reset()
            RESOURCES.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            DB.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            try:
                result = _chapter_tutorial(
                    game_state.start_level("wn00_tutorial"), triggers
                )
            finally:
                engine.terminate()

    assert all(result["checks"].values()), result["checks"]
