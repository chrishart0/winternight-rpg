from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import yaml
from conftest import ROOT
from PIL import Image

EXPECTED_TOPOLOGY_HASHES = {
    "althor_farm__night_attack": (
        "0df6fd155d13ee6f624f82d6423bf44271f0266b5e37e12cccaf3c169424b7a4"
    ),
    "althor_farm__ruined_return": (
        "7d5d61fb5fe0755eece284cdb82c1e604ced71cad887c44fa9daf1fefb93d61d"
    ),
    "emonds_field__burned_dawn": (
        "51607669ac3670244ad70515fa75b155388f8dd84521503438575f53f4f00315"
    ),
    "emonds_field__festival_day": (
        "1354f4d5c5ffb4a3477e498acd213f03af62cefef7ca1b0810477a59ef68e830"
    ),
    "emonds_field__winternight_attack": (
        "94f38fa295c9241a93c050958a8611da35366ef3a6309e3018599c3a182ea45d"
    ),
    "emonds_field_battle__winternight_attack": (
        "656c8a91a95e3bfa22cccb1e22f108fcade49afe3e6dee3640b8d870eab7c721"
    ),
    "westwood_road__night_march": (
        "76abb1b4426344b85e6d4c95d8025b75c4b4ce6da9c2e86e75f202d144d35a51"
    ),
}


def _map_specs() -> list[dict[str, object]]:
    return [
        yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "design" / "maps").glob("*.yaml"))
    ]


def test_visual_pass_preserves_approved_map_topology() -> None:
    observed = {}
    for layout in _map_specs():
        for variant in layout["variants"]:
            variant_id = f"{layout['id']}__{variant['id']}"
            observed[variant_id] = hashlib.sha256("\n".join(variant["rows"]).encode()).hexdigest()

    assert observed == EXPECTED_TOPOLOGY_HASHES


def test_campaign_tileset_has_lit_semantic_pixel_variants(compiled_campaign: Path) -> None:
    terrain_ids = {
        entry["terrain_id"] for layout in _map_specs() for entry in layout["legend"].values()
    }
    tileset_path = compiled_campaign / "resources" / "tilesets" / "winternight_world_tiles.png"
    catalog = json.loads(
        (compiled_campaign / "resources" / "tilesets" / "tilesets.json").read_text()
    )
    tileset = next(entry for entry in catalog if entry["nid"] == "winternight_world_tiles")

    with Image.open(tileset_path) as source:
        image = source.convert("RGBA")
        assert source.size == (16 * len(terrain_ids) * 4, 16 * 3)
        tile_hashes: dict[str, set[str]] = defaultdict(set)
        for coordinate, terrain_id in tileset["terrain_grid"].items():
            x, y = (int(value) for value in coordinate.split(","))
            tile = image.crop((x * 16, y * 16, x * 16 + 16, y * 16 + 16))
            tile_hashes[terrain_id].add(hashlib.sha256(tile.tobytes()).hexdigest())

    assert set(tile_hashes) == terrain_ids
    assert len(tileset["terrain_grid"]) == len(terrain_ids) * 4 * 3
    assert all(len(variants) >= 3 for variants in tile_hashes.values())

def test_battle_houses_use_coordinated_roofs_facades_and_occupancy_cues(
    compiled_campaign: Path,
) -> None:
    tilemaps = json.loads(
        (
            compiled_campaign / "resources" / "tilemaps" / "tilemap_data" / "tilemaps.json"
        ).read_text()
    )
    battle = next(
        tilemap
        for tilemap in tilemaps
        if tilemap["nid"] == "emonds_field_battle__winternight_attack"
    )
    sprites = battle["layers"][0]["sprite_grid"]
    assert sprites["9,1"][1][0] % 4 in {0, 1}
    assert sprites["9,2"][1][0] % 4 in {2, 3}
    assert sprites["2,13"][1][0] % 4 in {0, 1}
    assert sprites["2,14"][1][0] % 4 in {2, 3}

    catalog = json.loads(
        (compiled_campaign / "resources" / "tilesets" / "tilesets.json").read_text()
    )
    tileset = next(entry for entry in catalog if entry["nid"] == "winternight_world_tiles")
    coordinates = {
        terrain_id: sorted(
            (
                tuple(int(value) for value in coordinate.split(","))
                for coordinate, candidate in tileset["terrain_grid"].items()
                if candidate == terrain_id and coordinate.endswith(",2")
            )
        )
        for terrain_id in ("occupied_house", "empty_house")
    }
    with Image.open(
        compiled_campaign / "resources" / "tilesets" / "winternight_world_tiles.png"
    ) as source:
        source = source.convert("RGBA")
        bottom_tiles = {
            terrain_id: [
                source.crop((x * 16, y * 16, x * 16 + 16, y * 16 + 16))
                for x, y in terrain_coordinates[2:]
            ]
            for terrain_id, terrain_coordinates in coordinates.items()
        }

    def brightness(tiles: list[Image.Image]) -> int:
        return sum(
            red + green + blue
            for tile in tiles
            for red, green, blue, _ in tile.getdata()
        )

    assert brightness(bottom_tiles["occupied_house"]) > brightness(
        bottom_tiles["empty_house"]
    )


def test_battle_house_doors_are_cut_into_the_facade_they_stand_in(
    compiled_campaign: Path,
) -> None:
    catalog = json.loads(
        (compiled_campaign / "resources" / "tilesets" / "tilesets.json").read_text()
    )
    tileset = next(entry for entry in catalog if entry["nid"] == "winternight_world_tiles")
    firelit = {
        terrain_id: sorted(
            tuple(int(value) for value in coordinate.split(","))
            for coordinate, candidate in tileset["terrain_grid"].items()
            if candidate == terrain_id and coordinate.endswith(",2")
        )
        for terrain_id in ("occupied_house", "house_door", "closed_door")
    }
    with Image.open(
        compiled_campaign / "resources" / "tilesets" / "winternight_world_tiles.png"
    ) as source:
        image = source.convert("RGBA")
        tiles = {
            terrain_id: [
                image.crop((x * 16, y * 16, x * 16 + 16, y * 16 + 16))
                for x, y in coordinates
            ]
            for terrain_id, coordinates in firelit.items()
        }

    # Variant 2 is the windowed ground floor, so everything outside the window
    # is the bare shell that every wall-row tile of a house shares.
    wall = tiles["occupied_house"][2]
    gold = (244, 200, 80, 255)
    for terrain_id in ("house_door", "closed_door"):
        for door in tiles[terrain_id]:
            assert door.crop((0, 0, 16, 5)).tobytes() == wall.crop((0, 0, 16, 5)).tobytes()
            for x in (0, 1, 2, 13, 14, 15):
                assert [door.getpixel((x, y)) for y in range(16)] == [
                    wall.getpixel((x, y)) for y in range(16)
                ]

    for door in tiles["house_door"]:
        assert sum(pixel == gold for pixel in door.crop((0, 13, 16, 16)).getdata()) >= 24
        assert gold not in set(door.crop((0, 0, 16, 13)).getdata())
    for shut in tiles["closed_door"]:
        assert gold not in set(shut.getdata())


def test_festival_inn_door_is_tangible_and_distinct_at_native_resolution(
    compiled_campaign: Path,
) -> None:
    catalog = json.loads(
        (compiled_campaign / "resources" / "tilesets" / "tilesets.json").read_text()
    )
    tileset = next(entry for entry in catalog if entry["nid"] == "winternight_world_tiles")
    door_coordinate = next(
        coordinate
        for coordinate, terrain_id in tileset["terrain_grid"].items()
        if terrain_id == "inn_door" and coordinate.endswith(",0")
    )
    step_coordinate = next(
        coordinate
        for coordinate, terrain_id in tileset["terrain_grid"].items()
        if terrain_id == "inn_step" and coordinate.endswith(",0")
    )
    door_x, door_y = (int(value) for value in door_coordinate.split(","))
    step_x, step_y = (int(value) for value in step_coordinate.split(","))
    with Image.open(
        compiled_campaign / "resources" / "tilesets" / "winternight_world_tiles.png"
    ) as source:
        source = source.convert("RGBA")
        door = source.crop(
            (door_x * 16, door_y * 16, door_x * 16 + 16, door_y * 16 + 16)
        )
        step = source.crop(
            (step_x * 16, step_y * 16, step_x * 16 + 16, step_y * 16 + 16)
        )

    colors = set(door.getdata())
    assert (35, 28, 27, 255) in colors
    assert (176, 116, 60, 255) in colors
    assert (244, 200, 80, 255) in colors
    assert sum(color == (244, 200, 80, 255) for color in door.getdata()) >= 30
    assert sum(color == (244, 200, 80, 255) for color in step.getdata()) >= 40

    tilemaps = json.loads(
        (
            compiled_campaign / "resources" / "tilemaps" / "tilemap_data" / "tilemaps.json"
        ).read_text()
    )
    festival = next(
        tilemap for tilemap in tilemaps if tilemap["nid"] == "emonds_field__festival_day"
    )
    assert festival["layers"][0]["terrain_grid"]["9,7"] == "inn_door"
    assert festival["layers"][0]["terrain_grid"]["9,8"] == "inn_step"


def test_map_variants_select_their_declared_lighting_row(
    compiled_campaign: Path,
) -> None:
    expected_rows = {
        "althor_farm__night_attack": 1,
        "althor_farm__ruined_return": 1,
        "emonds_field__burned_dawn": 0,
        "emonds_field__festival_day": 0,
        "emonds_field__winternight_attack": 2,
        "emonds_field_battle__winternight_attack": 2,
        "westwood_road__night_march": 1,
    }
    tilemaps = json.loads(
        (
            compiled_campaign / "resources" / "tilemaps" / "tilemap_data" / "tilemaps.json"
        ).read_text()
    )

    for tilemap in tilemaps:
        sprite_grid = tilemap["layers"][0]["sprite_grid"]
        assert tilemap["tilesets"][0] == "winternight_world_tiles"
        assert {value[1][1] for value in sprite_grid.values()} == {expected_rows[tilemap["nid"]]}
        assert len({tuple(value[1]) for value in sprite_grid.values()}) >= 20
