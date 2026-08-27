from __future__ import annotations

import hashlib
import json

import yaml
from conftest import ROOT
from PIL import Image

from winternight_gen.visual_capture import _prepare_screenshot_directory


def test_gallery_refresh_preserves_input_flow_screenshots(tmp_path: Path) -> None:
    screenshots = tmp_path / "screenshots"
    screenshots.mkdir()
    for name in ("chapter-transition.png", "game-over.png", "old-gallery.png"):
        (screenshots / name).write_bytes(name.encode())
    stale_directory = screenshots / "stale"
    stale_directory.mkdir()
    (stale_directory / "frame.png").write_bytes(b"stale")

    _prepare_screenshot_directory(screenshots)

    assert (screenshots / "chapter-transition.png").is_file()
    assert (screenshots / "game-over.png").is_file()
    assert not (screenshots / "old-gallery.png").exists()
    assert not stale_directory.exists()


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


def test_campaign_overrides_title_ui_with_engine_sprite_keys(compiled_campaign):
    expected = {
        "resources/custom_sprites/logo.png": (220, 52),
        # LT animates eight 18px-high frames from this vertical strip.
        "resources/custom_sprites/press_start.png": (132, 144),
    }
    for relative, dimensions in expected.items():
        with Image.open(compiled_campaign / relative) as image:
            assert image.size == dimensions

    assert not (compiled_campaign / "resources/custom_sprites/title_logo.png").exists()


def test_campaign_dialogue_font_has_high_contrast_dark_palette(compiled_campaign):
    fonts = json.loads(
        (compiled_campaign / "resources/fonts/fonts.json").read_text(encoding="utf-8")
    )
    convo = next(font for font in fonts if font["nid"] == "convo")
    assert convo["palettes"]["black"][0][:3] == [32, 36, 42]


def test_approved_ai_assets_are_source_and_output_hash_locked(compiled_campaign):
    manifest = yaml.safe_load((ROOT / "design/asset_manifest.yaml").read_text(encoding="utf-8"))
    ai_assets = [
        asset
        for asset in manifest["assets"]
        if asset["provenance"] == "ai_generated" and asset["type"] != "reference"
    ]
    assert len(ai_assets) == 25

    expected_dimensions = {"portrait": (160, 112), "background": (240, 160)}
    for asset in ai_assets:
        assert asset["approval_status"] == "approved"
        source = ROOT / asset["source_path"]
        output = compiled_campaign / asset["processed_path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == asset["source_hash"]
        assert hashlib.sha256(output.read_bytes()).hexdigest() == asset["output_hash"]
        with Image.open(output) as image:
            rgba = image.convert("RGBA")
            assert image.size == expected_dimensions[asset["type"]]
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
