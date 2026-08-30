# Winternight SFX provenance

Every effect in this directory is an original, gameplay-invented sound created for this
repository. Authored scene effects retain narrative beat lineage and exact scene references.
Story-neutral system effects instead declare the pinned LT runtime IDs they serve: menus,
dialogue, phase changes, combat, progression, notifications, healing, and movement.

No recording, field recording, stock effect, sample library, MIDI file, franchise cue, or
model-generated audio was used. `src/winternight_gen/sfx_pipeline.py` constructs every PCM sample
from mathematical oscillators, envelopes, simple filters, and a documented deterministic
pseudo-random number generator. In particular, `growl_nearby` contains no human or animal voice.

The effects neither copy nor arrange sound design from Wheel of Time adaptations, Fire Emblem,
or LT-Maker's bundled example projects. They should not be represented as official franchise
audio.

FFmpeg converts the generated 16-bit mono PCM to the Ogg/Vorbis resource format required by the
pinned LT-Maker engine. The generator canonicalizes Ogg stream serials and page checksums so the
same source and pinned encoder produce byte-identical resources. `sfx_manifest.json` records the
design hash, generator hash, encoder build, durations, aliases, scene uses, and SHA-256 deliverable
hashes. `sfx.json` is the source effect catalog; compilation expands declared aliases into the
exact engine-facing LT `SFXCatalog` without copying LT's bundled example audio.

