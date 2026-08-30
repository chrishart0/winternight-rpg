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


def test_tutorial_guide_lines_compile_below_units_without_terrain(compiled_campaign):
    with generated_component_system(ENGINE_ROOT):
        import sys

        sys.path.insert(0, str(ENGINE_ROOT))
        from app.data.resources.resources import Resources
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

        resources = Resources()
        resources.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)

    tilemap = resources.tilemaps.get("emonds_field__festival_day")
    assert "winternight_world_tiles__guides" in tilemap.tilesets
    expected = {
        "rand_attack_line": {
            (9, 6): (1, 0),
            (10, 6): (11, 0),
            (10, 7): (15, 0),
        },
        "mat_attack_line": {
            (13, 10): (7, 0),
            (12, 10): (9, 0),
            (11, 10): (16, 0),
        },
    }
    for layer_id, sprites in expected.items():
        layer = tilemap.layers.get(layer_id)
        assert layer.visible is False
        assert layer.foreground is False
        assert layer.terrain_grid == {}
        assert {
            point: tuple(sprite.tileset_position)
            for point, sprite in layer.sprite_grid.items()
        } == sprites
