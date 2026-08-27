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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

GENERATOR_VERSION = "winternight-sfx-1"
SUPPORTED_PROFILES = {
    "heavy_wood_impact",
    "distant_combat",
    "creature_growl",
    "house_fire",
}


@dataclass(frozen=True)
class SFXEffect:
    nid: str
    filename: str
    title: str
    role: str
    profile: str
    duration_ms: int
    seed: int
    gain: float
    tag: str
    source_beat_ids: tuple[str, ...]
    scene_references: tuple[str, ...]
    integration_status: str


@dataclass(frozen=True)
class SFXDesign:
    schema_version: str
    sample_rate: int
    channels: int
    sample_width_bits: int
    codec: str
    effects: tuple[SFXEffect, ...]
    source_path: Path
    source_sha256: str


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def _require_sequence(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def load_sfx_design(path: Path) -> SFXDesign:
    raw = _require_mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "SFX design")
    if raw.get("schema_version") != "1.0":
        raise ValueError("SFX design schema_version must be '1.0'")
    if raw.get("generator_version") != GENERATOR_VERSION:
        raise ValueError(f"SFX design generator_version must be {GENERATOR_VERSION!r}")

    render = _require_mapping(raw.get("render"), "render")
    sample_rate = int(render.get("sample_rate", 0))
    channels = int(render.get("channels", 0))
    sample_width_bits = int(render.get("sample_width_bits", 0))
    codec = str(render.get("codec", ""))
    if sample_rate not in {22050, 44100}:
        raise ValueError("render.sample_rate must be 22050 or 44100")
    if channels != 1 or sample_width_bits != 16:
        raise ValueError("the deterministic SFX synthesizer supports 16-bit mono PCM only")
    if codec != "vorbis":
        raise ValueError("pinned LT SFX must use the configured Vorbis encoder")

    effects: list[SFXEffect] = []
    seen: set[str] = set()
    for index, item in enumerate(_require_sequence(raw.get("effects"), "effects")):
        entry = _require_mapping(item, f"effects[{index}]")
        nid = str(entry.get("nid", ""))
        filename = str(entry.get("filename", ""))
        if not re.fullmatch(r"[a-z][a-z0-9_]*", nid) or nid in seen:
            raise ValueError(f"SFX NID must be safe, non-empty, and unique: {nid!r}")
        if filename != f"{nid}.ogg" or Path(filename).name != filename:
            raise ValueError(f"effect {nid} filename must be exactly {nid}.ogg")
        seen.add(nid)
        profile = str(entry.get("profile", ""))
        if profile not in SUPPORTED_PROFILES:
            raise ValueError(f"unsupported synthesis profile for {nid}: {profile}")
        duration_ms = int(entry.get("duration_ms", 0))
        if not 250 <= duration_ms <= 10_000:
            raise ValueError(f"effect {nid} duration_ms must be between 250 and 10000")
        gain = float(entry.get("gain", 0))
        if not 0 < gain <= 0.98:
            raise ValueError(f"effect {nid} gain must be in (0, 0.98]")
        source_beat_ids = tuple(
            str(value)
            for value in _require_sequence(
                entry.get("source_beat_ids"), f"effect {nid} source_beat_ids"
            )
        )
        scene_references = tuple(
            str(value)
            for value in _require_sequence(
                entry.get("scene_references"), f"effect {nid} scene_references"
            )
        )
        if not source_beat_ids:
            raise ValueError(f"effect {nid} must reference at least one source beat")
        integration_status = str(entry.get("integration_status", ""))
        if integration_status not in {"authored_scene", "available_optional"}:
            raise ValueError(f"invalid integration_status for {nid}: {integration_status}")
        if integration_status == "authored_scene" and not scene_references:
            raise ValueError(f"authored effect {nid} must name its scene references")
        if integration_status == "available_optional" and scene_references:
            raise ValueError(f"optional effect {nid} cannot claim authored scene references")
        effects.append(
            SFXEffect(
                nid=nid,
                filename=filename,
                title=str(entry.get("title", nid)),
                role=str(entry.get("role", "")),
                profile=profile,
                duration_ms=duration_ms,
                seed=int(entry.get("seed", 0)),
                gain=gain,
                tag=str(entry.get("tag", "Winternight")),
                source_beat_ids=source_beat_ids,
                scene_references=scene_references,
                integration_status=integration_status,
            )
        )
    if not effects:
        raise ValueError("SFX design must contain at least one effect")
    return SFXDesign(
        schema_version="1.0",
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bits=sample_width_bits,
        codec=codec,
        effects=tuple(effects),
        source_path=path,
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def authored_scene_sfx(root: Path) -> dict[str, set[str]]:
    references: dict[str, set[str]] = {}
    for path in sorted((root / "design" / "scenes").rglob("*.yaml")):
        raw = _require_mapping(yaml.safe_load(path.read_text(encoding="utf-8")), str(path))
        for scene in _require_sequence(raw.get("scenes"), f"{path} scenes"):
            scene_data = _require_mapping(scene, "scene")
            scene_id = str(scene_data.get("id", ""))
            for beat in _require_sequence(scene_data.get("beats"), f"scene {scene_id} beats"):
                beat_data = _require_mapping(beat, f"scene {scene_id} beat")
                if beat_data.get("type") != "action" or beat_data.get("action") != "sound":
                    continue
                asset = str(beat_data.get("asset", ""))
                if not asset:
                    raise ValueError(f"scene {scene_id} contains a sound action without an asset")
                references.setdefault(asset, set()).add(scene_id)
    return references


def verify_authored_sfx_references(design: SFXDesign, root: Path) -> None:
    authored = authored_scene_sfx(root)
    effects = {effect.nid: effect for effect in design.effects}
    missing = set(authored) - set(effects)
    if missing:
        raise ValueError(f"authored scenes reference unknown SFX: {sorted(missing)}")
    for effect in design.effects:
        expected = set(effect.scene_references)
        actual = authored.get(effect.nid, set())
        if expected != actual:
            raise ValueError(
                f"SFX scene references differ for {effect.nid}: "
                f"design={sorted(expected)}, authored={sorted(actual)}"
            )


def _noise(seed: int) -> tuple[int, float]:
    seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
    return seed, ((seed >> 8) / 8388607.5) - 1.0


def _fade_boundaries(mix: list[float], sample_rate: int, fade_ms: int = 4) -> None:
    length = min(len(mix) // 2, max(1, sample_rate * fade_ms // 1000))
    for index in range(length):
        gain = index / length
        mix[index] *= gain
        mix[-1 - index] *= gain


def _heavy_wood_impact(effect: SFXEffect, sample_rate: int, count: int) -> list[float]:
    mix = [0.0] * count
    seed = effect.seed & 0xFFFFFFFF
    low_noise = 0.0
    for index in range(count):
        time = index / sample_rate
        seed, raw_noise = _noise(seed)
        low_noise = 0.91 * low_noise + 0.09 * raw_noise
        thump_phase = 2.0 * math.pi * (77.0 * time - 13.0 * time * time)
        thump = math.sin(thump_phase) * math.exp(-5.8 * time)
        wood = (
            0.52 * math.sin(2.0 * math.pi * 146.0 * time)
            + 0.22 * math.sin(2.0 * math.pi * 221.0 * time)
        ) * math.exp(-8.4 * time)
        burst = low_noise * math.exp(-11.0 * time)
        # A short secondary flex gives the impression of a door settling in its frame.
        delayed = 0.0
        if time >= 0.085:
            local = time - 0.085
            delayed = math.sin(2.0 * math.pi * 103.0 * local) * math.exp(-17.0 * local)
        mix[index] = 0.72 * thump + 0.38 * wood + 0.3 * burst + 0.2 * delayed
    return mix


def _distant_combat(effect: SFXEffect, sample_rate: int, count: int) -> list[float]:
    mix = [0.0] * count
    seed = effect.seed & 0xFFFFFFFF
    events = (
        (0.12, 780.0, 0.52),
        (0.68, 1040.0, 0.42),
        (1.21, 630.0, 0.48),
        (1.92, 910.0, 0.38),
        (2.48, 720.0, 0.43),
        (2.91, 1160.0, 0.32),
    )
    low_pass = 0.0
    for index in range(count):
        time = index / sample_rate
        value = 0.0
        seed, raw_noise = _noise(seed)
        for onset, frequency, strength in events:
            local = time - onset
            if not 0 <= local <= 0.75:
                continue
            clang = (
                math.sin(2.0 * math.pi * frequency * local)
                + 0.37 * math.sin(2.0 * math.pi * frequency * 1.47 * local)
                + 0.18 * math.sin(2.0 * math.pi * frequency * 2.11 * local)
            )
            value += strength * clang * math.exp(-6.8 * local)
            value += 0.22 * strength * raw_noise * math.exp(-25.0 * local)
            value += (
                0.24
                * strength
                * math.sin(2.0 * math.pi * 82.0 * local)
                * math.exp(-10.0 * local)
            )
        # Distance is represented by a strong single-pole low-pass, not a sampled reverb.
        low_pass = 0.82 * low_pass + 0.18 * value
        mix[index] = low_pass
    return mix


def _creature_growl(effect: SFXEffect, sample_rate: int, count: int) -> list[float]:
    mix = [0.0] * count
    seed = effect.seed & 0xFFFFFFFF
    low_noise = 0.0
    duration = count / sample_rate
    for index in range(count):
        time = index / sample_rate
        seed, raw_noise = _noise(seed)
        low_noise = 0.94 * low_noise + 0.06 * raw_noise
        pitch_wobble = 1.0 + 0.065 * math.sin(2.0 * math.pi * 2.3 * time)
        throat = (
            math.sin(2.0 * math.pi * 51.0 * pitch_wobble * time)
            + 0.43 * math.sin(2.0 * math.pi * 76.0 * pitch_wobble * time)
            + 0.19 * math.sin(2.0 * math.pi * 109.0 * pitch_wobble * time)
        )
        pulse = 0.67 + 0.33 * math.sin(2.0 * math.pi * 7.1 * time)
        attack = min(1.0, time / 0.13)
        release = min(1.0, max(0.0, duration - time) / 0.28)
        mix[index] = attack * release * pulse * (0.63 * throat + 0.34 * low_noise)
    return mix


def _house_fire(effect: SFXEffect, sample_rate: int, count: int) -> list[float]:
    mix = [0.0] * count
    seed = effect.seed & 0xFFFFFFFF
    low_noise = 0.0
    high_noise = 0.0
    crackle = 0.0
    for index in range(count):
        time = index / sample_rate
        seed, raw_noise = _noise(seed)
        low_noise = 0.985 * low_noise + 0.015 * raw_noise
        high_noise = 0.65 * high_noise + 0.35 * raw_noise
        if seed & 0xFFFF < 29:
            crackle = 0.8 + 0.2 * ((seed >> 16) / 65535.0)
        crackle *= 0.985
        flame = low_noise * (0.65 + 0.2 * math.sin(2.0 * math.pi * 1.7 * time))
        mix[index] = 0.72 * flame + 0.36 * crackle * high_noise
    return mix


SYNTHESIZERS = {
    "heavy_wood_impact": _heavy_wood_impact,
    "distant_combat": _distant_combat,
    "creature_growl": _creature_growl,
    "house_fire": _house_fire,
}


def synthesize_sfx_pcm(effect: SFXEffect, sample_rate: int) -> array.array[int]:
    sample_count = sample_rate * effect.duration_ms // 1000
    mix = SYNTHESIZERS[effect.profile](effect, sample_rate, sample_count)
    _fade_boundaries(mix, sample_rate)
    peak = max(abs(value) for value in mix) or 1.0
    scale = effect.gain * 32767.0 / peak
    return array.array("h", (round(value * scale) for value in mix))


def _write_wav(path: Path, samples: array.array[int], sample_rate: int) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(samples.tobytes())


def _ogg_crc(data: bytes | bytearray) -> int:
    crc = 0
    for value in data:
        crc ^= value << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF
    return crc


def _canonicalize_ogg(path: Path, serial_number: int) -> None:
    payload = bytearray(path.read_bytes())
    offset = 0
    while offset < len(payload):
        if payload[offset : offset + 4] != b"OggS" or offset + 27 > len(payload):
            raise ValueError(f"invalid Ogg page at byte {offset}: {path}")
        segment_count = payload[offset + 26]
        header_end = offset + 27 + segment_count
        if header_end > len(payload):
            raise ValueError(f"truncated Ogg segment table: {path}")
        page_end = header_end + sum(payload[offset + 27 : header_end])
        if page_end > len(payload):
            raise ValueError(f"truncated Ogg page: {path}")
        payload[offset + 14 : offset + 18] = serial_number.to_bytes(4, "little")
        payload[offset + 22 : offset + 26] = b"\0\0\0\0"
        payload[offset + 22 : offset + 26] = _ogg_crc(payload[offset:page_end]).to_bytes(
            4, "little"
        )
        offset = page_end
    path.write_bytes(payload)


def _ffmpeg_version(ffmpeg: str) -> str:
    result = subprocess.run(
        [ffmpeg, "-version"], check=True, capture_output=True, text=True
    )
    return result.stdout.splitlines()[0]


def _encode_ogg(ffmpeg: str, wav_path: Path, ogg_path: Path, serial_number: int) -> None:
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
            "4",
            "-flags:a",
            "+bitexact",
            "-serial_offset",
            str(serial_number),
            str(ogg_path),
        ],
        check=True,
    )
    _canonicalize_ogg(ogg_path, serial_number)


def lt_sfx_manifest_entries(design: SFXDesign) -> list[list[str]]:
    return [[effect.nid, effect.tag] for effect in design.effects]


def render_sfx(design_path: Path, output_dir: Path, ffmpeg: str = "ffmpeg") -> dict[str, Any]:
    design = load_sfx_design(design_path)
    encoder = shutil.which(ffmpeg)
    if not encoder:
        raise RuntimeError("ffmpeg with libvorbis support is required to create LT-compatible SFX")
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="winternight-sfx-") as temporary:
        temp_dir = Path(temporary)
        for serial_number, effect in enumerate(design.effects, start=101):
            samples = synthesize_sfx_pcm(effect, design.sample_rate)
            wav_path = temp_dir / f"{effect.nid}.wav"
            ogg_path = output_dir / effect.filename
            _write_wav(wav_path, samples, design.sample_rate)
            _encode_ogg(encoder, wav_path, ogg_path, serial_number)
            rendered.append(
                {
                    "nid": effect.nid,
                    "filename": effect.filename,
                    "title": effect.title,
                    "role": effect.role,
                    "profile": effect.profile,
                    "duration_samples": len(samples),
                    "duration_seconds": len(samples) / design.sample_rate,
                    "sample_rate": design.sample_rate,
                    "channels": design.channels,
                    "sha256": hashlib.sha256(ogg_path.read_bytes()).hexdigest(),
                    "tag": effect.tag,
                    "integration_status": effect.integration_status,
                    "scene_references": list(effect.scene_references),
                }
            )
    (output_dir / "sfx.json").write_text(
        json.dumps(lt_sfx_manifest_entries(design), indent=4) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": "1.0",
        "generator_version": GENERATOR_VERSION,
        "design_path": design_path.as_posix(),
        "design_sha256": design.source_sha256,
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "encoder": _ffmpeg_version(encoder),
        "codec": "Ogg Vorbis",
        "provenance": {
            "creation": "Original deterministic procedural synthesis for this repository",
            "samples": "None; every PCM sample is generated mathematically",
            "generator": "src/winternight_gen/sfx_pipeline.py",
        },
        "effects": rendered,
    }
    (output_dir / "sfx_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def verify_rendered_sfx(design: SFXDesign, asset_dir: Path) -> None:
    actual_catalog = json.loads((asset_dir / "sfx.json").read_text(encoding="utf-8"))
    expected_catalog = lt_sfx_manifest_entries(design)
    if actual_catalog != expected_catalog:
        raise ValueError("assets/sfx/sfx.json does not match design/sfx.yaml")
    manifest = json.loads((asset_dir / "sfx_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("generator_version") != GENERATOR_VERSION:
        raise ValueError("SFX provenance generator version is stale")
    if manifest.get("design_sha256") != design.source_sha256:
        raise ValueError("SFX provenance design hash is stale")
    generator_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if manifest.get("generator_sha256") != generator_hash:
        raise ValueError("SFX provenance generator hash is stale")
    by_nid = {entry["nid"]: entry for entry in manifest.get("effects", [])}
    if set(by_nid) != {effect.nid for effect in design.effects}:
        raise ValueError("SFX provenance effect inventory does not match the design")
    for effect in design.effects:
        path = asset_dir / effect.filename
        if not path.is_file():
            raise ValueError(f"missing rendered SFX: {path}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        expected_hash = by_nid[effect.nid].get("sha256")
        if actual_hash != expected_hash:
            raise ValueError(
                f"SFX hash mismatch for {effect.nid}: {actual_hash} != {expected_hash}"
            )


def register_lt_sfx(resources: Any, design: SFXDesign, asset_dir: Path) -> None:
    from app.data.resources.sounds import SFXPrefab

    verify_rendered_sfx(design, asset_dir)
    existing = set(resources.sfx.keys())
    collisions = existing & {effect.nid for effect in design.effects}
    if collisions:
        raise ValueError(f"SFX NIDs already registered: {sorted(collisions)}")
    for effect in design.effects:
        resources.sfx.append(
            SFXPrefab(effect.nid, str(asset_dir / effect.filename), tag=effect.tag)
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render the original Winternight SFX set")
    parser.add_argument("design", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    arguments = parser.parse_args()
    render_sfx(arguments.design, arguments.output, arguments.ffmpeg)
