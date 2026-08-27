# Original SFX lane

This lane supplies four original deterministic effects:

| LT NID | Length | Authored use |
| --- | ---: | --- |
| `impact_heavy` | 1.15 s | farmhouse door impact in `sc_c1_farmhouse_calm` |
| `combat_distant` | 3.40 s | offscreen pursuit in `sc_c1_tam_wounded` |
| `growl_nearby` | 1.90 s | wounded Trolloc warning in `sc_c3_trolloc_appears` |
| `fire_house_threat` | 4.20 s | threatened-home fire in `sc_c2_home_burns` |

The four NIDs are every sound asset currently referenced by `design/scenes/**/*.yaml`.

`design/sfx.yaml` owns effect roles, source-beat lineage, scene-reference inventory, synthesis
profiles, duration, gain, and fixed seeds. `src/winternight_gen/sfx_pipeline.py` generates 16-bit
mono PCM using only mathematical oscillators, envelopes, filters, and deterministic noise. It
does not read any audio source. FFmpeg with `libvorbis` performs the delivery-format conversion
required by LT-Maker.

## Rebuild and verify

```bash
uv run --python 3.11 python -m winternight_gen.sfx_pipeline \
  design/sfx.yaml assets/sfx
uv run --python 3.11 pytest tests/test_sfx.py
```

The renderer canonicalizes Ogg serials and page checksums after encoding. Repeated renders with
the same design, generator, and encoder are byte-identical. `assets/sfx/sfx_manifest.json` binds
the design and generator hashes, encoder build, effect inventory, durations, scene references,
and output hashes.

For a human listening pass:

```bash
for effect in assets/sfx/*.ogg; do ffplay -autoexit "$effect"; done
```

Check the door effect against dialogue volume, whether the filtered clashes read as distant, that
the growl communicates proximity without resembling a sampled person or animal, and whether the
fire texture supports the threatened-home scene without masking dialogue.

## Verified pinned-engine contract

At LT commit `1820e585450f6f47605aebd686b2a3f13af181f0`:

- `app/data/resources/sounds.py` defines `.ogg` as the only `SFXCatalog` file type and serializes
  each manifest entry as `[nid, tag]` in `resources/sfx/sfx.json`.
- `app/data/resources/base_catalog.py` resolves NID `x` to `resources/sfx/x.ogg`.
- `app/engine/sound.py` loads the resource with `pygame.mixer.Sound`; `play_sfx` starts it once by
  default and returns the decoded `Sound` object.
- `app/events/event_functions.py` lowers the `sound` event command to
  `get_sound_thread().play_sfx(nid, volume=...)`.

The focused tests restore the exact LT catalog and start/stop every effect through the pinned
`DefaultSoundController` under SDL's dummy audio driver.

## Campaign integration

The campaign compiler treats SFX as an optional content-pack capability. When `design/sfx.yaml`
exists, it verifies the exact authored scene-reference inventory, provenance hashes, LT catalog,
and Ogg files before registering them. Sound actions compile to real LT `sound;<asset>` commands;
static analysis rejects missing SFX. The generated project receives `SFX_PROVENANCE.json`, and all
SFX inputs participate in the deterministic content hash and private package.

`make sfx` rebuilds the committed effects. Content packs without SFX remain valid; the Signal
Lantern portability fixture exercises that path. The test suite verifies source and compiled
catalog loading, deterministic rendering, direct decode/start/stop through the pinned sound
controller, authored-scene coverage, and provenance integrity.
