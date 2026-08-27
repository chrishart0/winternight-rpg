# Known issues

- This is a private adaptation experiment and must not be redistributed.
- The Linux package requires `uv` and network access on first launch to obtain
  Python 3.11 and the two pinned runtime wheels.
- Battle-animation sheets and bespoke map tiles remain out of scope. The slice
  has original procedurally synthesized music and authored sound effects.
- The pinned LT runtime emits benign iCCP warnings for some upstream PNG files.
- The packaged launcher hides LT's optional terrain-information panel because
  commit `1820e585450f6f47605aebd686b2a3f13af181f0` can initialize it before the
  restored cursor tile after Continue.
- Automated input runs validate progression and balance invariants, but the
  45–75 minute duration still requires timed human play sessions.
