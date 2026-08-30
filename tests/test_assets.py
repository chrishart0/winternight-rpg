from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from conftest import ENGINE_ROOT, ROOT
from PIL import Image

from winternight_gen.visual_capture import _prepare_screenshot_directory


def test_gallery_refresh_preserves_input_flow_screenshots(tmp_path: Path) -> None:
    screenshots = tmp_path / "screenshots"
    screenshots.mkdir()
    for name in (
        "chapter-transition.png",
        "game-over.png",
        "flow-inventory.png",
        "tutorial-after-mat.png",
        "old-gallery.png",
    ):
        (screenshots / name).write_bytes(name.encode())
    stale_directory = screenshots / "stale"
    stale_directory.mkdir()
    (stale_directory / "frame.png").write_bytes(b"stale")

    _prepare_screenshot_directory(screenshots)

    assert (screenshots / "chapter-transition.png").is_file()
    assert (screenshots / "game-over.png").is_file()
    assert (screenshots / "flow-inventory.png").is_file()
    assert (screenshots / "tutorial-after-mat.png").is_file()
    assert not (screenshots / "old-gallery.png").exists()
    assert not stale_directory.exists()


def test_tutorial_throw_and_miss_animations_are_registered(compiled_campaign):
    animations = compiled_campaign / "resources" / "animations"
    expected = {
        "MapMiss.png": (144, 12),
        "StoneThrow.png": (192, 32),
        "BallLightning.png": (192, 32),
    }
    for filename, dimensions in expected.items():
        with Image.open(animations / filename) as image:
            assert image.size == dimensions

    manifest = json.loads((animations / "animations.json").read_text())
    by_nid = {animation["nid"]: animation for animation in manifest}
    assert by_nid["MapMiss"]["num_frames"] == 6
    assert by_nid["StoneThrow"]["num_frames"] == 6
    assert by_nid["BallLightning"]["num_frames"] == 6


def test_placeholder_assets_have_engine_dimensions(compiled_project):
    expected = {
        "resources/panoramas/graybox_hall.png": (240, 160),
        "resources/portraits/guide_portrait.png": (160, 112),
        "resources/portraits/automaton_portrait.png": (160, 112),
        "resources/map_sprites/graybox_unit-stand.png": (192, 144),
        "resources/map_sprites/graybox_unit-move.png": (192, 160),
    }
    for relative, dimensions in expected.items():
        with Image.open(compiled_project / relative) as image:
            assert image.size == dimensions, relative
            assert image.format == "PNG"


def test_project_records_asset_provenance_and_hash_inventory(compiled_project):
    provenance = (compiled_project / "ASSET_PROVENANCE.md").read_text(encoding="utf-8")
    manifest = json.loads((compiled_project / "build_manifest.json").read_text())
    assert "No image model" in provenance
    assert manifest["engine_commit"] == "1820e585450f6f47605aebd686b2a3f13af181f0"
    assert "resources/portraits/guide_portrait.png" in manifest["generated_files"]


def test_placeholder_sprite_sheets_use_pinned_engine_colorkey(compiled_project, compiled_campaign):
    expected = (128, 160, 128, 255)
    paths = [
        compiled_project / "resources/map_sprites/graybox_unit-stand.png",
        compiled_project / "resources/portraits/guide_portrait.png",
        *sorted((compiled_campaign / "resources/map_sprites").glob("*-stand.png")),
        *sorted((compiled_campaign / "resources/portraits").glob("*.png")),
    ]

    assert paths
    for path in paths:
        with Image.open(path) as image:
            assert image.convert("RGBA").getpixel((0, 0)) == expected, path


def test_campaign_map_sprites_use_pinned_layout_palette_and_distinct_facings(
    compiled_campaign,
):
    pinned_palette = {
        (128, 160, 128, 255),
        (88, 72, 120, 255),
        (144, 184, 232, 255),
        (216, 232, 240, 255),
        (112, 96, 96, 255),
        (176, 144, 88, 255),
        (248, 248, 208, 255),
        (56, 56, 144, 255),
        (56, 80, 224, 255),
        (40, 160, 248, 255),
        (24, 240, 248, 255),
        (232, 16, 24, 255),
        (248, 248, 64, 255),
        (248, 248, 248, 255),
        (64, 56, 56, 255),
        (128, 136, 112, 255),
    }
    team_palette = {
        (56, 56, 144, 255),
        (56, 80, 224, 255),
        (40, 160, 248, 255),
        (24, 240, 248, 255),
    }
    sprites = compiled_campaign / "resources/map_sprites"
    manifest = yaml.safe_load((ROOT / "design/asset_manifest.yaml").read_text(encoding="utf-8"))
    expected_ids = {asset["id"] for asset in manifest["assets"] if asset["type"] == "map_sprite"}
    placeholder_ids = {
        asset["id"]
        for asset in manifest["assets"]
        if asset["type"] == "map_sprite" and asset["approval_status"] == "placeholder"
    }
    stand_paths = sorted(sprites.glob("*-stand.png"))
    assert {path.name.removesuffix("-stand.png") for path in stand_paths} == expected_ids
    for stand_path in stand_paths:
        move_path = stand_path.with_name(stand_path.name.replace("-stand", "-move"))
        with Image.open(stand_path) as stand, Image.open(move_path) as move:
            assert stand.size == (192, 144)
            assert move.size == (192, 160)
            assert set(stand.convert("RGBA").getdata()) <= pinned_palette
            assert set(move.convert("RGBA").getdata()) <= pinned_palette

            # Direction rows must be authored facings, not four copies of the
            # same front-facing graybox pose.
            frames = [move.crop((0, row * 40, 48, (row + 1) * 40)).tobytes() for row in range(4)]
            assert len(set(frames)) == 4, stand_path.name

            first_stand = stand.convert("RGBA").crop((0, 0, 64, 48))
            subject_points = [
                (index % 64, index // 64, pixel)
                for index, pixel in enumerate(first_stand.getdata())
                if pixel != (128, 160, 128, 255)
            ]
            height = (
                max(y for _, y, _ in subject_points)
                - min(y for _, y, _ in subject_points)
                + 1
            )
            # Approved AI identities are processed to GBA scale; deterministic
            # graybox placeholders draw a slightly taller body until the art pass.
            maximum_height = (
                34 if stand_path.name.removesuffix("-stand.png") in placeholder_ids else 27
            )
            assert height <= maximum_height, stand_path.name
            subject_colors = {pixel for _, _, pixel in subject_points}
            assert 6 <= len(subject_colors) <= 13, stand_path.name
            team_share = sum(
                pixel in team_palette for _, _, pixel in subject_points
            ) / len(subject_points)
            assert team_share >= 0.2, stand_path.name


def test_campaign_map_sprite_archetypes_have_distinct_silhouettes(compiled_campaign):
    sprites = compiled_campaign / "resources/map_sprites"
    silhouettes = {}
    for path in sorted(sprites.glob("*-stand.png")):
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            frame = rgba.crop((0, 0, 64, 48))
            mask = bytes(0 if pixel == (128, 160, 128, 255) else 1 for pixel in frame.getdata())
            silhouettes[path.stem] = hashlib.sha256(mask).hexdigest()
    assert len(set(silhouettes.values())) == len(silhouettes), silhouettes


def test_campaign_characters_have_approved_visual_assets() -> None:
    characters = yaml.safe_load((ROOT / "source/characters.yaml").read_text(encoding="utf-8"))[
        "characters"
    ]
    manifest = yaml.safe_load((ROOT / "design/asset_manifest.yaml").read_text(encoding="utf-8"))
    assets = {asset["id"]: asset for asset in manifest["assets"]}
    assignments = {
        character["id"]: character["combat"]["map_sprite"] for character in characters
    }
    assert len(set(assignments.values())) == len(assignments), assignments
    for character in characters:
        portrait = assets[character["portrait"]]
        map_sprite = assets[character["combat"]["map_sprite"]]
        assert portrait["type"] == "portrait", character["id"]
        assert map_sprite["type"] == "map_sprite", character["id"]
        for asset in (portrait, map_sprite):
            assert asset["provenance"] == "ai_generated", character["id"]
            assert asset["approval_status"] == "approved", character["id"]


def test_campaign_overrides_title_ui_with_engine_sprite_keys(compiled_campaign):
    expected = {
        "resources/custom_sprites/logo.png": (220, 72),
        # LT animates eight 18px-high frames from this vertical strip.
        "resources/custom_sprites/press_start.png": (132, 144),
    }
    for relative, dimensions in expected.items():
        with Image.open(compiled_campaign / relative) as image:
            assert image.size == dimensions

    assert not (compiled_campaign / "resources/custom_sprites/title_logo.png").exists()


def test_campaign_weapon_types_have_player_facing_icons(compiled_campaign):
    weapons = json.loads((compiled_campaign / "game_data/weapons.json").read_text())
    assert weapons

    with Image.open(compiled_campaign / "resources/icons16/wexp_icons.png") as image:
        assert image.size == (16 * len(weapons), 16)

    assert all(weapon["icon_nid"] == "wexp_icons" for weapon in weapons)
    assert [weapon["icon_index"] for weapon in weapons] == [
        [index, 0] for index in range(len(weapons))
    ]


def test_campaign_items_have_player_facing_icons(compiled_campaign):
    items = json.loads((compiled_campaign / "game_data/items.json").read_text())
    with Image.open(compiled_campaign / "resources/icons16/item_icons.png") as source:
        icons = source.convert("RGBA")
        assert icons.size == (16 * len(items), 16)
        assert all(
            any(pixel[3] for pixel in icons.crop((index * 16, 0, index * 16 + 16, 16)).getdata())
            for index in range(len(items))
        )

    assert all(item["icon_nid"] == "item_icons" for item in items)
    assert [item["icon_index"] for item in items] == [[index, 0] for index in range(len(items))]


def test_campaign_dialogue_font_has_high_contrast_dark_palette(compiled_campaign):
    fonts = json.loads(
        (compiled_campaign / "resources/fonts/fonts.json").read_text(encoding="utf-8")
    )
    convo = next(font for font in fonts if font["nid"] == "convo")
    assert convo["palettes"]["black"] == [
        [32, 36, 42, 255],
        [16, 20, 26, 0],
    ]
    assert convo["palettes"]["white"][1] == [8, 12, 16, 255]
    index = (compiled_campaign / "resources/fonts/convo.idx").read_text(encoding="utf-8")
    assert "stacked\n" in index
    assert "width 9\n" in index
    with Image.open(compiled_campaign / "resources/fonts/convo.png") as image:
        assert image.size == (144, 192)
        assert {alpha for *_, alpha in image.convert("RGBA").getdata()} <= {0, 255}


def test_campaign_dialogue_font_renders_dark_text_through_lt(compiled_campaign):
    code = r"""
import json
import sys
from pathlib import Path

engine_root = Path(sys.argv[1])
project = Path(sys.argv[2])
sys.path.insert(0, str(engine_root))

from app.data.resources.fonts import Font
from app.engine.bmpfont import BmpFont

raw = next(
    entry
    for entry in json.loads((project / "resources/fonts/fonts.json").read_text())
    if entry["nid"] == "convo"
)
font = Font(raw["nid"], default_color=raw["default_color"], palettes=raw["palettes"])
font.set_full_path(str(project / "resources/fonts/convo"))
bmp = BmpFont(font, headless=True)

def opaque_colors(surface):
    return sorted({
        tuple(surface.get_at((x, y)))
        for x in range(surface.get_width())
        for y in range(surface.get_height())
        if surface.get_at((x, y)).a
    })

high, low, _ = bmp._get_stacked_char_from_surf("A", "black")
print(json.dumps({"high": opaque_colors(high), "low": opaque_colors(low)}))
"""
    environment = os.environ.copy()
    environment.update({"SDL_VIDEODRIVER": "dummy", "PYGAME_HIDE_SUPPORT_PROMPT": "1"})
    result = subprocess.run(
        [sys.executable, "-c", code, str(ENGINE_ROOT), str(compiled_campaign)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    rendered = json.loads(result.stdout.splitlines()[-1])

    assert [32, 36, 42, 255] in rendered["high"]
    assert [248, 248, 248, 255] not in rendered["high"]
    assert rendered["low"] == []


def test_campaign_portrait_sheets_match_pinned_lt_frame_layout(compiled_campaign):
    portraits = sorted((compiled_campaign / "resources/portraits").glob("*.png"))

    assert portraits
    for path in portraits:
        with Image.open(path) as image:
            sheet = image.convert("RGBA")
            face = sheet.crop((32, 0, 128, 80))
            unused_top_left = sheet.crop((0, 0, 32, 80))
            neutral_blink = sheet.crop((128, 48, 160, 64))
            mouth = face.crop((30, 48, 62, 64))

            assert set(unused_top_left.getdata()) == {(128, 160, 128, 255)}, path
            assert (128, 160, 128, 255) in set(face.crop((0, 0, 1, 80)).getdata()), path
            assert (128, 160, 128, 255) in set(face.crop((95, 0, 96, 80)).getdata()), path
            assert neutral_blink.tobytes() == face.crop((30, 31, 62, 47)).tobytes(), path
            for x, y in (
                (96, 80),
                (64, 80),
                (32, 80),
                (0, 80),
                (64, 96),
                (32, 96),
                (0, 96),
            ):
                frame = sheet.crop((x, y, x + 32, y + 16))
                assert frame.tobytes() == mouth.tobytes(), path


def test_campaign_civilian_portraits_have_textured_pixel_detail(compiled_campaign):
    for name in ("villager_woman.png", "villager_man.png"):
        with Image.open(compiled_campaign / "resources/portraits" / name) as image:
            colors = image.convert("RGBA").getcolors(maxcolors=1_000_000)
            assert colors is not None
            assert 24 <= len(colors) <= 64


def test_approved_ai_assets_are_source_and_output_hash_locked(compiled_campaign):
    manifest = yaml.safe_load((ROOT / "design/asset_manifest.yaml").read_text(encoding="utf-8"))
    ai_assets = [
        asset
        for asset in manifest["assets"]
        if asset["provenance"] == "ai_generated"
        and asset["type"] != "reference"
        and asset["approval_status"] == "approved"
    ]
    assert len(ai_assets) == 65

    expected_dimensions = {
        "portrait": (160, 112),
        "background": (240, 160),
        "ui": (220, 72),
    }
    for asset in ai_assets:
        source = ROOT / asset["source_path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == asset["source_hash"]

        if asset["type"] == "map_sprite":
            outputs = (
                (asset["stand_processed_path"], asset["stand_output_hash"], (192, 144)),
                (asset["move_processed_path"], asset["move_output_hash"], (192, 160)),
            )
        else:
            outputs = (
                (
                    asset["processed_path"],
                    asset["output_hash"],
                    expected_dimensions[asset["type"]],
                ),
            )

        for relative, expected_hash, expected_size in outputs:
            output = compiled_campaign / relative
            assert hashlib.sha256(output.read_bytes()).hexdigest() == expected_hash
            with Image.open(output) as image:
                rgba = image.convert("RGBA")
                assert image.size == expected_size
                assert len(rgba.getcolors(maxcolors=1_000_000) or []) <= 64
                if asset["type"] == "portrait":
                    assert not any(
                        red >= 110 and blue >= 90 and min(red, blue) - green >= 35
                        for count, (red, green, blue, alpha) in rgba.getcolors(maxcolors=1_000_000)
                        if alpha and count
                    )


def test_asset_reference_lineage_resolves_and_is_source_hash_locked():
    manifest = yaml.safe_load((ROOT / "design/asset_manifest.yaml").read_text(encoding="utf-8"))
    assets = {asset["id"]: asset for asset in manifest["assets"]}
    for asset in assets.values():
        assert set(asset.get("reference_ids", [])) <= set(assets)
    references = [asset for asset in assets.values() if asset["type"] == "reference"]
    assert references
    for asset in references:
        source = ROOT / asset["source_path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == asset["source_hash"]


def test_campaign_content_hash_includes_ai_source_images(compiled_campaign):
    manifest = json.loads((compiled_campaign / "build_manifest.json").read_text())
    inputs = {entry["path"] for entry in manifest["inputs"]}
    assert "assets/generated_sources/cast_identity_chroma-v1.png" in inputs
    assert "assets/generated_sources/emonds_burning-v1.png" in inputs
    assert "assets/fonts/DepartureMono-Regular.otf" in inputs
