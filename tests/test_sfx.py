from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml
from conftest import ENGINE_ROOT, ROOT

from winternight_gen.sfx_pipeline import (
    authored_scene_sfx,
    load_sfx_design,
    register_lt_sfx,
    render_sfx,
    verify_authored_sfx_references,
    verify_rendered_sfx,
)

DESIGN_PATH = ROOT / "design" / "sfx.yaml"
ASSET_DIR = ROOT / "assets" / "sfx"

CORE_RUNTIME_SFX = {
    "Attack Hit 1",
    "Attack Hit 2",
    "Attack Hit 3",
    "Attack Hit 4",
    "Attack Hit 5",
    "Attack Miss 2",
    "Critical Hit 1",
    "Critical Hit 2",
    "Death",
    "Error",
    "Experience Gain",
    "Final Hit",
    "Info In",
    "Info Out",
    "Item",
    "Level Up",
    "Map In",
    "Map Out",
    "Map_Step_Infantry1",
    "Map_Step_Infantry2",
    "Next Turn",
    "No Damage",
    "Save",
    "Select 1",
    "Select 2",
    "Select 3",
    "Select 4",
    "Select 5",
    "Select 6",
    "StageClear",
    "Start",
    "Stat Up",
    "Status_Page_Change",
    "Talk_Boop",
}


@pytest.fixture(scope="module")
def sfx_design():
    return load_sfx_design(DESIGN_PATH)


def test_sfx_design_is_original_bounded_and_covers_authored_sounds(sfx_design):
    raw = yaml.safe_load(DESIGN_PATH.read_text(encoding="utf-8"))
    provenance = raw["provenance"]
    assert provenance["authorship"] == "original_procedural_sound_design"
    assert provenance["adaptation_label"] == "gameplay_invented"
    assert provenance["recorded_samples"] == "none"
    assert provenance["external_cues"] == "none"
    assert authored_scene_sfx(ROOT) == {
        "impact_heavy": {"sc_c1_door_bursts"},
        "combat_distant": {"sc_c1_tam_wounded"},
        "growl_nearby": {"sc_c3_trolloc_appears"},
        "fire_house_threat": {
            "sc_c2_house_west_ruined",
            "sc_c2_house_north_ruined",
            "sc_c2_house_east_ruined",
            "sc_c2_house_south_ruined",
            "sc_c2_unavoidable_damage_west",
            "sc_c2_unavoidable_damage_east",
        },
    }
    verify_authored_sfx_references(sfx_design, ROOT)
    by_nid = {effect.nid: effect for effect in sfx_design.effects}
    assert by_nid["impact_heavy"].role == "heavy_door_impact"
    assert by_nid["combat_distant"].role == "offscreen_combat_clashes"
    assert by_nid["growl_nearby"].role == "nearby_trolloc_warning"
    assert by_nid["fire_house_threat"].integration_status == "authored_scene"
    assert {alias for effect in sfx_design.effects for alias in effect.aliases} >= (
        CORE_RUNTIME_SFX
    )


def test_transition_cues_replace_long_default_runtime_fanfares(sfx_design):
    by_nid = {effect.nid: effect for effect in sfx_design.effects}
    phase_change = by_nid["phase_change"]
    save = by_nid["ui_save"]

    assert phase_change.aliases == ("Next Turn",)
    assert phase_change.integration_status == "engine_runtime"
    assert 250 <= phase_change.duration_ms <= 500
    assert save.aliases == ("Save",)
    assert save.integration_status == "engine_runtime"
    assert 250 <= save.duration_ms <= 600
    assert (sfx_design.sample_rate, sfx_design.channels) == (22_050, 1)


def test_sfx_beat_lineage_resolves(sfx_design):
    beat_ids = {
        beat["id"]
        for beat in yaml.safe_load((ROOT / "source/story_beats.yaml").read_text())["beats"]
    }
    for effect in sfx_design.effects:
        assert set(effect.source_beat_ids) <= beat_ids


def test_committed_sfx_matches_hash_locked_manifest(sfx_design):
    verify_rendered_sfx(sfx_design, ASSET_DIR)
    manifest = json.loads((ASSET_DIR / "sfx_manifest.json").read_text(encoding="utf-8"))
    assert manifest["provenance"] == {
        "creation": "Original deterministic procedural synthesis for this repository",
        "generator": "src/winternight_gen/sfx_pipeline.py",
        "samples": "None; every PCM sample is generated mathematically",
    }
    assert not list(ASSET_DIR.glob("*.wav"))


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_sfx_render_is_byte_deterministic(tmp_path, sfx_design):
    rendered = tmp_path / "sfx"
    manifest = render_sfx(DESIGN_PATH, rendered)
    assert {entry["nid"] for entry in manifest["effects"]} == {
        effect.nid for effect in sfx_design.effects
    }
    for effect in sfx_design.effects:
        assert (rendered / effect.filename).read_bytes() == (
            ASSET_DIR / effect.filename
        ).read_bytes()
    assert (rendered / "sfx.json").read_bytes() == (ASSET_DIR / "sfx.json").read_bytes()


def test_pinned_lt_sfx_catalog_registration(sfx_design):
    sys.path.insert(0, str(ENGINE_ROOT))
    from app.data.resources.resources import Resources

    resources = Resources()
    register_lt_sfx(resources, sfx_design, ASSET_DIR)
    expected_nids = [
        resource_nid
        for effect in sfx_design.effects
        for resource_nid in (
            effect.aliases
            if effect.integration_status == "engine_runtime"
            else (effect.nid, *effect.aliases)
        )
    ]
    assert resources.sfx.keys() == expected_nids
    assert set(resources.sfx.keys()) >= CORE_RUNTIME_SFX
    assert resources.sfx.get("impact_heavy").tag == "Winternight"
    assert resources.sfx.get("Select 1").full_path.endswith("ui_confirm.ogg")
    assert resources.sfx.get("Next Turn").full_path.endswith("phase_change.ogg")
    assert resources.sfx.get("Save").full_path.endswith("ui_save.ogg")
    assert resources.sfx.get("growl_nearby").full_path.endswith("growl_nearby.ogg")


def test_pinned_lt_runtime_decodes_and_starts_every_sfx():
    code = """
import json
import pathlib
import sys
import pygame

engine = pathlib.Path(sys.argv[1])
sfx_dir = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(engine))
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

from app.data.resources.resources import RESOURCES
from app.engine.sound import DefaultSoundController, SFX

RESOURCES.sfx.clear()
entries = json.loads((sfx_dir / 'sfx.json').read_text(encoding='utf-8'))
RESOURCES.sfx.load(str(sfx_dir), entries)
SFX.clear()
controller = DefaultSoundController()
for nid in RESOURCES.sfx.keys():
    effect = controller.play_sfx(nid)
    assert effect is not None, nid
    assert effect.get_length() >= 0.03, nid
    assert controller.stop_sfx(nid) is effect, nid
pygame.quit()
"""
    environment = os.environ.copy()
    environment.update(
        SDL_AUDIODRIVER="dummy",
        SDL_VIDEODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
    )
    subprocess.run(
        [sys.executable, "-c", code, str(ENGINE_ROOT), str(ASSET_DIR)],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )


def test_compiled_campaign_sfx_decodes_and_starts(compiled_campaign):
    code = """
import pathlib
import pygame
import sys

engine = pathlib.Path(sys.argv[1])
project = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(engine))
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

from app.data.resources.resources import RESOURCES
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.engine.sound import DefaultSoundController, SFX

RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
SFX.clear()
controller = DefaultSoundController()
for nid in RESOURCES.sfx.keys():
    effect = controller.play_sfx(nid)
    assert effect is not None, nid
    assert effect.get_length() >= 0.03, nid
    assert controller.stop_sfx(nid) is effect, nid
pygame.quit()
"""
    environment = os.environ.copy()
    environment.update(
        SDL_AUDIODRIVER="dummy",
        SDL_VIDEODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
    )
    subprocess.run(
        [sys.executable, "-c", code, str(ENGINE_ROOT), str(compiled_campaign)],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert (
        compiled_campaign / "resources/sfx/Next Turn.ogg"
    ).read_bytes() == (ASSET_DIR / "phase_change.ogg").read_bytes()
    assert (compiled_campaign / "resources/sfx/Save.ogg").read_bytes() == (
        ASSET_DIR / "ui_save.ogg"
    ).read_bytes()
