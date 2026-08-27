# Winternight music provenance

All three tracks in this directory are original, gameplay-invented compositions created for
this repository. The note patterns, chord progressions, arrangements, synthesis parameters,
and fixed noise seeds are recorded in `design/music.yaml`.

The audio contains no recordings, imported samples, MIDI, stock loops, or model-generated
audio. `src/winternight_gen/music_pipeline.py` synthesizes every sample with mathematical
oscillators and deterministic pseudo-random percussion, then invokes FFmpeg's Vorbis encoder.
It canonicalizes Ogg stream serials and checksums so repeated renders with the same inputs and
encoder produce byte-identical files.

No melody from a Wheel of Time adaptation, Fire Emblem, or LT-Maker's bundled example music was
used as a reference or source. The tracks should not be represented as official Wheel of Time
music or as music by any existing franchise composer.

`music_manifest.json` records the design hash, generator version, encoder build, duration, and
SHA-256 hash of each deliverable. `music.json` is the exact manifest shape consumed by the pinned
LT-Maker `MusicCatalog`; it does not claim authorship beyond this repository.

