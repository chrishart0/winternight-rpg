# Winternight music provenance

The six level, phase, and failure tracks in this directory are original, gameplay-invented
compositions created for this repository. The title track, `wn_wheel_of_time.ogg` ("Wheel of
Time"), is a GBA-style synthesizer arrangement of Blind Guardian's "Wheel of Time," released on
*At the Edge of Time* (Nuclear Blast, 2010). Its structure was audited against the reviewed,
publicly accessible Songsterr tab `s410588`, revision `927374`
(`https://www.songsterr.com/a/wsa/blind-guardian-wheel-of-time-tab-s410588`): 207 measures at a
marked 95 BPM, 22 labeled riffs, and eleven guitar, bass, drum, string, and violin parts. The
48-bar score re-voices the D#-E-C#-D# riff cell, rising build, and hook contour as an orchestral
prelude, riff entry, two verse passes, pre-chorus, hook, break, and final hook in
`design/music.yaml`, which records the track's `external_source` declaration.

The three enemy-phase and failure tracks added alongside the four map themes take their functional
taxonomy from published Fire Emblem Sound Room documentation, which lists separate player-phase,
enemy-phase, NPC-phase, and Game Over entries. Only that functional layout was referenced. No
melody, harmony, rhythm, or arrangement was transcribed from any Fire Emblem track.

The chord blocks, phrases, arpeggio and accompaniment patterns, drum kits, section forms,
orchestration roles, synthesis parameters, and fixed noise seeds for every track are recorded in
`design/music.yaml`.

The audio contains no recordings, imported samples, MIDI, stock loops, or model-generated
audio. `src/winternight_gen/music_pipeline.py` synthesizes every sample with band-limited
additive wavetables built from sine partials, envelope and vibrato math, deterministic
pseudo-random percussion, a feedback delay, and an RMS-plus-soft-knee master stage, then invokes
FFmpeg's Vorbis encoder. It canonicalizes Ogg stream serials and checksums so repeated renders
with the same inputs and encoder produce byte-identical files.

No melody from a Fire Emblem title or from LT-Maker's bundled example music was used as a
reference or source. The title track is an explicitly declared third-party derivative
arrangement and must retain its Blind Guardian attribution wherever the audio is described.
The repository's synthesis and transcription provenance does not grant distribution rights:
public distribution requires separate rights review and licensing. No other track should be
represented as music by any existing franchise composer.

`music_manifest.json` records the design hash, generator version, encoder build, duration, and
SHA-256 hash of each deliverable. `music.json` is the exact manifest shape consumed by the pinned
LT-Maker `MusicCatalog`; it does not claim authorship beyond this repository.
