"""Deterministic multi-voice music renderer for the Winternight slice.

The design file is a small tracker-style score: named harmony blocks, named
monophonic phrases on a sixteenth-note grid, named accompaniment and drum
patterns, and an ordered form that assigns instrument roles per section. The
synthesizer is band-limited additive: every timbre is a normalized wavetable
summed from sine partials below Nyquist, so pulse and reed leads stay clean at
22.05 kHz instead of aliasing. Only the standard library and PyYAML are used;
no recordings, samples, MIDI, or model-generated audio are involved.
"""

from __future__ import annotations

import array
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

GENERATOR_VERSION = "winternight-music-2"
SCHEMA_VERSION = "2.0"
_INVALID_LT_MUSIC_NID = re.compile(r'[\\/*?:"<>|\x00-\x1f]')

STEPS_PER_BEAT = 4
STEPS_PER_BAR = 4 * STEPS_PER_BEAT

_ROLES = ("pad", "bass", "lead", "counter", "arp")
_DRUM_LANES = ("kick", "snare", "hat", "openhat", "tom", "crash", "stick")
_PATTERN_CHARS = {".": 0.0, "o": 0.55, "x": 1.0, "X": 1.3}
_VOICINGS = ("chord", "power", "wide")

# Pinned LT resolves map music as ``<team>_phase`` in app/engine/phase.py and
# battle music as ``<team>_battle`` or ``boss_battle`` in animation_combat.py.
_LEVEL_MUSIC_KEYS = {
    "player_phase",
    "enemy_phase",
    "enemy2_phase",
    "other_phase",
    "player_battle",
    "enemy_battle",
    "enemy2_battle",
    "other_battle",
    "boss_battle",
}
_SPECIAL_MUSIC_CONSTANTS = {
    "game_over": "music_game_over",
    "promotion": "music_promotion",
    "class_change": "music_class_change",
}

# Register guards. Bass roots are authored relative to the chord, so folding
# keeps a descending progression from walking off the bottom of the mix.
_BASS_LOW = 33
_BASS_HIGH = 52


@dataclass(frozen=True)
class Voice:
    """A band-limited additive timbre plus its amplitude envelope."""

    name: str
    harmonics: tuple[tuple[int, float], ...]
    attack: float
    decay: float
    sustain: float
    release: float
    gate: float = 0.95
    vibrato_hz: float = 0.0
    vibrato_cents: float = 0.0
    vibrato_delay: float = 0.0
    detune_cents: float = 0.0
    dark_time: float = 0.0
    dark_tilt: float = 0.5
    level: float = 1.0


def _pulse_harmonics(duty: float, count: int) -> tuple[tuple[int, float], ...]:
    """Fourier partials of a bipolar pulse train, so the table is band-limited."""
    return tuple(
        (harmonic, math.sin(math.pi * harmonic * duty) / harmonic)
        for harmonic in range(1, count + 1)
        if abs(math.sin(math.pi * harmonic * duty)) > 1e-9
    )


def _saw_harmonics(count: int, tilt: float = 1.0) -> tuple[tuple[int, float], ...]:
    return tuple((harmonic, 1.0 / harmonic**tilt) for harmonic in range(1, count + 1))


_VOICES: dict[str, Voice] = {
    "flute": Voice(
        name="flute",
        harmonics=((1, 1.0), (2, 0.14), (3, 0.05), (4, 0.02)),
        attack=0.045,
        decay=0.12,
        sustain=0.82,
        release=0.16,
        gate=0.96,
        vibrato_hz=5.2,
        vibrato_cents=13.0,
        vibrato_delay=0.22,
        level=0.9,
    ),
    "reed": Voice(
        name="reed",
        harmonics=((1, 1.0), (2, 0.22), (3, 0.46), (4, 0.16), (5, 0.3), (6, 0.1), (7, 0.14)),
        attack=0.028,
        decay=0.1,
        sustain=0.8,
        release=0.14,
        gate=0.94,
        vibrato_hz=5.6,
        vibrato_cents=11.0,
        vibrato_delay=0.18,
        dark_time=0.5,
        dark_tilt=0.72,
        level=0.72,
    ),
    "strings": Voice(
        name="strings",
        harmonics=_saw_harmonics(12, 1.25),
        attack=0.16,
        decay=0.3,
        sustain=0.78,
        release=0.34,
        gate=1.0,
        vibrato_hz=4.6,
        vibrato_cents=7.0,
        vibrato_delay=0.3,
        detune_cents=7.0,
        dark_time=0.7,
        dark_tilt=0.6,
        level=0.62,
    ),
    "choir": Voice(
        name="choir",
        harmonics=((1, 1.0), (2, 0.32), (3, 0.2), (4, 0.09), (5, 0.05)),
        attack=0.3,
        decay=0.4,
        sustain=0.85,
        release=0.45,
        gate=1.0,
        vibrato_hz=4.2,
        vibrato_cents=9.0,
        vibrato_delay=0.4,
        detune_cents=9.0,
        level=0.66,
    ),
    "brass": Voice(
        name="brass",
        harmonics=((1, 1.0), (2, 0.62), (3, 0.42), (4, 0.3), (5, 0.19), (6, 0.11), (7, 0.06)),
        attack=0.035,
        decay=0.16,
        sustain=0.76,
        release=0.16,
        gate=0.93,
        vibrato_hz=5.0,
        vibrato_cents=6.0,
        vibrato_delay=0.28,
        dark_time=0.35,
        dark_tilt=0.55,
        level=0.6,
    ),
    "harp": Voice(
        name="harp",
        harmonics=((1, 1.0), (2, 0.38), (3, 0.16), (4, 0.09), (5, 0.04)),
        attack=0.004,
        decay=0.42,
        sustain=0.1,
        release=0.3,
        gate=1.0,
        level=0.8,
    ),
    "bell": Voice(
        name="bell",
        harmonics=((1, 1.0), (3, 0.42), (5, 0.2), (7, 0.09), (9, 0.05)),
        attack=0.002,
        decay=0.7,
        sustain=0.05,
        release=0.5,
        gate=1.0,
        level=0.6,
    ),
    "pulse": Voice(
        name="pulse",
        harmonics=_pulse_harmonics(0.25, 24),
        attack=0.006,
        decay=0.09,
        sustain=0.72,
        release=0.07,
        gate=0.9,
        level=0.5,
    ),
    "pulse_wide": Voice(
        name="pulse_wide",
        harmonics=_pulse_harmonics(0.5, 24),
        attack=0.008,
        decay=0.12,
        sustain=0.7,
        release=0.09,
        gate=0.92,
        detune_cents=6.0,
        level=0.44,
    ),
    "pulse_soft": Voice(
        name="pulse_soft",
        harmonics=_pulse_harmonics(0.125, 20),
        attack=0.012,
        decay=0.14,
        sustain=0.6,
        release=0.1,
        gate=0.88,
        level=0.5,
    ),
    "bass_round": Voice(
        name="bass_round",
        harmonics=((1, 1.0), (2, 0.3), (3, 0.1), (4, 0.04)),
        attack=0.008,
        decay=0.16,
        sustain=0.7,
        release=0.1,
        gate=0.9,
        level=1.0,
    ),
    "bass_pluck": Voice(
        name="bass_pluck",
        harmonics=((1, 1.0), (2, 0.45), (3, 0.24), (4, 0.13), (5, 0.07)),
        attack=0.003,
        decay=0.2,
        sustain=0.32,
        release=0.1,
        gate=0.86,
        dark_time=0.18,
        dark_tilt=0.45,
        level=0.95,
    ),
    "bass_drive": Voice(
        name="bass_drive",
        harmonics=_saw_harmonics(8, 1.1),
        attack=0.004,
        decay=0.1,
        sustain=0.6,
        release=0.06,
        gate=0.82,
        dark_time=0.14,
        dark_tilt=0.5,
        level=0.66,
    ),
}


@dataclass(frozen=True)
class Chord:
    root: int
    intervals: tuple[int, ...]
    beats: int


@dataclass(frozen=True)
class Event:
    """One phrase step: ``value`` is ``None`` for a rest."""

    value: int | None
    steps: int
    velocity: float = 1.0


@dataclass(frozen=True)
class Part:
    voice: str
    pattern: str
    gain: float
    octave: int
    echo: bool = False
    voicing: str = "chord"


@dataclass(frozen=True)
class Drums:
    kit: str
    gain: float
    fill: bool


@dataclass(frozen=True)
class Section:
    name: str
    bars: int
    harmony: str
    dynamic: float
    parts: dict[str, Part]
    drums: Drums | None


@dataclass(frozen=True)
class Echo:
    steps: int
    gain: float


@dataclass(frozen=True)
class MusicTrack:
    nid: str
    filename: str
    title: str
    role: str
    bpm: int
    tonic_midi: int
    seed: int
    gain: float
    soundroom_index: int
    harmony: dict[str, tuple[Chord, ...]]
    phrases: dict[str, tuple[Event, ...]]
    arps: dict[str, tuple[Event, ...]]
    comps: dict[str, str]
    kits: dict[str, dict[str, str]]
    form: tuple[Section, ...]
    echo: Echo | None = None

    @property
    def bars(self) -> int:
        return sum(section.bars for section in self.form)


@dataclass(frozen=True)
class MusicDesign:
    schema_version: str
    sample_rate: int
    channels: int
    sample_width_bits: int
    codec: str
    encoder_quality: int
    loop_fade_ms: int
    master_rms_dbfs: float
    master_knee: float
    tracks: tuple[MusicTrack, ...]
    title_track: str
    level_music: dict[str, dict[str, str]]
    special_music: dict[str, str]


@dataclass(frozen=True)
class NoteEvent:
    step: int
    steps: int
    midi: int
    velocity: float
    voice: str
    echo: bool


@dataclass(frozen=True)
class DrumHit:
    step: int
    lane: str
    velocity: float


@dataclass(frozen=True)
class Score:
    total_steps: int
    notes: tuple[NoteEvent, ...] = field(default=())
    drums: tuple[DrumHit, ...] = field(default=())


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def _require_sequence(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _parse_chords(raw: Any, name: str) -> tuple[Chord, ...]:
    chords: list[Chord] = []
    for entry in _require_sequence(raw, name):
        values = _require_sequence(entry, f"{name} chord")
        if len(values) != 3:
            raise ValueError(f"{name} chord must be [root, intervals, beats]")
        intervals = tuple(int(value) for value in _require_sequence(values[1], f"{name} intervals"))
        if not intervals or intervals[0] != 0:
            raise ValueError(f"{name} chord intervals must start at 0")
        beats = int(values[2])
        if beats <= 0:
            raise ValueError(f"{name} chord beats must be positive")
        chords.append(Chord(int(values[0]), intervals, beats))
    if not chords:
        raise ValueError(f"{name} needs at least one chord")
    return tuple(chords)


def _parse_events(raw: Any, name: str) -> tuple[Event, ...]:
    events: list[Event] = []
    for entry in _require_sequence(raw, name):
        values = _require_sequence(entry, f"{name} event")
        if len(values) not in {2, 3}:
            raise ValueError(f"{name} event must be [value, steps] or [value, steps, velocity]")
        steps = int(values[1])
        if steps <= 0:
            raise ValueError(f"{name} event step count must be positive")
        velocity = float(values[2]) if len(values) == 3 else 1.0
        if not 0.0 < velocity <= 2.0:
            raise ValueError(f"{name} event velocity must be within (0, 2]")
        value = None if values[0] is None else int(values[0])
        events.append(Event(value, steps, velocity))
    if not events:
        raise ValueError(f"{name} needs at least one event")
    return tuple(events)


def _parse_pattern(raw: Any, name: str) -> str:
    pattern = str(raw)
    if not pattern or len(pattern) % STEPS_PER_BAR:
        raise ValueError(f"{name} must be a whole number of 16-step bars")
    unknown = set(pattern) - set(_PATTERN_CHARS)
    if unknown:
        raise ValueError(f"{name} uses unsupported step characters: {sorted(unknown)}")
    return pattern


def _parse_part(raw: Any, role: str, name: str) -> Part:
    entry = _require_mapping(raw, name)
    voice = str(entry.get("voice", ""))
    if voice not in _VOICES:
        raise ValueError(f"{name} uses an unknown voice: {voice!r}")
    default_octave = {"pad": 0, "bass": -1, "lead": 1, "counter": 0, "arp": 1}[role]
    pattern = str(entry.get("pattern", "sustain" if role == "pad" else ""))
    if not pattern:
        raise ValueError(f"{name} needs a pattern name")
    voicing = str(entry.get("voicing", "chord"))
    if voicing not in _VOICINGS:
        raise ValueError(f"{name} voicing must be one of {_VOICINGS}")
    gain = float(entry.get("gain", 1.0))
    if not 0.0 < gain <= 2.0:
        raise ValueError(f"{name} gain must be within (0, 2]")
    unknown_keys = set(entry) - {"voice", "pattern", "gain", "octave", "echo", "voicing"}
    if unknown_keys:
        raise ValueError(f"{name} has unsupported keys: {sorted(unknown_keys)}")
    return Part(
        voice=voice,
        pattern=pattern,
        gain=gain,
        octave=int(entry.get("octave", default_octave)),
        echo=bool(entry.get("echo", False)),
        voicing=voicing,
    )


def _parse_track(entry: dict[str, Any], sample_rate: int) -> MusicTrack:
    nid = str(entry.get("nid", ""))
    filename = str(entry.get("filename", ""))
    if not nid:
        raise ValueError("track NID must be non-empty")
    if filename != f"{nid}.ogg" or Path(filename).name != filename:
        raise ValueError(f"track {nid} filename must be exactly {nid}.ogg")

    bpm = int(entry.get("bpm", 0))
    if bpm <= 0 or (sample_rate * 60) % (bpm * STEPS_PER_BEAT):
        raise ValueError(f"track {nid} bpm must produce an integral sample count per sixteenth")

    harmony = {
        str(name): _parse_chords(block, f"track {nid} harmony {name}")
        for name, block in _require_mapping(entry.get("harmony"), f"track {nid} harmony").items()
    }
    phrases = {
        str(name): _parse_events(events, f"track {nid} phrase {name}")
        for name, events in _require_mapping(
            entry.get("phrases", {}), f"track {nid} phrases"
        ).items()
    }
    arps = {
        str(name): _parse_events(events, f"track {nid} arp {name}")
        for name, events in _require_mapping(entry.get("arps", {}), f"track {nid} arps").items()
    }
    comps = {
        str(name): _parse_pattern(pattern, f"track {nid} comp {name}")
        for name, pattern in _require_mapping(entry.get("comps", {}), f"track {nid} comps").items()
    }
    kits: dict[str, dict[str, str]] = {}
    for kit_name, lanes in _require_mapping(entry.get("kits", {}), f"track {nid} kits").items():
        lane_map = _require_mapping(lanes, f"track {nid} kit {kit_name}")
        unknown_lanes = set(lane_map) - set(_DRUM_LANES) - {"fill"}
        if unknown_lanes:
            raise ValueError(
                f"track {nid} kit {kit_name} has unknown lanes: {sorted(unknown_lanes)}"
            )
        parsed: dict[str, str] = {}
        for lane, pattern in lane_map.items():
            if lane == "fill":
                fill_map = _require_mapping(pattern, f"track {nid} kit {kit_name} fill")
                unknown_fill = set(fill_map) - set(_DRUM_LANES)
                if unknown_fill:
                    raise ValueError(
                        f"track {nid} kit {kit_name} fill has unknown lanes: {sorted(unknown_fill)}"
                    )
                for fill_lane, fill_pattern in fill_map.items():
                    fill_text = _parse_pattern(
                        fill_pattern, f"track {nid} kit {kit_name} fill {fill_lane}"
                    )
                    if len(fill_text) != STEPS_PER_BAR:
                        raise ValueError(
                            f"track {nid} kit {kit_name} fill {fill_lane} must be exactly one bar"
                        )
                    parsed[f"fill.{fill_lane}"] = fill_text
                continue
            parsed[str(lane)] = _parse_pattern(pattern, f"track {nid} kit {kit_name} lane {lane}")
        kits[str(kit_name)] = parsed

    form: list[Section] = []
    for index, raw_section in enumerate(_require_sequence(entry.get("form"), f"track {nid} form")):
        section_raw = _require_mapping(raw_section, f"track {nid} form[{index}]")
        label = f"track {nid} section {section_raw.get('name', index)}"
        bars = int(section_raw.get("bars", 0))
        if bars <= 0:
            raise ValueError(f"{label} needs a positive bar count")
        harmony_name = str(section_raw.get("harmony", ""))
        if harmony_name not in harmony:
            raise ValueError(f"{label} references unknown harmony {harmony_name!r}")
        block_steps = sum(chord.beats for chord in harmony[harmony_name]) * STEPS_PER_BEAT
        section_steps = bars * STEPS_PER_BAR
        if block_steps != section_steps:
            raise ValueError(
                f"{label} harmony spans {block_steps} steps but the section spans {section_steps}"
            )
        dynamic = float(section_raw.get("dynamic", 1.0))
        if not 0.0 < dynamic <= 1.5:
            raise ValueError(f"{label} dynamic must be within (0, 1.5]")

        parts: dict[str, Part] = {}
        for role in _ROLES:
            raw_part = section_raw.get(role)
            if raw_part is None:
                continue
            part = _parse_part(raw_part, role, f"{label} {role}")
            registry = comps if role == "pad" else arps if role == "arp" else phrases
            if role == "pad" and part.pattern == "sustain":
                parts[role] = part
                continue
            if part.pattern not in registry:
                raise ValueError(f"{label} {role} references unknown pattern {part.pattern!r}")
            if role == "pad":
                span = len(comps[part.pattern])
            else:
                span = sum(event.steps for event in registry[part.pattern])
            if section_steps % span:
                raise ValueError(
                    f"{label} {role} pattern {part.pattern!r} spans {span} steps, "
                    f"which does not tile {section_steps}"
                )
            parts[role] = part

        drums: Drums | None = None
        raw_drums = section_raw.get("drums")
        if raw_drums is not None:
            drum_entry = _require_mapping(raw_drums, f"{label} drums")
            kit_name = str(drum_entry.get("kit", ""))
            if kit_name not in kits:
                raise ValueError(f"{label} references unknown kit {kit_name!r}")
            for lane, pattern in kits[kit_name].items():
                if lane.startswith("fill."):
                    continue
                if section_steps % len(pattern):
                    raise ValueError(
                        f"{label} kit lane {lane} spans {len(pattern)} steps, "
                        f"which does not tile {section_steps}"
                    )
            gain = float(drum_entry.get("gain", 1.0))
            if not 0.0 < gain <= 2.0:
                raise ValueError(f"{label} drum gain must be within (0, 2]")
            drums = Drums(kit=kit_name, gain=gain, fill=bool(drum_entry.get("fill", False)))

        unknown_keys = set(section_raw) - {"name", "bars", "harmony", "dynamic", "drums", *_ROLES}
        if unknown_keys:
            raise ValueError(f"{label} has unsupported keys: {sorted(unknown_keys)}")
        form.append(
            Section(
                name=str(section_raw.get("name", f"section{index}")),
                bars=bars,
                harmony=harmony_name,
                dynamic=dynamic,
                parts=parts,
                drums=drums,
            )
        )
    if not form:
        raise ValueError(f"track {nid} needs at least one form section")

    echo: Echo | None = None
    raw_echo = entry.get("echo")
    if raw_echo is not None:
        echo_entry = _require_mapping(raw_echo, f"track {nid} echo")
        steps = int(echo_entry.get("steps", 0))
        echo_gain = float(echo_entry.get("gain", 0.0))
        if not 1 <= steps <= STEPS_PER_BAR:
            raise ValueError(f"track {nid} echo steps must be within 1..{STEPS_PER_BAR}")
        if not 0.0 < echo_gain < 0.7:
            raise ValueError(f"track {nid} echo gain must be within (0, 0.7)")
        echo = Echo(steps=steps, gain=echo_gain)

    soundroom_index = int(entry.get("soundroom_index", 0))
    gain = float(entry.get("gain", 0.0))
    if not 0.0 < gain < 0.98:
        raise ValueError(f"track {nid} gain must be a target peak within (0, 0.98)")
    return MusicTrack(
        nid=nid,
        filename=filename,
        title=str(entry.get("title", nid)),
        role=str(entry.get("role", "")),
        bpm=bpm,
        tonic_midi=int(entry.get("tonic_midi", 0)),
        seed=int(entry.get("seed", 0)),
        gain=gain,
        soundroom_index=soundroom_index,
        harmony=harmony,
        phrases=phrases,
        arps=arps,
        comps=comps,
        kits=kits,
        form=tuple(form),
        echo=echo,
    )


def load_music_design(path: Path) -> MusicDesign:
    raw = _require_mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "music design")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"music design schema_version must be {SCHEMA_VERSION!r}")
    if raw.get("generator_version") != GENERATOR_VERSION:
        raise ValueError(f"music design generator_version must be {GENERATOR_VERSION!r}")

    render = _require_mapping(raw.get("render"), "render")
    sample_rate = int(render.get("sample_rate", 0))
    channels = int(render.get("channels", 0))
    sample_width_bits = int(render.get("sample_width_bits", 0))
    codec = str(render.get("codec", ""))
    encoder_quality = int(render.get("encoder_quality", -1))
    loop_fade_ms = int(render.get("loop_boundary_fade_ms", 0))
    master_rms_dbfs = float(render.get("master_rms_dbfs", 0.0))
    master_knee = float(render.get("master_knee", 0.0))
    if sample_rate not in {22050, 44100}:
        raise ValueError("render.sample_rate must be 22050 or 44100")
    if channels != 1 or sample_width_bits != 16:
        raise ValueError("the deterministic synthesizer supports 16-bit mono PCM only")
    if codec != "vorbis":
        raise ValueError("LT music must use the configured Vorbis encoder")
    if not 0 <= encoder_quality <= 10:
        raise ValueError("render.encoder_quality must be within 0..10")
    if not 1 <= loop_fade_ms <= 40:
        raise ValueError("render.loop_boundary_fade_ms must be within 1..40")
    if not -24.0 <= master_rms_dbfs <= -12.0:
        raise ValueError("render.master_rms_dbfs must be within -24..-12")
    if not 0.2 <= master_knee <= 0.9:
        raise ValueError("render.master_knee must be within 0.2..0.9")

    tracks: list[MusicTrack] = []
    seen_nids: set[str] = set()
    seen_indices: set[int] = set()
    for index, item in enumerate(_require_sequence(raw.get("tracks"), "tracks")):
        track = _parse_track(_require_mapping(item, f"tracks[{index}]"), sample_rate)
        if track.nid in seen_nids:
            raise ValueError(f"duplicate track NID: {track.nid}")
        if track.soundroom_index <= 0 or track.soundroom_index in seen_indices:
            raise ValueError("soundroom indices must be unique positive integers")
        seen_nids.add(track.nid)
        seen_indices.add(track.soundroom_index)
        tracks.append(track)

    expected_indices = list(range(1, len(tracks) + 1))
    if sorted(seen_indices) != expected_indices:
        raise ValueError(f"soundroom indices must be consecutive: {expected_indices}")

    assignments = _require_mapping(raw.get("assignments"), "assignments")
    title_track = str(assignments.get("title", ""))
    levels_raw = _require_mapping(assignments.get("levels"), "assignments.levels")
    level_music: dict[str, dict[str, str]] = {}
    for level, music in levels_raw.items():
        phases = {
            str(key): str(value) for key, value in _require_mapping(music, str(level)).items()
        }
        unknown_music_keys = set(phases) - _LEVEL_MUSIC_KEYS
        if unknown_music_keys:
            raise ValueError(
                f"level {level} uses music keys pinned LT never resolves: "
                f"{sorted(unknown_music_keys)}"
            )
        level_music[str(level)] = phases
    special_raw = _require_mapping(assignments.get("special", {}), "assignments.special")
    unknown_special = set(special_raw) - set(_SPECIAL_MUSIC_CONSTANTS)
    if unknown_special:
        raise ValueError(f"unsupported special music slots: {sorted(unknown_special)}")
    special_music = {str(slot): str(nid) for slot, nid in special_raw.items()}
    referenced = {title_track, *special_music.values()} | {
        track for assignment in level_music.values() for track in assignment.values()
    }
    missing = referenced - seen_nids
    if missing:
        raise ValueError(f"music assignments reference unknown tracks: {sorted(missing)}")
    return MusicDesign(
        schema_version=SCHEMA_VERSION,
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bits=sample_width_bits,
        codec=codec,
        encoder_quality=encoder_quality,
        loop_fade_ms=loop_fade_ms,
        master_rms_dbfs=master_rms_dbfs,
        master_knee=master_knee,
        tracks=tuple(tracks),
        title_track=title_track,
        level_music=level_music,
        special_music=special_music,
    )


# --------------------------------------------------------------------------
# Score construction
# --------------------------------------------------------------------------


def _chord_timeline(chords: tuple[Chord, ...]) -> list[Chord]:
    timeline: list[Chord] = []
    for chord in chords:
        timeline.extend([chord] * (chord.beats * STEPS_PER_BEAT))
    return timeline


def _fold(midi: int, low: int, high: int) -> int:
    while midi < low:
        midi += 12
    while midi > high:
        midi -= 12
    return midi


def _chord_tone(intervals: tuple[int, ...], index: int) -> int:
    size = len(intervals)
    return intervals[index % size] + 12 * (index // size)


def _pad_intervals(chord: Chord, voicing: str) -> tuple[int, ...]:
    if voicing == "power":
        return (0, 7, 12)
    if voicing == "wide":
        # Octave doubling above the root fills the pad without crowding the
        # bass register, which matters in a 22.05 kHz mono mix.
        return tuple(dict.fromkeys((*chord.intervals, 12)))
    return chord.intervals


def _tiled_events(events: tuple[Event, ...], span: int, total: int) -> list[tuple[int, Event]]:
    placed: list[tuple[int, Event]] = []
    for offset in range(0, total, span):
        cursor = offset
        for event in events:
            placed.append((cursor, event))
            cursor += event.steps
    return placed


def build_score(track: MusicTrack) -> Score:
    """Flatten the authored form into absolute-step note and drum events."""
    notes: list[NoteEvent] = []
    drums: list[DrumHit] = []
    bar_cursor = 0
    for section in track.form:
        section_steps = section.bars * STEPS_PER_BAR
        origin = bar_cursor * STEPS_PER_BAR
        timeline = _chord_timeline(track.harmony[section.harmony])
        dynamic = section.dynamic

        pad = section.parts.get("pad")
        if pad is not None:
            voicing = pad.voicing
            base = track.tonic_midi + 12 * pad.octave
            amplitude = pad.gain * dynamic
            if pad.pattern == "sustain":
                step = 0
                while step < section_steps:
                    chord = timeline[step]
                    length = chord.beats * STEPS_PER_BEAT
                    for interval in _pad_intervals(chord, voicing):
                        notes.append(
                            NoteEvent(
                                step=origin + step,
                                steps=length,
                                midi=base + chord.root + interval,
                                velocity=amplitude,
                                voice=pad.voice,
                                echo=pad.echo,
                            )
                        )
                    step += length
            else:
                pattern = track.comps[pad.pattern]
                hits = [
                    index
                    for index in range(section_steps)
                    if _PATTERN_CHARS[pattern[index % len(pattern)]] > 0.0
                ]
                for position, step in enumerate(hits):
                    end = hits[position + 1] if position + 1 < len(hits) else section_steps
                    chord = timeline[step]
                    accent = _PATTERN_CHARS[pattern[step % len(pattern)]]
                    for interval in _pad_intervals(chord, voicing):
                        notes.append(
                            NoteEvent(
                                step=origin + step,
                                steps=max(1, end - step),
                                midi=base + chord.root + interval,
                                velocity=amplitude * accent,
                                voice=pad.voice,
                                echo=pad.echo,
                            )
                        )

        for role in ("bass", "lead", "counter", "arp"):
            part = section.parts.get(role)
            if part is None:
                continue
            registry = track.arps if role == "arp" else track.phrases
            events = registry[part.pattern]
            span = sum(event.steps for event in events)
            base = track.tonic_midi + 12 * part.octave
            amplitude = part.gain * dynamic
            for step, event in _tiled_events(events, span, section_steps):
                if event.value is None:
                    continue
                chord = timeline[step]
                if role == "bass":
                    midi = _fold(base + chord.root + event.value, _BASS_LOW, _BASS_HIGH)
                elif role == "arp":
                    midi = base + chord.root + _chord_tone(chord.intervals, event.value)
                else:
                    midi = base + event.value
                notes.append(
                    NoteEvent(
                        step=origin + step,
                        steps=event.steps,
                        midi=midi,
                        velocity=amplitude * event.velocity,
                        voice=part.voice,
                        echo=part.echo,
                    )
                )

        if section.drums is not None:
            kit = track.kits[section.drums.kit]
            gain = section.drums.gain * dynamic
            fill_start = section_steps - STEPS_PER_BAR if section.drums.fill else section_steps
            for lane in _DRUM_LANES:
                pattern = kit.get(lane)
                fill_pattern = kit.get(f"fill.{lane}")
                if pattern is None and fill_pattern is None:
                    continue
                for step in range(section_steps):
                    if step >= fill_start and fill_pattern is not None:
                        symbol = fill_pattern[(step - fill_start) % STEPS_PER_BAR]
                    elif step >= fill_start and any(key.startswith("fill.") for key in kit):
                        # A fill bar replaces every authored lane, so lanes without
                        # a fill pattern stay silent instead of doubling the fill.
                        continue
                    elif pattern is None:
                        continue
                    else:
                        symbol = pattern[step % len(pattern)]
                    accent = _PATTERN_CHARS[symbol]
                    if accent <= 0.0:
                        continue
                    drums.append(DrumHit(step=origin + step, lane=lane, velocity=gain * accent))

        bar_cursor += section.bars

    notes.sort(key=lambda note: (note.step, note.voice, note.midi, note.steps))
    drums.sort(key=lambda hit: (hit.step, hit.lane))
    return Score(total_steps=bar_cursor * STEPS_PER_BAR, notes=tuple(notes), drums=tuple(drums))


# --------------------------------------------------------------------------
# Synthesis
# --------------------------------------------------------------------------

_TABLE_SIZE = 2048
_TABLE_CACHE: dict[tuple[str, int], tuple[tuple[float, ...], tuple[float, ...] | None]] = {}


def _midi_frequency(note: int) -> float:
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def _build_table(harmonics: tuple[tuple[int, float], ...]) -> list[float]:
    scale = 2.0 * math.pi / _TABLE_SIZE
    table = [0.0] * _TABLE_SIZE
    for harmonic, amplitude in harmonics:
        for index in range(_TABLE_SIZE):
            table[index] += amplitude * math.sin(harmonic * index * scale)
    return table


def _voice_tables(
    voice: Voice, max_harmonic: int
) -> tuple[tuple[float, ...], tuple[float, ...] | None]:
    """Return the (bright, dark) wavetables band-limited to ``max_harmonic``."""
    key = (voice.name, max_harmonic)
    cached = _TABLE_CACHE.get(key)
    if cached is not None:
        return cached
    harmonics = tuple(
        (harmonic, amplitude) for harmonic, amplitude in voice.harmonics if harmonic <= max_harmonic
    ) or ((1, 1.0),)
    bright = _build_table(harmonics)
    peak = max(abs(value) for value in bright) or 1.0
    dark: tuple[float, ...] | None = None
    if voice.dark_time > 0.0:
        tilted = tuple(
            (harmonic, amplitude * voice.dark_tilt ** (harmonic - 1))
            for harmonic, amplitude in harmonics
        )
        dark = tuple(value / peak for value in _build_table(tilted))
    result = (tuple(value / peak for value in bright), dark)
    _TABLE_CACHE[key] = result
    return result


def _render_note(
    bus: list[float],
    sample_rate: int,
    start: int,
    gate_samples: int,
    midi: int,
    amplitude: float,
    voice: Voice,
) -> None:
    if start >= len(bus) or gate_samples <= 0:
        return
    frequency = _midi_frequency(midi)
    max_harmonic = max(1, int(0.45 * sample_rate / frequency))
    bright, dark = _voice_tables(voice, max_harmonic)

    attack = max(1, int(sample_rate * voice.attack))
    decay = max(1, int(sample_rate * voice.decay))
    release = max(1, int(sample_rate * voice.release))
    sustain = voice.sustain
    gate = max(1, int(gate_samples * voice.gate))

    if gate <= attack:
        gate_level = gate / attack
    elif gate <= attack + decay:
        gate_level = 1.0 + (sustain - 1.0) * (gate - attack) / decay
    else:
        gate_level = sustain

    total = gate + release
    end = min(len(bus), start + total)
    level = amplitude * voice.level
    step = frequency * _TABLE_SIZE / sample_rate
    dark_samples = int(sample_rate * voice.dark_time) if dark is not None else 0
    vibrato_step = 2.0 * math.pi * voice.vibrato_hz / sample_rate
    vibrato_depth = 2.0 ** (voice.vibrato_cents / 1200.0) - 1.0
    vibrato_delay = int(sample_rate * voice.vibrato_delay)
    detune_step = step * 2.0 ** (voice.detune_cents / 1200.0)
    has_vibrato = voice.vibrato_hz > 0.0 and vibrato_depth > 0.0
    has_detune = voice.detune_cents > 0.0

    phase = 0.0
    detune_phase = 0.0
    lfo = 0.0
    size = _TABLE_SIZE
    for index in range(end - start):
        if index < attack:
            envelope = index / attack
        elif index < attack + decay:
            envelope = 1.0 + (sustain - 1.0) * (index - attack) / decay
        elif index < gate:
            envelope = sustain
        else:
            remaining = 1.0 - (index - gate) / release
            envelope = gate_level * remaining * remaining

        position = int(phase)
        fraction = phase - position
        first = bright[position]
        value = first + (bright[(position + 1) & (size - 1)] - first) * fraction
        if dark_samples:
            weight = index / dark_samples if index < dark_samples else 1.0
            dark_first = dark[position]
            dark_value = dark_first + (dark[(position + 1) & (size - 1)] - dark_first) * fraction
            value += (dark_value - value) * weight
        if has_detune:
            detune_position = int(detune_phase)
            detune_fraction = detune_phase - detune_position
            other = bright[detune_position]
            value = 0.62 * value + 0.62 * (
                other + (bright[(detune_position + 1) & (size - 1)] - other) * detune_fraction
            )

        bus[start + index] += level * envelope * value

        advance = step
        if has_vibrato and index >= vibrato_delay:
            lfo += vibrato_step
            advance = step * (1.0 + vibrato_depth * math.sin(lfo))
        phase += advance
        if phase >= size:
            phase -= size
        if has_detune:
            detune_phase += detune_step * (advance / step)
            if detune_phase >= size:
                detune_phase -= size


def _noise(seed: int) -> tuple[int, float]:
    # Fixed 32-bit LCG: platform-independent and independent of Python's RNG.
    seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
    return seed, ((seed >> 8) / 8388607.5) - 1.0


@dataclass(frozen=True)
class DrumProfile:
    """A percussion voice: a pitched body sweep plus filtered noise.

    ``highpass`` counts first-difference stages applied to the noise (each adds
    roughly 6 dB/octave of tilt) and ``lowpass_hz`` tames the resulting top
    octave, which otherwise piles up just below a 22.05 kHz Nyquist.
    """

    length: float
    level: float
    tone_start: float
    tone_end: float
    tone_amp: float
    noise_amp: float
    decay: float
    highpass: int
    lowpass_hz: float


_DRUM_PROFILES: dict[str, DrumProfile] = {
    "kick": DrumProfile(0.26, 0.95, 128.0, 46.0, 1.00, 0.10, 16.0, 1, 0.0),
    "tom": DrumProfile(0.24, 0.58, 250.0, 132.0, 1.00, 0.08, 13.0, 0, 0.0),
    "snare": DrumProfile(0.16, 0.52, 232.0, 178.0, 0.50, 0.80, 22.0, 1, 6000.0),
    "stick": DrumProfile(0.05, 0.34, 900.0, 700.0, 0.50, 0.65, 70.0, 1, 6000.0),
    "hat": DrumProfile(0.055, 0.22, 0.0, 0.0, 0.00, 1.00, 68.0, 2, 5000.0),
    "openhat": DrumProfile(0.19, 0.19, 0.0, 0.0, 0.00, 1.00, 17.0, 2, 5000.0),
    "crash": DrumProfile(1.10, 0.24, 0.0, 0.0, 0.00, 1.00, 3.4, 1, 5000.0),
}


def _render_drum(
    bus: list[float],
    sample_rate: int,
    start: int,
    lane: str,
    amplitude: float,
    seed: int,
) -> int:
    profile = _DRUM_PROFILES[lane]
    length = int(sample_rate * profile.length)
    end = min(len(bus), start + length)
    if start >= len(bus):
        # Still advance the generator so later hits stay reproducible.
        for _ in range(length):
            seed, _value = _noise(seed)
        return seed
    level = amplitude * profile.level
    tone_start = profile.tone_start
    tone_end = profile.tone_end
    tone_amp = profile.tone_amp
    noise_amp = profile.noise_amp
    decay = profile.decay
    stages = profile.highpass
    lowpass = (
        1.0 - math.exp(-2.0 * math.pi * profile.lowpass_hz / sample_rate)
        if profile.lowpass_hz > 0.0
        else 1.0
    )
    tone_phase = 0.0
    previous = 0.0
    previous2 = 0.0
    smoothed = 0.0
    for index in range(length):
        seed, sample = _noise(seed)
        if start + index >= end:
            continue
        envelope = math.exp(-decay * index / sample_rate)
        value = 0.0
        if tone_amp > 0.0:
            sweep = math.exp(-decay * 0.6 * index / sample_rate)
            frequency = tone_end + (tone_start - tone_end) * sweep
            tone_phase += 2.0 * math.pi * frequency / sample_rate
            value += tone_amp * math.sin(tone_phase)
            if lane == "snare":
                value += 0.4 * tone_amp * math.sin(1.42 * tone_phase)
        filtered = sample
        if stages >= 1:
            filtered, previous = filtered - previous, sample
        if stages >= 2:
            filtered, previous2 = filtered - previous2, filtered
        smoothed += (filtered - smoothed) * lowpass
        value += noise_amp * smoothed * 0.7
        bus[start + index] += level * envelope * value
    return seed


def synthesize_pcm(
    track: MusicTrack,
    sample_rate: int,
    loop_fade_ms: int = 8,
    master_rms_dbfs: float = -18.5,
    master_knee: float = 0.5,
) -> array.array[int]:
    score = build_score(track)
    samples_per_step = sample_rate * 60 // (track.bpm * STEPS_PER_BEAT)
    total_samples = samples_per_step * score.total_steps
    dry = [0.0] * total_samples
    echo_bus = [0.0] * total_samples if track.echo is not None else dry

    for note in score.notes:
        _render_note(
            echo_bus if note.echo else dry,
            sample_rate,
            note.step * samples_per_step,
            note.steps * samples_per_step,
            note.midi,
            note.velocity,
            _VOICES[note.voice],
        )

    seed = track.seed & 0xFFFFFFFF
    for hit in score.drums:
        seed = _render_drum(
            dry, sample_rate, hit.step * samples_per_step, hit.lane, hit.velocity, seed
        )

    if track.echo is not None:
        delay = track.echo.steps * samples_per_step
        feedback = track.echo.gain
        for index in range(delay, total_samples):
            echo_bus[index] += feedback * echo_bus[index - delay]
        for index in range(total_samples):
            dry[index] += echo_bus[index]

    # Master stage. Loudness is set by RMS so every track lands in the same
    # window, then peaks fold into the per-track ceiling through a knee that is
    # exactly linear below the threshold: quiet material passes untouched and
    # transients cannot clip or dominate the normalization.
    energy = math.sqrt(sum(value * value for value in dry) / total_samples) or 1.0
    normalize = 10.0 ** (master_rms_dbfs / 20.0) / energy
    ceiling = track.gain
    threshold = master_knee * ceiling
    span = ceiling - threshold
    for index in range(total_samples):
        value = dry[index] * normalize
        magnitude = abs(value)
        if magnitude > threshold:
            folded = threshold + span * (1.0 - math.exp(-(magnitude - threshold) / span))
            value = folded if value >= 0.0 else -folded
        dry[index] = value

    # Guarantee a zero crossing at both file boundaries. LT loops the Sound
    # object directly, so this short master ramp prevents a seam click.
    seam = max(1, int(sample_rate * loop_fade_ms / 1000.0))
    for index in range(seam):
        gain = index / seam
        dry[index] *= gain
        dry[-1 - index] *= gain

    return array.array("h", (round(value * 32767.0) for value in dry))


def _write_wav(path: Path, samples: array.array[int], sample_rate: int) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(samples.tobytes())


def _ffmpeg_version(ffmpeg: str) -> str:
    result = subprocess.run(
        [ffmpeg, "-version"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()[0]


def _ogg_crc(data: bytes | bytearray) -> int:
    crc = 0
    for value in data:
        crc ^= value << 24
        for _ in range(8):
            crc = (
                ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
                if crc & 0x80000000
                else (crc << 1) & 0xFFFFFFFF
            )
    return crc


def _canonicalize_ogg(path: Path, serial_number: int) -> None:
    """Replace ffmpeg's random Ogg stream serial and repair page CRCs."""
    payload = bytearray(path.read_bytes())
    offset = 0
    while offset < len(payload):
        if payload[offset : offset + 4] != b"OggS" or offset + 27 > len(payload):
            raise ValueError(f"invalid Ogg page at byte {offset}: {path}")
        segment_count = payload[offset + 26]
        header_end = offset + 27 + segment_count
        if header_end > len(payload):
            raise ValueError(f"truncated Ogg segment table: {path}")
        body_size = sum(payload[offset + 27 : header_end])
        page_end = header_end + body_size
        if page_end > len(payload):
            raise ValueError(f"truncated Ogg page: {path}")
        payload[offset + 14 : offset + 18] = serial_number.to_bytes(4, "little")
        payload[offset + 22 : offset + 26] = b"\0\0\0\0"
        checksum = _ogg_crc(payload[offset:page_end])
        payload[offset + 22 : offset + 26] = checksum.to_bytes(4, "little")
        offset = page_end
    path.write_bytes(payload)


def _encode_ogg(
    ffmpeg: str, wav_path: Path, ogg_path: Path, serial_offset: int, quality: int
) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-fflags",
            "+bitexact",
            "-i",
            str(wav_path),
            "-map_metadata",
            "-1",
            "-c:a",
            "libvorbis",
            "-q:a",
            str(quality),
            "-flags:a",
            "+bitexact",
            "-serial_offset",
            str(serial_offset),
            str(ogg_path),
        ],
        check=True,
    )
    _canonicalize_ogg(ogg_path, serial_offset)


def lt_manifest_entries(design: MusicDesign) -> list[list[object]]:
    return [
        [track.nid, False, False, track.soundroom_index]
        for track in sorted(design.tracks, key=lambda item: item.soundroom_index)
    ]


def lt_music_resource_nids(design: MusicDesign) -> dict[str, str]:
    """Map private composition IDs to safe, user-facing LT resource IDs.

    Pinned LT displays the resource NID verbatim in the Sound Room and also
    uses it as the compiled Ogg filename. Keep the authored title readable
    while rejecting values that cannot be packaged portably as filenames.
    """
    display_nids = {track.nid: track.title for track in design.tracks}
    folded: set[str] = set()
    for private_nid, title in display_nids.items():
        if (
            not title
            or title != title.strip()
            or title in {".", ".."}
            or title.endswith(".")
            or _INVALID_LT_MUSIC_NID.search(title)
        ):
            raise ValueError(
                f"music title for {private_nid} is not a portable LT resource name: {title!r}"
            )
        normalized = title.casefold()
        if normalized in folded:
            raise ValueError("music titles must be unique for LT's sound room")
        folded.add(normalized)
    return display_nids


def render_music(design_path: Path, output_dir: Path, ffmpeg: str = "ffmpeg") -> dict[str, Any]:
    design = load_music_design(design_path)
    encoder = shutil.which(ffmpeg)
    if not encoder:
        raise RuntimeError("ffmpeg with libvorbis support is required to create LT-compatible Ogg")
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="winternight-music-") as temp:
        temp_dir = Path(temp)
        for index, track in enumerate(design.tracks, start=1):
            samples = synthesize_pcm(
                track,
                design.sample_rate,
                design.loop_fade_ms,
                design.master_rms_dbfs,
                design.master_knee,
            )
            wav_path = temp_dir / f"{track.nid}.wav"
            ogg_path = output_dir / track.filename
            _write_wav(wav_path, samples, design.sample_rate)
            _encode_ogg(
                encoder,
                wav_path,
                ogg_path,
                serial_offset=index,
                quality=design.encoder_quality,
            )
            rendered.append(
                {
                    "nid": track.nid,
                    "filename": track.filename,
                    "title": track.title,
                    "role": track.role,
                    "bars": track.bars,
                    "sections": [section.name for section in track.form],
                    "duration_samples": len(samples),
                    "duration_seconds": len(samples) / design.sample_rate,
                    "sample_rate": design.sample_rate,
                    "channels": design.channels,
                    "sha256": hashlib.sha256(ogg_path.read_bytes()).hexdigest(),
                    "soundroom_index": track.soundroom_index,
                }
            )
    (output_dir / "music.json").write_text(
        json.dumps(lt_manifest_entries(design), indent=4) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "design_path": design_path.as_posix(),
        "design_sha256": hashlib.sha256(design_path.read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "encoder": _ffmpeg_version(encoder),
        "codec": "Ogg Vorbis",
        "provenance": {
            "composition": "Deterministic synthesis; per-track authorship in design/music.yaml",
            "synthesis": "Deterministic procedural synthesis; no recorded or external samples",
            "generator": "src/winternight_gen/music_pipeline.py",
        },
        "tracks": rendered,
    }
    (output_dir / "music_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def verify_rendered_music(design: MusicDesign, asset_dir: Path) -> None:
    expected_manifest = lt_manifest_entries(design)
    actual_manifest = json.loads((asset_dir / "music.json").read_text(encoding="utf-8"))
    if actual_manifest != expected_manifest:
        raise ValueError("assets/music/music.json does not match design/music.yaml")
    provenance = json.loads((asset_dir / "music_manifest.json").read_text(encoding="utf-8"))
    expected_design_hash = hashlib.sha256(
        (asset_dir.parents[1] / "design" / "music.yaml").read_bytes()
    ).hexdigest()
    expected_generator_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if provenance.get("generator_version") != GENERATOR_VERSION:
        raise ValueError("music provenance generator version is stale")
    if provenance.get("design_sha256") != expected_design_hash:
        raise ValueError("music provenance design hash is stale")
    if provenance.get("generator_sha256") != expected_generator_hash:
        raise ValueError("music provenance generator hash is stale")
    by_nid = {entry["nid"]: entry for entry in provenance.get("tracks", [])}
    if set(by_nid) != {track.nid for track in design.tracks}:
        raise ValueError("music provenance track inventory does not match the design")
    for track in design.tracks:
        path = asset_dir / track.filename
        if not path.is_file():
            raise ValueError(f"missing rendered music: {path}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        expected_hash = by_nid.get(track.nid, {}).get("sha256")
        if actual_hash != expected_hash:
            raise ValueError(
                f"music hash mismatch for {track.nid}: {actual_hash} != {expected_hash}"
            )


def register_lt_music(resources: Any, design: MusicDesign, asset_dir: Path) -> None:
    """Register verified source audio with an LT ``Resources`` object."""
    from app.data.resources.sounds import SongPrefab

    verify_rendered_music(design, asset_dir)
    display_nids = lt_music_resource_nids(design)
    for track in sorted(design.tracks, key=lambda item: item.soundroom_index):
        # LT renders a music resource NID directly in its sound room and has no
        # separate display-name field. Adapt the private specification ID to
        # the authored title at the engine boundary.
        song = SongPrefab(display_nids[track.nid], str(asset_dir / track.filename))
        song.soundroom_idx = track.soundroom_index
        resources.music.append(song)


def apply_lt_music_assignments(database: Any, design: MusicDesign) -> None:
    """Set the title, special-slot, and level-phase NIDs on an LT database."""
    display_nids = lt_music_resource_nids(design)
    slots = {"music_main": design.title_track} | {
        _SPECIAL_MUSIC_CONSTANTS[slot]: nid for slot, nid in design.special_music.items()
    }
    for constant_nid, track_nid in slots.items():
        constant = database.constants.get(constant_nid)
        if constant is None:
            raise ValueError(f"pinned LT database has no {constant_nid} constant")
        constant.set_value(display_nids[track_nid])
    known_levels = set(database.levels.keys())
    unknown_levels = set(design.level_music) - known_levels
    if unknown_levels:
        raise ValueError(f"music assignments reference unknown levels: {sorted(unknown_levels)}")
    for level_nid, assignments in design.level_music.items():
        database.levels.get(level_nid).music.update(
            {phase: display_nids[nid] for phase, nid in assignments.items()}
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render the Winternight music set")
    parser.add_argument("design", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    arguments = parser.parse_args()
    render_music(arguments.design, arguments.output, arguments.ffmpeg)
