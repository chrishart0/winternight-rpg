from __future__ import annotations

import array
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

GENERATOR_VERSION = "winternight-music-1"


@dataclass(frozen=True)
class MusicTrack:
    nid: str
    filename: str
    title: str
    role: str
    bpm: int
    bars: int
    tonic_midi: int
    chords: tuple[tuple[int, tuple[int, ...]], ...]
    motif: tuple[int | None, ...]
    melody_shifts: tuple[int, ...]
    bass_pattern: tuple[int | None, ...]
    lead_wave: str
    percussion: str
    seed: int
    gain: float
    soundroom_index: int


@dataclass(frozen=True)
class MusicDesign:
    schema_version: str
    sample_rate: int
    channels: int
    sample_width_bits: int
    codec: str
    tracks: tuple[MusicTrack, ...]
    title_track: str
    level_music: dict[str, dict[str, str]]


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def _require_sequence(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def load_music_design(path: Path) -> MusicDesign:
    raw = _require_mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "music design")
    if raw.get("schema_version") != "1.0":
        raise ValueError("music design schema_version must be '1.0'")
    if raw.get("generator_version") != GENERATOR_VERSION:
        raise ValueError(f"music design generator_version must be {GENERATOR_VERSION!r}")

    render = _require_mapping(raw.get("render"), "render")
    sample_rate = int(render.get("sample_rate", 0))
    channels = int(render.get("channels", 0))
    sample_width_bits = int(render.get("sample_width_bits", 0))
    codec = str(render.get("codec", ""))
    if sample_rate not in {22050, 44100}:
        raise ValueError("render.sample_rate must be 22050 or 44100")
    if channels != 1 or sample_width_bits != 16:
        raise ValueError("the deterministic synthesizer supports 16-bit mono PCM only")
    if codec != "vorbis":
        raise ValueError("LT music must use the configured Vorbis encoder")

    tracks: list[MusicTrack] = []
    seen_nids: set[str] = set()
    seen_indices: set[int] = set()
    for index, item in enumerate(_require_sequence(raw.get("tracks"), "tracks")):
        entry = _require_mapping(item, f"tracks[{index}]")
        nid = str(entry.get("nid", ""))
        filename = str(entry.get("filename", ""))
        if not nid or nid in seen_nids:
            raise ValueError(f"track NID must be non-empty and unique: {nid!r}")
        if filename != f"{nid}.ogg" or Path(filename).name != filename:
            raise ValueError(f"track {nid} filename must be exactly {nid}.ogg")
        seen_nids.add(nid)

        chords: list[tuple[int, tuple[int, ...]]] = []
        for chord in _require_sequence(entry.get("chords"), f"track {nid} chords"):
            values = _require_sequence(chord, f"track {nid} chord")
            if len(values) != 2:
                raise ValueError(f"track {nid} chord must be [root, intervals]")
            intervals = tuple(int(value) for value in _require_sequence(values[1], "intervals"))
            if not intervals:
                raise ValueError(f"track {nid} chord intervals cannot be empty")
            chords.append((int(values[0]), intervals))

        motif = tuple(
            None if value is None else int(value)
            for value in _require_sequence(entry.get("motif"), f"track {nid} motif")
        )
        bass_pattern = tuple(
            None if value is None else int(value)
            for value in _require_sequence(
                entry.get("bass_pattern"), f"track {nid} bass_pattern"
            )
        )
        melody_shifts = tuple(
            int(value)
            for value in _require_sequence(
                entry.get("melody_shifts"), f"track {nid} melody_shifts"
            )
        )
        bars = int(entry.get("bars", 0))
        if bars <= 0 or len(chords) != bars or len(melody_shifts) != bars:
            raise ValueError(f"track {nid} needs one chord and melody shift per bar")
        if len(motif) != 8 or len(bass_pattern) != 4:
            raise ValueError(f"track {nid} requires 8 motif steps and 4 bass steps")
        bpm = int(entry.get("bpm", 0))
        if bpm <= 0 or (sample_rate * 60) % bpm:
            raise ValueError(f"track {nid} bpm must produce an integral sample count per beat")
        soundroom_index = int(entry.get("soundroom_index", 0))
        if soundroom_index <= 0 or soundroom_index in seen_indices:
            raise ValueError("soundroom indices must be unique positive integers")
        seen_indices.add(soundroom_index)
        lead_wave = str(entry.get("lead_wave", ""))
        percussion = str(entry.get("percussion", ""))
        if lead_wave not in {"sine", "triangle", "reed"}:
            raise ValueError(f"unsupported lead_wave for {nid}: {lead_wave}")
        if percussion not in {"none", "soft", "march"}:
            raise ValueError(f"unsupported percussion profile for {nid}: {percussion}")

        tracks.append(
            MusicTrack(
                nid=nid,
                filename=filename,
                title=str(entry.get("title", nid)),
                role=str(entry.get("role", "")),
                bpm=bpm,
                bars=bars,
                tonic_midi=int(entry.get("tonic_midi", 0)),
                chords=tuple(chords),
                motif=motif,
                melody_shifts=melody_shifts,
                bass_pattern=bass_pattern,
                lead_wave=lead_wave,
                percussion=percussion,
                seed=int(entry.get("seed", 0)),
                gain=float(entry.get("gain", 0.0)),
                soundroom_index=soundroom_index,
            )
        )

    expected_indices = list(range(1, len(tracks) + 1))
    if sorted(seen_indices) != expected_indices:
        raise ValueError(f"soundroom indices must be consecutive: {expected_indices}")
    assignments = _require_mapping(raw.get("assignments"), "assignments")
    title_track = str(assignments.get("title", ""))
    levels_raw = _require_mapping(assignments.get("levels"), "assignments.levels")
    level_music = {
        str(level): {str(key): str(value) for key, value in _require_mapping(music, level).items()}
        for level, music in levels_raw.items()
    }
    referenced = {title_track} | {
        track for assignment in level_music.values() for track in assignment.values()
    }
    missing = referenced - seen_nids
    if missing:
        raise ValueError(f"music assignments reference unknown tracks: {sorted(missing)}")
    return MusicDesign(
        schema_version="1.0",
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bits=sample_width_bits,
        codec=codec,
        tracks=tuple(tracks),
        title_track=title_track,
        level_music=level_music,
    )


def _midi_frequency(note: int) -> float:
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def _waveform(kind: str, phase: float) -> float:
    cycle = phase / (2.0 * math.pi)
    if kind == "sine":
        return math.sin(phase)
    if kind == "triangle":
        return 4.0 * abs(cycle - math.floor(cycle + 0.5)) - 1.0
    # A deliberately restrained odd-harmonic timbre. It evokes a small reed
    # instrument without using any recorded sample.
    return math.sin(phase) + 0.28 * math.sin(3.0 * phase) + 0.08 * math.sin(5.0 * phase)


def _envelope(position: int, length: int, attack: int, release: int) -> float:
    if length <= 1:
        return 0.0
    attack_gain = min(1.0, position / max(1, attack))
    release_gain = min(1.0, (length - 1 - position) / max(1, release))
    return max(0.0, min(attack_gain, release_gain))


def _add_note(
    mix: list[float],
    sample_rate: int,
    start: int,
    length: int,
    midi_note: int,
    volume: float,
    waveform: str,
    attack_seconds: float,
    release_seconds: float,
) -> None:
    frequency = _midi_frequency(midi_note)
    attack = int(sample_rate * attack_seconds)
    release = int(sample_rate * release_seconds)
    end = min(len(mix), start + length)
    for target in range(start, end):
        position = target - start
        phase = 2.0 * math.pi * frequency * position / sample_rate
        mix[target] += volume * _envelope(position, length, attack, release) * _waveform(
            waveform, phase
        )


def _noise(seed: int) -> tuple[int, float]:
    # Fixed 32-bit LCG: platform-independent and independent of Python's RNG.
    seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
    return seed, ((seed >> 8) / 8388607.5) - 1.0


def _add_drum(
    mix: list[float],
    sample_rate: int,
    start: int,
    kind: str,
    volume: float,
    seed: int,
) -> int:
    length = int(sample_rate * (0.16 if kind == "kick" else 0.10))
    end = min(len(mix), start + length)
    for target in range(start, end):
        position = target - start
        time = position / sample_rate
        if kind == "kick":
            value = math.sin(2.0 * math.pi * (78.0 - 38.0 * time) * time)
            envelope = math.exp(-25.0 * time)
        else:
            seed, value = _noise(seed)
            envelope = math.exp(-42.0 * time)
        mix[target] += volume * envelope * value
    return seed


def synthesize_pcm(track: MusicTrack, sample_rate: int) -> array.array[int]:
    samples_per_beat = sample_rate * 60 // track.bpm
    samples_per_bar = samples_per_beat * 4
    total_samples = samples_per_bar * track.bars
    mix = [0.0] * total_samples

    for bar, (root, intervals) in enumerate(track.chords):
        bar_start = bar * samples_per_bar
        for interval in intervals:
            _add_note(
                mix,
                sample_rate,
                bar_start,
                samples_per_bar,
                track.tonic_midi - 12 + root + interval,
                0.075,
                "sine",
                0.12,
                0.18,
            )
        for beat, bass_interval in enumerate(track.bass_pattern):
            if bass_interval is None:
                continue
            _add_note(
                mix,
                sample_rate,
                bar_start + beat * samples_per_beat,
                int(samples_per_beat * 0.82),
                track.tonic_midi - 24 + root + bass_interval,
                0.16,
                "triangle",
                0.015,
                0.09,
            )
        for step, motif_interval in enumerate(track.motif):
            if motif_interval is None:
                continue
            _add_note(
                mix,
                sample_rate,
                bar_start + step * samples_per_beat // 2,
                int(samples_per_beat * 0.43),
                track.tonic_midi + 12 + motif_interval + track.melody_shifts[bar],
                0.11,
                track.lead_wave,
                0.018,
                0.07,
            )

    noise_seed = track.seed & 0xFFFFFFFF
    if track.percussion != "none":
        for bar in range(track.bars):
            bar_start = bar * samples_per_bar
            for beat in range(4):
                if beat in {0, 2}:
                    noise_seed = _add_drum(
                        mix,
                        sample_rate,
                        bar_start + beat * samples_per_beat,
                        "kick",
                        0.12 if track.percussion == "march" else 0.065,
                        noise_seed,
                    )
                if track.percussion == "march" and beat in {1, 3}:
                    noise_seed = _add_drum(
                        mix,
                        sample_rate,
                        bar_start + beat * samples_per_beat,
                        "noise",
                        0.075,
                        noise_seed,
                    )
                noise_seed = _add_drum(
                    mix,
                    sample_rate,
                    bar_start + beat * samples_per_beat + samples_per_beat // 2,
                    "noise",
                    0.025 if track.percussion == "soft" else 0.038,
                    noise_seed,
                )

    # Guarantee a zero crossing at both file boundaries. LT loops the Sound
    # object directly, so this short master ramp prevents a seam click.
    seam = max(1, int(sample_rate * 0.008))
    for index in range(seam):
        gain = index / seam
        mix[index] *= gain
        mix[-1 - index] *= gain

    peak = max(abs(value) for value in mix) or 1.0
    scale = min(track.gain / peak, 0.98) * 32767.0
    return array.array("h", (round(value * scale) for value in mix))


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
            crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if crc & 0x80000000 else (
                crc << 1
            ) & 0xFFFFFFFF
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


def _encode_ogg(ffmpeg: str, wav_path: Path, ogg_path: Path, serial_offset: int) -> None:
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
            "3",
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
            samples = synthesize_pcm(track, design.sample_rate)
            wav_path = temp_dir / f"{track.nid}.wav"
            ogg_path = output_dir / track.filename
            _write_wav(wav_path, samples, design.sample_rate)
            _encode_ogg(encoder, wav_path, ogg_path, serial_offset=index)
            rendered.append(
                {
                    "nid": track.nid,
                    "filename": track.filename,
                    "title": track.title,
                    "role": track.role,
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
        "schema_version": "1.0",
        "generator_version": GENERATOR_VERSION,
        "design_path": design_path.as_posix(),
        "design_sha256": hashlib.sha256(design_path.read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "encoder": _ffmpeg_version(encoder),
        "codec": "Ogg Vorbis",
        "provenance": {
            "composition": "Original, specification-driven composition for this repository",
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
    for track in sorted(design.tracks, key=lambda item: item.soundroom_index):
        song = SongPrefab(track.nid, str(asset_dir / track.filename))
        song.soundroom_idx = track.soundroom_index
        resources.music.append(song)


def apply_lt_music_assignments(database: Any, design: MusicDesign) -> None:
    """Set the title and level-phase NIDs on an assembled LT database."""
    title_music = database.constants.get("music_main")
    if title_music is None:
        raise ValueError("pinned LT database has no music_main constant")
    title_music.set_value(design.title_track)
    known_levels = set(database.levels.keys())
    unknown_levels = set(design.level_music) - known_levels
    if unknown_levels:
        raise ValueError(f"music assignments reference unknown levels: {sorted(unknown_levels)}")
    for level_nid, assignments in design.level_music.items():
        database.levels.get(level_nid).music.update(assignments)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render the original Winternight music set")
    parser.add_argument("design", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    arguments = parser.parse_args()
    render_music(arguments.design, arguments.output, arguments.ffmpeg)
