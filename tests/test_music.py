from __future__ import annotations

import array
import dataclasses
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest
import yaml
from conftest import ENGINE_ROOT, ROOT

import winternight_gen.music_pipeline as music_pipeline
from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.music_pipeline import (
    STEPS_PER_BAR,
    apply_lt_music_assignments,
    build_score,
    load_music_design,
    register_lt_music,
    render_music,
    synthesize_pcm,
    verify_rendered_music,
)
from winternight_gen.packager import PACKAGE_NAME, package_private_build

DESIGN_PATH = ROOT / "design" / "music.yaml"
ASSET_DIR = ROOT / "assets" / "music"


@pytest.fixture(scope="module")
def music_design():
    return load_music_design(DESIGN_PATH)


def test_music_design_is_original_bounded_and_source_linked(music_design):
    raw = yaml.safe_load(DESIGN_PATH.read_text(encoding="utf-8"))
    provenance = raw["provenance"]
    assert provenance["authorship"] == "original_and_arranged"
    assert provenance["adaptation_label"] == "gameplay_invented_with_external_arrangement"
    assert provenance["samples"] == "none"
    assert "Blind Guardian" in provenance["external_melodies"]
    assert {track.role for track in music_design.tracks} == {
        "title_theme",
        "tutorial",
        "winternight_combat",
        "winternight_enemy_phase",
        "dark_return_and_ending",
        "dark_enemy_phase",
        "game_over",
    }
    beat_ids = {
        beat["id"]
        for beat in yaml.safe_load((ROOT / "source/story_beats.yaml").read_text())["beats"]
    }
    for track in raw["tracks"]:
        expected_label = (
            "third_party_arrangement" if track["nid"] == "wn_wheel_of_time" else "gameplay_invented"
        )
        assert track["adaptation_label"] == expected_label
        assert track["source_beat_ids"]
        assert set(track["source_beat_ids"]) <= beat_ids


def test_title_track_is_a_full_native_synthesizer_arrangement(music_design):
    track = next(track for track in music_design.tracks if track.nid == "wn_wheel_of_time")
    assert (music_design.title_track, track.filename, track.title, track.soundroom_index) == (
        "wn_wheel_of_time",
        "wn_wheel_of_time.ogg",
        "Wheel of Time",
        1,
    )
    assert (track.bpm, track.tonic_midi, track.bars) == (98, 51, 48)
    assert [section.name for section in track.form] == [
        "orchestral_intro",
        "riff_entry",
        "verse_a",
        "verse_b",
        "prechorus_build",
        "chorus_hook",
        "orchestral_break",
        "final_chorus",
    ]
    assert {role for section in track.form for role in section.parts} == {
        "pad",
        "bass",
        "lead",
        "counter",
        "arp",
    }
    voices = {part.voice for section in track.form for part in section.parts.values()}
    assert {"choir", "strings", "reed", "brass", "pulse", "bass_drive", "harp"} <= voices
    assert max(section.dynamic for section in track.form) - min(
        section.dynamic for section in track.form
    ) >= 0.45
    assert [section.drums.kit if section.drums else None for section in track.form] == [
        None,
        "entry",
        "gallop",
        "gallop",
        "build",
        "rock",
        "half_time",
        "finale",
    ]
    assert len(track.kits["gallop"]["kick"]) == 2 * STEPS_PER_BAR
    assert {
        part.pattern
        for section in track.form
        if (part := section.parts.get("pad")) is not None
    } >= {"sustain", "power_gallop", "power_chug", "power_eighths", "half_time", "hook_drive"}


def test_every_track_is_a_multi_section_arrangement(music_design):
    """Looping themes must be sectional, not one motif repeated for every bar.

    Short failure cues are exempt from the length and section-count bounds:
    GBA-era practice puts a death or game-over sting at 5-15 seconds, so
    holding it to a map-loop shape would be the wrong contract.
    """
    for track in music_design.tracks:
        seconds = track.bars * 4 * 60 / track.bpm
        names = [section.name for section in track.form]
        assert len(set(names)) == len(names), track.nid
        # Sections must differ in harmony or orchestration, so the loop develops.
        signatures = {
            (
                section.harmony,
                tuple(sorted((role, part.pattern) for role, part in section.parts.items())),
                section.drums.kit if section.drums else None,
            )
            for section in track.form
        }
        assert len(signatures) == len(track.form), track.nid
        if track.role == "game_over":
            assert 5.0 <= seconds <= 20.0, track.nid
            assert len(names) >= 2, track.nid
            assert not any(section.drums for section in track.form), track.nid
            continue
        assert len(names) >= 3, track.nid
        assert len({section.harmony for section in track.form}) >= 3, track.nid
        assert seconds >= 45.0, track.nid
        # More than one instrument role has to be carrying material.
        assert max(len(section.parts) for section in track.form) >= 4, track.nid


def test_score_events_stay_inside_the_declared_form(music_design):
    for track in music_design.tracks:
        score = build_score(track)
        assert score.total_steps == track.bars * STEPS_PER_BAR
        assert score.notes
        for note in score.notes:
            assert 0 <= note.step < score.total_steps
            assert note.steps > 0
            assert 21 <= note.midi <= 108
        for hit in score.drums:
            assert 0 <= hit.step < score.total_steps
        # Deterministic ordering keeps the noise generator reproducible.
        assert list(score.drums) == sorted(score.drums, key=lambda hit: (hit.step, hit.lane))


def test_master_stage_holds_the_ceiling_and_target_loudness(music_design):
    track = next(item for item in music_design.tracks if item.nid == "wn_black_wind")
    short = dataclasses.replace(
        track, form=tuple(section for section in track.form if section.name == "tag")
    )
    samples = synthesize_pcm(
        short,
        music_design.sample_rate,
        music_design.loop_fade_ms,
        music_design.master_rms_dbfs,
        music_design.master_knee,
    )
    peak = max(abs(sample) for sample in samples)
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    assert peak <= round(track.gain * 32767.0)
    assert abs(20.0 * math.log10(rms / 32767.0) - music_design.master_rms_dbfs) <= 1.0


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda track: track["form"][1].update({"bars": 7}), "harmony spans"),
        (
            lambda track: track["kits"]["march"].update({"hat": "x.x.x"}),
            "whole number of 16-step bars",
        ),
        (
            lambda track: track["phrases"]["bass_gallop"].append([0, 3]),
            "does not tile",
        ),
        (
            lambda track: track["form"][1].update({"lead": {"voice": "gong", "pattern": "x"}}),
            "unknown voice",
        ),
    ],
)
def test_design_rejects_scores_that_do_not_line_up(tmp_path, mutate, message):
    raw = yaml.safe_load(DESIGN_PATH.read_text(encoding="utf-8"))
    mutate(next(track for track in raw["tracks"] if track["nid"] == "wn_black_wind"))
    broken = tmp_path / "music.yaml"
    broken.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_music_design(broken)


def test_music_assignments_cover_every_campaign_chapter(music_design, campaign_bundle):
    assert set(music_design.level_music) == set(campaign_bundle.campaign.chapter_order)
    by_nid = {track.nid: track for track in music_design.tracks}
    mission_by_id = {mission.id: mission for mission in campaign_bundle.missions}
    for level_nid, assignment in music_design.level_music.items():
        assert {"player_phase", "enemy_phase"} <= set(assignment)
        has_combat = any(unit.team == "enemy" for unit in mission_by_id[level_nid].units)
        expected_keys = {"player_phase", "enemy_phase"}
        if has_combat:
            expected_keys |= {"player_battle", "enemy_battle"}
        assert set(assignment) == expected_keys
        player = by_nid[assignment["player_phase"]]
        enemy = by_nid[assignment["enemy_phase"]]
        if level_nid == "wn00_tutorial":
            assert player.nid == enemy.nid == assignment["player_battle"]
            assert assignment["enemy_battle"] == player.nid
            continue
        if not has_combat:
            continue
        assert player.nid != enemy.nid, level_nid
        assert enemy.role.endswith("enemy_phase"), level_nid
        # LT crossfades phase music over 400 ms without beat matching, so a
        # shared key and tempo is what keeps the handoff from lurching.
        assert (player.bpm, player.tonic_midi) == (enemy.bpm, enemy.tonic_midi), level_nid


def test_special_music_slots_cover_failure_and_class_change(music_design):
    assert music_design.special_music == {
        "game_over": "wn_broken_wheel",
        "promotion": "wn_hearthlight",
        "class_change": "wn_hearthlight",
    }
    cue = next(track for track in music_design.tracks if track.nid == "wn_broken_wheel")
    assert cue.role == "game_over"


def test_committed_music_matches_hash_locked_manifest(music_design):
    verify_rendered_music(music_design, ASSET_DIR)
    manifest = json.loads((ASSET_DIR / "music_manifest.json").read_text(encoding="utf-8"))
    assert manifest["design_sha256"] == hashlib.sha256(DESIGN_PATH.read_bytes()).hexdigest()
    assert (
        manifest["generator_sha256"]
        == hashlib.sha256(Path(music_pipeline.__file__).read_bytes()).hexdigest()
    )
    assert manifest["generator_version"] == "winternight-music-2"
    assert manifest["provenance"]["synthesis"].endswith("no recorded or external samples")


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_music_render_is_byte_deterministic(tmp_path, music_design):
    rendered = tmp_path / "music"
    manifest = render_music(DESIGN_PATH, rendered)
    assert {track["duration_seconds"] for track in manifest["tracks"]} == {
        track.bars * 4 * 60 / track.bpm for track in music_design.tracks
    }
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
        "Wheel of Time",
        "Hearthlight Before Snow",
        "Black Wind at the Palisade",
        "Shadow on the Snow",
        "Embers Under Snow",
        "The Last Light",
        "The Wheel Turns Away",
    ]
    assert resources.music.get("Black Wind at the Palisade").full_path.endswith("wn_black_wind.ogg")

    database = Database()
    for level_nid in music_design.level_music:
        database.levels.append(LevelPrefab(level_nid, level_nid))
    apply_lt_music_assignments(database, music_design)
    assert database.constants.value("music_main") == "Wheel of Time"
    assert database.constants.value("music_game_over") == "The Wheel Turns Away"
    assert database.constants.value("music_promotion") == "Hearthlight Before Snow"
    assert database.constants.value("music_class_change") == "Hearthlight Before Snow"
    assert database.levels.get("wn02_village_defense").music == {
        "player_phase": "Black Wind at the Palisade",
        "enemy_phase": "Shadow on the Snow",
        "player_battle": "Black Wind at the Palisade",
        "enemy_battle": "Shadow on the Snow",
    }
    assert database.levels.get("wn03_return_to_farm").music == {
        "player_phase": "Embers Under Snow",
        "enemy_phase": "The Last Light",
        "player_battle": "Black Wind at the Palisade",
        "enemy_battle": "Shadow on the Snow",
    }


def test_lt_display_titles_are_portable_resource_names(music_design):
    unsafe_track = dataclasses.replace(music_design.tracks[0], title="../Hearthlight")
    unsafe_design = dataclasses.replace(
        music_design, tracks=(unsafe_track, *music_design.tracks[1:])
    )
    sys.path.insert(0, str(ENGINE_ROOT))
    from app.data.resources.resources import Resources

    with pytest.raises(ValueError, match="portable LT resource name"):
        register_lt_music(Resources(), unsafe_design, ASSET_DIR)


def test_compiled_campaign_contains_music_and_level_assignments(
    compiled_campaign, music_design, campaign_bundle
):
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
        "Wheel of Time",
        "Hearthlight Before Snow",
        "Black Wind at the Palisade",
        "Shadow on the Snow",
        "Embers Under Snow",
        "The Last Light",
        "The Wheel Turns Away",
    ]
    assert database.constants.value("music_main") == "Wheel of Time"
    assert database.constants.value("music_game_over") == "The Wheel Turns Away"
    assert database.constants.value("music_promotion") == "Hearthlight Before Snow"
    assert database.constants.value("music_class_change") == "Hearthlight Before Snow"
    display_nids = {track.nid: track.title for track in music_design.tracks}
    for level_nid, assignment in music_design.level_music.items():
        assert database.levels.get(level_nid).music == {
            phase: display_nids[source_nid] for phase, source_nid in assignment.items()
        }
    for mission in campaign_bundle.missions:
        expected_track = display_nids[
            music_design.level_music[mission.id]["player_phase"]
        ]
        intro = next(
            event
            for event in database.events
            if event.level_nid == mission.id
            and event.nid.endswith(f" {mission.intro_scene}")
        )
        assert intro.source.splitlines()[0] == f"music;{expected_track};400"
    assert (compiled_campaign / "MUSIC_PROVENANCE.json").read_bytes() == (
        ASSET_DIR / "music_manifest.json"
    ).read_bytes()
    compiled_catalog = json.loads(
        (compiled_campaign / "resources/music/music.json").read_text(encoding="utf-8")
    )
    assert compiled_catalog == [
        ["Wheel of Time", False, False, 1],
        ["Hearthlight Before Snow", False, False, 2],
        ["Black Wind at the Palisade", False, False, 3],
        ["Shadow on the Snow", False, False, 4],
        ["Embers Under Snow", False, False, 5],
        ["The Last Light", False, False, 6],
        ["The Wheel Turns Away", False, False, 7],
    ]
    for track in resources.music:
        assert (compiled_campaign / "resources/music" / f"{track.nid}.ogg").is_file()
    for track in music_design.tracks:
        assert not (compiled_campaign / "resources/music" / track.filename).exists()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_encoded_music_has_headroom_consistent_loudness_and_safe_loop_seams(music_design):
    provenance = json.loads((ASSET_DIR / "music_manifest.json").read_text(encoding="utf-8"))
    by_nid = {entry["nid"]: entry for entry in provenance["tracks"]}
    rms_levels: list[float] = []
    for track in music_design.tracks:
        decoded = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(ASSET_DIR / track.filename),
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "-ac",
                "1",
                "-ar",
                str(music_design.sample_rate),
                "-",
            ],
            check=True,
            capture_output=True,
        ).stdout
        samples = array.array("h")
        samples.frombytes(decoded)
        assert len(samples) == by_nid[track.nid]["duration_samples"]

        peak = max(abs(sample) for sample in samples)
        rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
        peak_dbfs = 20.0 * math.log10(peak / 32767.0)
        rms_dbfs = 20.0 * math.log10(rms / 32767.0)
        assert -9.0 <= peak_dbfs <= -5.0
        assert -21.0 <= rms_dbfs <= -16.0
        assert abs(samples[0]) <= 128
        assert abs(samples[-1]) <= 128
        assert abs(samples[0] - samples[-1]) <= 128
        rms_levels.append(rms_dbfs)
    assert max(rms_levels) - min(rms_levels) <= 2.0


def test_packaged_project_contains_bound_music_bytes(compiled_campaign, tmp_path):
    package = package_private_build(ROOT, compiled_campaign, ENGINE_ROOT, tmp_path / "dist")
    archive = Path(str(package["archive"]))
    prefix = f"{PACKAGE_NAME}/winternight.ltproj"
    with tarfile.open(archive, "r:gz") as bundled:
        names = set(bundled.getnames())
        assert f"{prefix}/MUSIC_PROVENANCE.json" in names
        assert f"{prefix}/resources/music/music.json" in names
        packaged_provenance = bundled.extractfile(f"{prefix}/MUSIC_PROVENANCE.json")
        assert packaged_provenance is not None
        assert (
            packaged_provenance.read() == (compiled_campaign / "MUSIC_PROVENANCE.json").read_bytes()
        )
        for title in (
            "Wheel of Time",
            "Hearthlight Before Snow",
            "Black Wind at the Palisade",
            "Shadow on the Snow",
            "Embers Under Snow",
            "The Last Light",
            "The Wheel Turns Away",
        ):
            member = bundled.extractfile(f"{prefix}/resources/music/{title}.ogg")
            assert member is not None
            assert (
                member.read()
                == (compiled_campaign / "resources/music" / f"{title}.ogg").read_bytes()
            )


def _expected_lengths(music_design, key: str) -> str:
    """Catalog NID -> designed seconds, so the decode probe checks real durations.

    The committed source catalog is keyed by private composition ID; a compiled
    project is keyed by the authored title LT shows in its Sound Room.
    """
    return json.dumps(
        {getattr(track, key): track.bars * 4 * 60 / track.bpm for track in music_design.tracks}
    )


_DECODE_PROBE = """
import json
import pathlib
import sys
import pygame

engine = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(engine))
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

from app.data.resources.resources import RESOURCES
from app.engine.sound import DefaultSoundController, MUSIC

{load}

expected = json.loads(sys.argv[3])
MUSIC.clear()
controller = DefaultSoundController()
assert sorted(RESOURCES.music.keys()) == sorted(expected), RESOURCES.music.keys()
for nid in RESOURCES.music.keys():
    song = controller.fade_in(nid, fade_in=1, from_start=True)
    assert song is not None, nid
    length = song.song.get_length()
    # A truncated or silent deliverable shows up as a length that no longer
    # matches the authored bar count, whatever that count happens to be.
    assert abs(length - expected[nid]) <= 0.2, (nid, length, expected[nid])
    controller.clear()
pygame.quit()
"""

_AUDIO_ENVIRONMENT = {
    "SDL_AUDIODRIVER": "dummy",
    "SDL_VIDEODRIVER": "dummy",
    "PYGAME_HIDE_SUPPORT_PROMPT": "1",
}


def _run_decode_probe(load: str, target: Path, music_design, key: str) -> None:
    environment = os.environ.copy()
    environment.update(_AUDIO_ENVIRONMENT)
    subprocess.run(
        [
            sys.executable,
            "-c",
            _DECODE_PROBE.format(load=load),
            str(ENGINE_ROOT),
            str(target),
            _expected_lengths(music_design, key),
        ],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )


def test_pinned_lt_runtime_decodes_and_starts_every_track(music_design):
    _run_decode_probe(
        "RESOURCES.music.clear()\n"
        "entries = json.loads((pathlib.Path(sys.argv[2]) / 'music.json')"
        ".read_text(encoding='utf-8'))\n"
        "RESOURCES.music.load(str(sys.argv[2]), entries)",
        ASSET_DIR,
        music_design,
        "nid",
    )


def test_compiled_campaign_music_decodes_and_starts(compiled_campaign, music_design):
    _run_decode_probe(
        "from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION\n"
        "RESOURCES.load(pathlib.Path(sys.argv[2]), CURRENT_SERIALIZATION_VERSION)",
        compiled_campaign,
        music_design,
        "title",
    )


# Pinned LT spreads music over four channel pairs and starts the next track as
# soon as any channel reports that a fade finished, so a track can start while
# an older pair is still audible. The browser build hands SDL an unbounded
# native loop, which turns that older pair into a second song that never ends.
# This probe drives the real controller through the browser adapter and fails
# on any frame where two channels are audible at once.
_SINGLE_OWNER_PROBE = """
import pathlib
import runpy
import sys
from unittest.mock import patch

import pygame

engine_root = pathlib.Path(sys.argv[1])
project = pathlib.Path(sys.argv[2])
runtime_main = pathlib.Path(sys.argv[3])
sys.path.insert(0, str(engine_root))
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
pygame.display.set_mode((64, 64))

from app.data.database.database import DB
from app.data.resources.resources import RESOURCES
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.engine import engine, sound

RESOURCES.load(str(project), CURRENT_SERIALIZATION_VERSION)
DB.load(str(project), CURRENT_SERIALIZATION_VERSION)


class ChannelProbe:
    \"\"\"pygame exposes no per-channel paused flag, and a paused channel is
    still 'busy'. Track the pause bit so audibility is measured, not guessed.\"\"\"

    def __init__(self, real):
        self.real = real
        self.paused = False

    def play(self, sound_object, loops=0):
        self.paused = False
        return self.real.play(sound_object, loops)

    def stop(self):
        self.paused = False
        return self.real.stop()

    def pause(self):
        self.paused = True
        return self.real.pause()

    def unpause(self):
        self.paused = False
        return self.real.unpause()

    def __getattr__(self, name):
        return getattr(self.real, name)


original_channel_init = sound.Channel.__init__


def probed_init(self, name, nid, end_event):
    original_channel_init(self, name, nid, end_event)
    self._channel = ChannelProbe(self._channel)


sound.Channel.__init__ = probed_init

# Install the shipped browser adapter itself rather than a copy of it.
with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
    runtime = runpy.run_path(str(runtime_main))
real_platform = sys.platform
sys.platform = "emscripten"
try:
    runtime["install_browser_compatibility"]()
finally:
    sys.platform = real_platform

# Fades are engine-time driven, so a virtual clock makes the frame sequence
# exact instead of racing a wall clock.
now = {"ms": 0}
engine.get_time = lambda: now["ms"]

controller = sound.DefaultSoundController()
sound._soundthread = controller
controller.set_music_volume(0.3)

PHASE = "Black Wind at the Palisade"
ENEMY = "Shadow on the Snow"
BATTLE = "Embers Under Snow"


def audible():
    rows = []
    for pair in controller.channel_stack:
        for channel in (pair.channel, pair.battle):
            handle = channel._channel
            if handle.get_busy() and not handle.paused and handle.get_volume() > 0.01:
                rows.append((channel.nid, getattr(channel.current_song, "nid", None)))
    return rows


def tick(frames):
    for _ in range(frames):
        now["ms"] += 16
        controller.update([])
        rows = audible()
        assert len(rows) <= 1, (now["ms"], rows)


# Minimal sequence that leaves two tracks audible without the single-owner
# rule: a battle track restarts, the phase track replaces it, combat ends and
# fades back, then the phase track is requested again before the fade settles.
controller.fade_in(PHASE, fade_in=400, from_start=True)
tick(1)
controller.fade_in(ENEMY, fade_in=400)
tick(1)
controller.fade_back(400)
tick(3)
controller.fade_in(ENEMY, fade_in=400)
tick(12)

# The campaign's real combat-chapter shape: player phase, enemy phase, a battle
# track that differs from both, and the fade back out of combat. Every intended
# track must still take over, one at a time.
for expected, action in (
    (PHASE, lambda: controller.fade_in(PHASE, fade_in=400)),
    (ENEMY, lambda: controller.fade_in(ENEMY, fade_in=400, from_start=True)),
    (BATTLE, lambda: controller.battle_fade_in(BATTLE, from_start=True)),
    (ENEMY, lambda: controller.battle_fade_back(controller.song_stack[-1], from_start=True)),
    (PHASE, lambda: controller.fade_in(PHASE, fade_in=400)),
):
    action()
    tick(60)
    rows = audible()
    assert rows and rows[0][1] == expected, (expected, rows)

controller.clear()
tick(4)
assert audible() == []
pygame.quit()
"""


def test_browser_music_keeps_one_audible_track_through_real_transitions(compiled_campaign):
    environment = os.environ.copy()
    environment.update(_AUDIO_ENVIRONMENT)
    subprocess.run(
        [
            sys.executable,
            "-c",
            _SINGLE_OWNER_PROBE,
            str(ENGINE_ROOT),
            str(compiled_campaign),
            str(ROOT / "web" / "runtime_main.py"),
        ],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
