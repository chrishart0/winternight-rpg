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
    "emonds_field__festival_day": (
        "cb10eb0e061fa0c489748bdfe36f3c293ec5cf496d016a47fa48260a165bc78e"
    ),
    "emonds_field__winternight_attack": (
        "94f38fa295c9241a93c050958a8611da35366ef3a6309e3018599c3a182ea45d"
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
            observed[variant_id] = hashlib.sha256(
                "\n".join(variant["rows"]).encode()
            ).hexdigest()

    assert observed == EXPECTED_TOPOLOGY_HASHES


def test_campaign_tileset_has_lit_semantic_pixel_variants(compiled_campaign: Path) -> None:
    terrain_ids = {
        entry["terrain_id"]
        for layout in _map_specs()
        for entry in layout["legend"].values()
    }
    tileset_path = (
        compiled_campaign / "resources" / "tilesets" / "winternight_world_tiles.png"
    )
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


def test_map_variants_select_their_declared_lighting_row(
    compiled_campaign: Path,
) -> None:
    expected_rows = {
        "althor_farm__night_attack": 1,
        "althor_farm__ruined_return": 1,
        "emonds_field__festival_day": 0,
        "emonds_field__winternight_attack": 2,
    }
    tilemaps = json.loads(
        (
            compiled_campaign
            / "resources"
            / "tilemaps"
            / "tilemap_data"
            / "tilemaps.json"
        ).read_text()
    )

    for tilemap in tilemaps:
        sprite_grid = tilemap["layers"][0]["sprite_grid"]
        assert tilemap["tilesets"] == ["winternight_world_tiles"]
        assert {value[1][1] for value in sprite_grid.values()} == {
            expected_rows[tilemap["nid"]]
        }
        assert len({tuple(value[1]) for value in sprite_grid.values()}) >= 20
