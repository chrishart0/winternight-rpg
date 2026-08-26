from __future__ import annotations

from pathlib import Path

from winternight_gen.lt_runtime import generated_component_system

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"


def test_map_and_units_load_through_lt(compiled_project):
    with generated_component_system(ENGINE_ROOT):
        import sys

        sys.path.insert(0, str(ENGINE_ROOT))
        from app.data.database.database import Database
        from app.data.resources.resources import Resources
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

        resources = Resources()
        resources.load(compiled_project, CURRENT_SERIALIZATION_VERSION)
        database = Database()
        database.load(compiled_project, CURRENT_SERIALIZATION_VERSION)
    level = database.levels.get("minimal_chapter")
    tilemap = resources.tilemaps.get(level.tilemap)
    assert (tilemap.width, tilemap.height) == (10, 8)
    assert {unit.nid: tuple(unit.starting_position) for unit in level.units} == {
        "guide": (2, 4),
        "automaton": (7, 4),
    }
    assert all(tilemap.check_bounds(tuple(unit.starting_position)) for unit in level.units)
