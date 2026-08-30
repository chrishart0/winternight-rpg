# Known issues

- This is an unofficial public-source adaptation experiment. The generated game archive is for local technical evaluation and is not distributed as a release.
- The Linux package requires `uv` and network access on first launch to obtain
  Python 3.11 and the two pinned runtime wheels.
- Battle-animation sheets and bespoke map tiles remain out of scope. The slice
  has six original procedurally synthesized music tracks plus one GBA-style
  arrangement of Blind Guardian's "Wheel of Time" as the title theme, and
  authored sound effects.
- The pinned LT runtime emits benign iCCP warnings for some upstream PNG files.
- The packaged launcher hides LT's optional terrain-information panel because
  commit `1820e585450f6f47605aebd686b2a3f13af181f0` can initialize it before the
  restored cursor tile after Continue.
- The pinned LT Sound Room uses numbered track slots; the selected track's full
  title appears in the top banner, but unselected titles are not listed.
- LT's Objective screen shows the deterministic random seed as an unlabeled
  number in the upper-right corner.
- Automated input runs validate progression and balance invariants, but the
  45–75 minute duration still requires timed human play sessions.
