from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from conftest import ENGINE_ROOT, ROOT

import winternight_gen.music_pipeline as music_pipeline
from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.music_pipeline import (
    apply_lt_music_assignments,
    load_music_design,
    register_lt_music,
    render_music,
    verify_rendered_music,
)

DESIGN_PATH = ROOT / "design" / "music.yaml"
ASSET_DIR = ROOT / "assets" / "music"


@pytest.fixture(scope="module")
def music_design():
    return load_music_design(DESIGN_PATH)


def test_music_design_is_original_bounded_and_source_linked(music_design):
    raw = yaml.safe_load(DESIGN_PATH.read_text(encoding="utf-8"))
    provenance = raw["provenance"]
    assert provenance["authorship"] == "original_procedural_composition"
    assert provenance["adaptation_label"] == "gameplay_invented"
    assert provenance["samples"] == "none"
    assert provenance["external_melodies"] == "none"
    assert {track.role for track in music_design.tracks} == {
        "title_and_tutorial",
        "winternight_combat",
        "dark_return_and_ending",
    }
    beat_ids = {
        beat["id"]
        for beat in yaml.safe_load((ROOT / "source/story_beats.yaml").read_text())["beats"]
    }
    for track in raw["tracks"]:
        assert track["adaptation_label"] == "gameplay_invented"
        assert track["source_beat_ids"]
        assert set(track["source_beat_ids"]) <= beat_ids


def test_committed_music_matches_hash_locked_manifest(music_design):
    verify_rendered_music(music_design, ASSET_DIR)
    manifest = json.loads((ASSET_DIR / "music_manifest.json").read_text(encoding="utf-8"))
    assert manifest["design_sha256"] == hashlib.sha256(DESIGN_PATH.read_bytes()).hexdigest()
    assert manifest["generator_sha256"] == hashlib.sha256(
        Path(music_pipeline.__file__).read_bytes()
    ).hexdigest()
    assert manifest["generator_version"] == "winternight-music-1"
    assert manifest["provenance"]["synthesis"].endswith("no recorded or external samples")


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_music_render_is_byte_deterministic(tmp_path, music_design):
    rendered = tmp_path / "music"
    manifest = render_music(DESIGN_PATH, rendered)
    assert {track["duration_seconds"] for track in manifest["tracks"]} == {24.0, 32.0, 38.4}
    for track in music_design.tracks:
        assert (rendered / track.filename).read_bytes() == (ASSET_DIR / track.filename).read_bytes()
    assert (rendered / "music.json").read_bytes() == (ASSET_DIR / "music.json").read_bytes()


def test_pinned_lt_catalog_registration_and_assignments(music_design):
    sys.path.insert(0, str(ENGINE_ROOT))
    from app.data.database.database import Database
    from app.data.database.levels import LevelPrefab
    from app.data.resources.resources import Resources

    resources = Resources()
    register_lt_music(resources, music_design, ASSET_DIR)
    assert resources.music.keys() == [
        "wn_hearthlight",
        "wn_black_wind",
        "wn_embers_on_snow",
    ]
    assert resources.music.get("wn_black_wind").full_path.endswith("wn_black_wind.ogg")

    database = Database()
    for level_nid in music_design.level_music:
        database.levels.append(LevelPrefab(level_nid, level_nid))
    apply_lt_music_assignments(database, music_design)
    assert database.constants.value("music_main") == "wn_hearthlight"
    assert database.levels.get("wn02_village_defense").music == {
        "player_phase": "wn_black_wind",
        "enemy_phase": "wn_black_wind",
    }


def test_compiled_campaign_contains_music_and_level_assignments(compiled_campaign):
    with generated_component_system(ENGINE_ROOT):
        sys.path.insert(0, str(ENGINE_ROOT))
        from app.data.database.database import Database
        from app.data.resources.resources import Resources
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

        resources = Resources()
        resources.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
        database = Database()
        database.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)

    assert resources.music.keys() == [
        "wn_hearthlight",
        "wn_black_wind",
        "wn_embers_on_snow",
    ]
    assert database.constants.value("music_main") == "wn_hearthlight"
    assert database.levels.get("wn00_tutorial").music["player_phase"] == "wn_hearthlight"
    assert database.levels.get("wn01_farm_escape").music["enemy_phase"] == "wn_black_wind"
    assert (
        database.levels.get("wn03_return_to_farm").music["player_phase"]
        == "wn_embers_on_snow"
    )
    assert (compiled_campaign / "MUSIC_PROVENANCE.json").is_file()
    for track in resources.music:
        assert (compiled_campaign / "resources/music" / f"{track.nid}.ogg").is_file()


def test_pinned_lt_runtime_decodes_and_starts_every_track():
    code = """
import json
import pathlib
import sys
import pygame

engine = pathlib.Path(sys.argv[1])
music_dir = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(engine))
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

from app.data.resources.resources import RESOURCES
from app.engine.sound import DefaultSoundController, MUSIC

RESOURCES.music.clear()
entries = json.loads((music_dir / 'music.json').read_text(encoding='utf-8'))
RESOURCES.music.load(str(music_dir), entries)
MUSIC.clear()
controller = DefaultSoundController()
for nid in RESOURCES.music.keys():
    song = controller.fade_in(nid, fade_in=1, from_start=True)
    assert song is not None, nid
    assert song.song.get_length() > 20.0, nid
    controller.clear()
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


def test_compiled_campaign_music_decodes_and_starts(compiled_campaign):
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
from app.engine.sound import DefaultSoundController, MUSIC

RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
MUSIC.clear()
controller = DefaultSoundController()
for nid in RESOURCES.music.keys():
    song = controller.fade_in(nid, fade_in=1, from_start=True)
    assert song is not None, nid
    assert song.song.get_length() > 20.0, nid
    controller.clear()
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
