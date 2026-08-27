# Original music lane

This lane supplies three original procedural tracks for the Winternight vertical slice:

| LT NID | Role | Length | Use |
| --- | --- | ---: | --- |
| `wn_hearthlight` | quiet minor-mode theme | 32.0 s | title and Chapter 0 tutorial |
| `wn_black_wind` | urgent dry march | 24.0 s | farm escape and village defense |
| `wn_embers_on_snow` | sparse dark lament | 38.4 s | return to the farm and ending |

The composition source is `design/music.yaml`. It labels the material gameplay-invented, links
each track to source beat IDs, and records the originality constraints. The generator is
`src/winternight_gen/music_pipeline.py`; it uses only standard Python and PyYAML to synthesize
16-bit mono PCM. No recordings or external samples are involved. FFmpeg with `libvorbis` is the
only delivery-format tool because pinned LT-Maker accepts music as Ogg/Vorbis.

## Rebuild and verify

From the repository root:

```bash
uv run --python 3.11 python -m winternight_gen.music_pipeline \
  design/music.yaml assets/music
uv run --python 3.11 pytest tests/test_music.py
```

The renderer strips input metadata, enables FFmpeg's bit-exact flags, assigns a fixed serial to
each Ogg stream, and recomputes every Ogg page checksum. On the pinned Ubuntu toolchain this makes
repeated renders byte-identical. `assets/music/music_manifest.json` records the exact FFmpeg build
alongside the design and output hashes. Changing the encoder version is an intentional toolchain
change and requires regenerating and reviewing the hashes.

For a quick local listen:

```bash
ffplay -autoexit assets/music/wn_hearthlight.ogg
ffplay -autoexit assets/music/wn_black_wind.ogg
ffplay -autoexit assets/music/wn_embers_on_snow.ogg
```

Listen especially at the loop boundary. The synthesizer ramps the first and final 8 ms to zero so
the pinned engine's direct `pygame.mixer.Sound` replay does not click.

## Verified LT-Maker contract

Pinned commit `1820e585450f6f47605aebd686b2a3f13af181f0` defines the contract as follows:

- `app/data/resources/sounds.py`: `MusicCatalog` requires `.ogg`, saves `music.json`, and restores
  each entry as `[nid, has_intro, has_battle, soundroom_index]`.
- `app/data/resources/base_catalog.py`: restoring NID `x` binds the main file to `x.ogg` in the
  music resource directory.
- `app/engine/sound.py`: `SongObject` decodes that path with `pygame.mixer.Sound`; the controller
  loops it on a reserved mixer channel.
- `app/engine/title_screen.py`: the title state resolves the `music_main` database constant.
- `app/engine/phase.py`: map playback resolves `<team>_phase` from `LevelPrefab.music`.

The committed `assets/music/music.json` uses that exact manifest shape. This lane deliberately
does not provide `-intro.ogg` or `-battle.ogg` companions: all three entries set both flags false,
which is the simplest verified runtime path.

## Campaign integration

The campaign compiler treats music as an optional content-pack capability. When
`design/music.yaml` exists, it verifies the committed Ogg hashes, registers the LT music catalog,
assigns title and per-level phase tracks, copies `MUSIC_PROVENANCE.json`, and includes every music
input in the deterministic content hash. A content pack without a music design remains valid; the
Signal Lantern portability fixture exercises that path.

The current campaign has no event-level `music`, `change_music`, or `change_special_music`
override. Title playback therefore resolves from `music_main`, and each chapter's authored phase
track continues beneath its scenes until the normal level or title transition changes it.

`make music` rebuilds the committed audio, while `make compile` installs it into the generated
project. FFmpeg with Vorbis support is an authoring dependency only; playing and packaging the
committed tracks does not invoke FFmpeg. The full `make check` lane verifies byte determinism,
decode/start behavior, compiled resource registration, chapter assignments, real-input campaign
progression with music active, and the isolated packaged launcher.
