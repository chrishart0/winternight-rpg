# Music lane

This lane supplies seven tracks for the Winternight vertical slice: six original procedural
compositions and one GBA-style arrangement of the main theme from Blind Guardian's "Wheel of Time".

| # | Source ID / Sound Room title | Role | Form | Length | Use |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `wn_wheel_of_time` / Wheel of Time | GBA-style synthesizer arrangement of Blind Guardian's "Wheel of Time" | orchestral intro, riff entry, verse A/B, build, hook, break, final hook | 117.6 s | title screen (`music_main`) |
| 2 | `wn_hearthlight` / Hearthlight Before Snow | warm D-minor village theme | opening, verse, bridge, outro | 64.0 s | Chapter 0, both phases |
| 3 | `wn_black_wind` / Black Wind at the Palisade | Phrygian battle march | approach, drive, surge, breach, tag | 61.0 s | Chapters 1-2 player phase |
| 4 | `wn_shadow_advance` / Shadow on the Snow | diminished passacaglia | creep, press, close, hold | 53.3 s | Chapters 1-2 enemy phase |
| 5 | `wn_embers_on_snow` / Embers Under Snow | slow lament, no percussion | lament, drift, rest | 68.6 s | Chapter 3 player phase |
| 6 | `wn_last_light` / The Last Light | tritone dread, bell and tremolo | wait, stalk, strike | 54.9 s | Chapter 3 enemy phase |
| 7 | `wn_broken_wheel` / The Wheel Turns Away | failure cue, no percussion | fall, rest | 13.7 s | Game Over (`music_game_over`) |

Sound Room order pairs each map theme with its enemy-phase answer, then ends on the failure cue.

Provenance: the title track arranges Blind Guardian's "Wheel of Time" from *At the Edge of Time*
(Nuclear Blast, 2010) and is declared a `third_party_arrangement` in `design/music.yaml`; the
other six tracks are original, gameplay-invented. Its form was audited against reviewed Songsterr
tab `s410588`, revision `927374`; the arrangement remains a derivative work requiring separate
rights review and licensing before public distribution. See `assets/music/PROVENANCE.md`.

## Phase alternation

Pinned LT resolves map music as `<team>_phase` from `LevelPrefab.music` (`app/engine/phase.py`) and
crossfades over 400 ms when the next phase names a different track. Distinct player and enemy phase
themes are the GBA-era convention: *The Sacred Stones* ships six player-phase map themes and six
enemy-phase map themes, plus an NPC-phase theme, across its 69-track Sound Room.

Chapters 1-4 therefore alternate. Each enemy-phase theme shares its partner's key and tempo,
because LT's crossfade is a volume fade with no beat matching: A Phrygian at 126 BPM for
Black Wind / Shadow on the Snow, C-sharp at 70 BPM for Embers Under Snow / The Last Light. A test
asserts that pairing so a future retune cannot silently break the handoff. Combat chapters also
bind LT's native `player_battle` and `enemy_battle` level slots: Black Wind for player attacks and
Shadow on the Snow for enemy attacks.

Chapter 0 uses Hearthlight for player phase, the scripted raven enemy phase, and both battle slots,
so its brief attack tutorial never arms a needless fade. Chapter 5 has no combat phase.
`other_phase` and `enemy2_phase` remain unused: the campaign's peaceful villagers are phase-inert
engine objects, so an NPC-phase theme would never play.

The enemy-phase themes are written as passacaglias rather than as verse-and-bridge arcs. A ground
bass and a fixed chord cycle repeat unchanged while the upper voices thicken and thin, which reads
as sustained pressure instead of a journey — the right shape for a turn the player is waiting out.

## Sacred Stones situation audit

The comparison uses the matching FE8U decompilation, not soundtrack-title inference:

- FE8's [song catalog](https://github.com/FireEmblemUniverse/fireemblem8u/blob/master/include/constants/songs.h)
  separates player-map, enemy-map, attack, defense, boss, healing, promotion, preparation, shop,
  arena, victory, Game Over, records, and ending music.
- The [Prologue event script](https://github.com/FireEmblemUniverse/fireemblem8u/blob/master/src/events/prologue-eventscript.h)
  changes music for the opening raid, O'Neill's appearance, and the ending victory scene.
  [Chapter 1](https://github.com/FireEmblemUniverse/fireemblem8u/blob/master/src/events/ch1-eventscript.h)
  likewise starts Tension in its opening, changes to Shadow of the Enemy for an enemy event, and
  starts Victory in its ending. This is the direct reason every Winternight chapter intro now emits
  LT's supported `music` event command before its first visual or line.
- FE8 reuses a small system-SFX vocabulary rather than inventing a cue per screen:
  [trade/menu code](https://github.com/FireEmblemUniverse/fireemblem8u/blob/master/src/bmtrade.c)
  uses cursor, confirm, and cancel sounds, while
  [the minimap](https://github.com/FireEmblemUniverse/fireemblem8u/blob/master/src/minimap.c)
  has distinct open and close cues. Winternight now supplies original procedural resources for the
  equivalent LT runtime IDs: title/start, cursor, confirm, cancel, invalid action, save, page/info,
  minimap, dialogue, phase change, combat hit/miss/block/death, experience, level-up, item,
  healing, movement, and stage clear.

The slice has no shops, arena, records screen, world map, or playable promotion flow, so those FE8
surfaces are not imitated. LT's normal promotion and class-change music constants are nevertheless
bound to a valid authored track; they cannot become silent if a later validated mission enables
those already-supported mechanics. No FE8 or LT sample audio is copied.

## Score format

`design/music.yaml` is a small tracker-style score, version `2.0`. Each track declares:

- `harmony`: named chord blocks. A chord is `[root, intervals, beats]`, with `root` in semitones
  from `tonic_midi` and `intervals` starting at `0`. A block's total beats must equal the length of
  every section that uses it, so a wrong bar count fails validation instead of drifting.
- `phrases`: named monophonic lines on a sixteenth-note grid. An event is
  `[value, steps]` or `[value, steps, velocity]`, and `null` is a rest. `lead` and `counter` values
  are semitones from the tonic; `bass` values are semitones from the current chord root, so one
  bar of bass follows a whole progression.
- `arps`: same event shape, but the value is a chord-tone index. Index `n` past the end of the
  chord wraps up an octave, which is what makes a single arpeggio or stab pattern work over every
  chord in a section.
- `comps`: 16-steps-per-bar accompaniment rhythms. `.` is a rest, `o` a ghost, `x` a hit, and `X`
  an accent.
- `kits`: per-lane drum patterns over the same grid for `kick`, `snare`, `hat`, `openhat`, `tom`,
  `crash`, and `stick`. A pattern may span several bars, so a four-bar `crash` lane lands a cymbal
  only on the downbeat of each phrase. An optional `fill` map replaces the final bar of any section
  that sets `drums.fill`.
- `form`: the ordered sections. Each names its harmony block, its bar count, a `dynamic` scalar,
  and up to five instrument roles (`pad`, `bass`, `lead`, `counter`, `arp`) plus `drums`. Any
  pattern shorter than the section tiles across it, and a pattern that does not divide the section
  evenly is rejected.
- `echo`: a feedback delay in sixteenths applied to every part that sets `echo: true`. This is the
  GBA-style delay channel; the lead and the arpeggios usually ride it.

Pad `voicing` selects `chord` (as authored), `power` (root, fifth, octave), or `wide` (the chord
plus an octave above the root).

`assignments` binds tracks to engine slots: `title` sets `music_main`,
`levels.<chapter>.<team>_phase` and `levels.<chapter>.<team>_battle` set native
`LevelPrefab.music` keys, and `special` sets `music_game_over`, `music_promotion`, or
`music_class_change`. Keys are checked against the exact lookups in the pinned engine, so a typo
like `enemy_phase_music` fails the build instead of producing silence.

## Synthesis

`src/winternight_gen/music_pipeline.py` renders the score with the standard library and PyYAML
only. No recordings, samples, MIDI, or model-generated audio are involved.

Timbres are band-limited additive wavetables: each voice sums sine partials, drops every partial
above `0.45 * sample_rate`, and normalizes the table. That matters at 22.05 kHz, where a naive
pulse or sawtooth lead aliases into audible grit. Voices carry an ADSR envelope plus optional
vibrato, two-oscillator detune, and a timed crossfade to a darker partial set, which is how the
strings, brass, and reed lose brightness as a note settles. Percussion is a pitched body sweep plus
noise shaped by first-difference high-pass stages and a one-pole low-pass.

Every part renders into one of two buses. The echo bus is fed back at the declared delay, then
summed into the dry bus. The master stage then sets loudness by RMS (`render.master_rms_dbfs`) and
folds peaks into the per-track ceiling (`gain`) through a knee that is exactly linear below
`master_knee * gain`, so quiet material passes untouched, transients cannot clip, and one loud
cymbal cannot drag the whole track down during normalization.

FFmpeg with `libvorbis` is the only delivery-format tool, because pinned LT-Maker accepts music as
Ogg/Vorbis.

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
ffplay -autoexit assets/music/wn_wheel_of_time.ogg
ffplay -autoexit assets/music/wn_hearthlight.ogg
ffplay -autoexit assets/music/wn_black_wind.ogg
ffplay -autoexit assets/music/wn_embers_on_snow.ogg
```

Listen especially at the loop boundary. The synthesizer ramps the first and final 20 ms to zero so
the pinned engine's direct `pygame.mixer.Sound` replay does not click. That window is deliberately
wider than the audible seam: Vorbis ringing at a file boundary scales with the surrounding energy,
and 8 ms was not enough once the master stage raised the tracks by roughly 5 dB.

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
- `app/engine/combat/animation_combat.py`: battle playback resolves `<team>_battle`.
- `app/events/event_commands.py`: the `music` command is the supported event-level fade-in path.

The committed `assets/music/music.json` uses the exact LT manifest shape. This lane deliberately
does not provide `-intro.ogg` or `-battle.ogg` companions: level and event assignments select the
same verified resources without using LT's optional companion-file convention.

LT has no separate display-name field for music: the Sound Room renders the resource NID itself.
The source manifest therefore retains stable private composition IDs, while the compiler adapts
them to authored titles at the LT boundary. A compiled project contains title-based catalog NIDs
and files such as `resources/music/Hearthlight Before Snow.ogg`. Titles are required to be unique
case-insensitively and safe as portable filenames. Sound Room indices 1–7 present the tracks in
the table order above.

## Campaign integration

The campaign compiler treats music as an optional content-pack capability. When
`design/music.yaml` exists, it verifies the committed Ogg hashes, registers the LT music catalog,
assigns title and per-level phase tracks, copies `MUSIC_PROVENANCE.json`, and includes every music
input in the deterministic content hash. A content pack without a music design remains valid; the
Signal Lantern portability fixture exercises that path.

Every compiled chapter-intro event begins with LT's native `music` command using that chapter's
player-phase track. This closes the title-to-Chapter-0 silence without a custom state or engine
patch; in-map scenes keep the active phase track unless normal phase, battle, level, or title
transitions change it. Dialogue uses LT's normal `Talk_Boop` path, while narration remains silent.
Title playback resolves from `music_main`, Game Over from `music_game_over`, combat from native
level battle keys, and promotion/class change from the corresponding constants. Perceived fit,
loudness, and transition quality remain listening checks rather than claims made by decode-only
automation.

Automated decoding checks the delivered Ogg files, not only the pre-encode PCM. All seven have at
least 5 dBFS peak headroom, RMS loudness within a 2 dB band, and near-zero endpoints with a small
loop-seam discontinuity. The pinned runtime probe compares each decoded length against the authored
bar count instead of a fixed floor, so it holds for the 13.7 s failure cue as well as the map loops.
Separate checks assert that every looping theme is a multi-section arrangement with distinct
orchestration per section, that the failure cue stays inside GBA-era sting length with no
percussion, that each chapter with enemies pairs distinct phase themes in a shared key and tempo,
that no scored event falls outside its declared form, and that a mis-sized harmony block, drum
pattern, phrase, or voice name fails validation rather than rendering a silently wrong bar. These
bounds catch clipping, large loudness jumps, truncation, obvious boundary clicks, and score
arithmetic errors; headphones are still required to judge a musically convincing loop and
transition.

`make music` rebuilds the committed audio, while `make compile` installs it into the generated
project. FFmpeg with Vorbis support is an authoring dependency only; playing and packaging the
committed tracks does not invoke FFmpeg. The full `make check` lane verifies byte determinism,
decode/start behavior, compiled resource registration, chapter assignments, real-input campaign
progression with music active, and the isolated packaged launcher.
