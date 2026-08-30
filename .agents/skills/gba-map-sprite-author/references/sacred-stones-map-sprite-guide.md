# Sacred Stones map-sprite construction guide

This guide distills broad GBA tactical-RPG sprite techniques. It does not authorize reuse of official or community art.

## Source-backed constraints

- GBA graphics use 8×8 tiles and typically 16-entry palettes; palette index 0 is normally transparent. Source: [FEUniverse graphics guide](https://tutorial.feuniverse.us/gfx).
- A community GBA Fire Emblem art challenge specifies a 32×32 maximum map-sprite canvas and 16 colors total, including transparency. Source: [Pixel Joint challenge brief](https://pixeljoint.com/2023/03/06/6765/Pixel_Art_Challenge-_Fire_Emblem_Engage_GBA.htm).
- FE8 standing-map entries distinguish 16×16 average infantry, 16×32 cavalry, and 32×32 large units at the engine allocation level. Source: [FEUniverse map-sprite insertion guide](https://feuniverse.us/t/brief-guide-to-map-sprite-insertion-ea/9868).
- Official rips remain Nintendo/Intelligent Systems material. Study scale, clustered shading, limited ramps, and silhouettes; draw original forms rather than tracing, splicing, or recoloring. Source: [FEGBA sprite rights and workflow guide](https://fireemblemgba.com/resources/sprites/).

Repository rules are stricter where they differ: map-sprite outputs use no more than 14 visible colors, the pinned LT team ramp, 192×144 stand sheets, and 192×160 movement sheets.

### Measured reference characteristics

Direct pixel inspection of the reference-only Sacred Stones map-sprite sheet shows that the 32×32 frame is not a single universal body height. Trainee/Recruit frames can be only 17–19 pixels tall, while standard infantry, lords, and gear-heavy classes commonly use roughly 22–26 pixels of height; weapons and attack poses may extend farther. Treating the smallest trainee sample as the roster-wide target produces an older, lower-fidelity look.

Representative frames use 10–13 subject colors. They do not spend those colors on seams and facial rendering. The colors form broad functional ramps:

- a dark purple-gray contour/contact color can occupy roughly one third of subject pixels;
- saturated blue/cyan/white team and class colors occupy about 17–34% on light infantry and nearly half on heavily armored units;
- one warm skin or leather midtone breaks the cool mass;
- a bright yellow, red, or near-white accent may use only a few pixels but creates the high-color impression.

The lesson is fewer shapes with stronger hue separation—not fewer palette entries and not more brown shading.

## Visual grammar

### Proportion and footprint

Sacred Stones-era infantry map units are icons, not miniature portraits.

- Target roughly 22–26 pixels of body height for standard infantry inside the 32×32 frame; reserve 15–20-pixel bodies for deliberately slight or trainee classes.
- Let bows, lances, staves, shields, cloaks, horns, or attack poses exceed that body footprint when they are the class cue.
- Spend pixels on one head block, one torso/team-color block, stance, and gear silhouette. Do not render an eye, belt, strap, cuff, boot wrapping, tunic fold, and quiver detail simultaneously.
- Compress neck, torso, forearms, and lower legs into connected masses. Hands and feet may be one small cluster each.
- Preserve generous transparency around the unit. A figure that fills most of a 32×32 cell is too large even when its proportions are chibi.
- Use one-pixel negative gaps only where they separate the weapon or limbs; internal gaps and repeated edge notches create noise.

### Pixel clusters and outlines

- Place large connected clusters; avoid single-pixel confetti and repeated stair-step texture.
- Use a dark purple-gray for silhouette, contact shadows, and form separation. Sacred Stones sprites often have substantial dark structure, but it surrounds bright masses rather than describing costume details.
- Use one saturated midtone mass and one compact highlight per major readable plane.
- Omit facial features at map scale unless a single pixel is essential. Omit straps, seams, fingers, boot laces, and fabric texture.
- No antialiasing or dithering. Every output pixel must strengthen silhouette, hue mass, pose, gear, or transparency.

### Palette economy

Build a shared role-based palette before detail:

1. transparent/chroma slot;
2. one dark purple-gray contour/contact color;
3. one or two skin/warm colors;
4. two hair colors at most;
5. three or four saturated team/class colors using the pinned ramp, including a bright cyan or near-white highlight where allowed;
6. two shared gear colors for leather, wood, or metal;
7. one tiny high-chroma identity/class accent when useful.

Hue-shift ramps rather than adding neutral gray shades: cooler shadows, warmer highlights. Reuse the same dark and highlight across hair, leather, wood, and metal where the forms remain legible.

Palette share matters as much as palette count. For a blue player unit, the blue/cyan ramp should usually be one of the largest visible material masses. A brown-haired, brown-clothed archer with only a thin blue strip remains brown at native scale regardless of how many blue shades exist in the palette.

### Directional construction

Use down, left, right, up in that exact source order.

- Fix a shared foot baseline and measured head box before drawing side/back views.
- Preserve total height, head size, shoulder width, and gear length across all facings.
- Side views compress the far limb and reveal front/back overlap; they are not merely narrowed front views.
- The up view must show the back of hair, shoulders, clothing, and carried gear; do not leave front-facing facial marks.
- Keep asymmetric gear on the same physical side. Draw both side views when mirroring would reverse a bow, scabbard, shield, satchel, or damaged limb.

### Stand and walk animation

A convincing walk is pose change, not image translation.

- Neutral: balanced feet and relaxed arm/gear angle.
- Contact A: near foot forward, far arm forward, hips shift slightly.
- Passing: feet overlap, body rises about one pixel, gear trails.
- Contact B: opposite limbs forward, body settles.
- Preserve volume and baseline; use vertical motion sparingly.
- For a three-frame stand cycle, limit motion to a controlled breathing or cloth/gear accent. Do not jitter the whole silhouette.

## Review checklist

Review native 1× first, then nearest-neighbor 4× for defects.

- Identity is readable from class/gear silhouette, hair mass, and one accent—not facial or clothing detail.
- Silhouette is distinct from other roster units and the current terrain.
- Standard infantry body height is about 22–26 pixels within the logical 32×32 cell; trainee-sized units are a deliberate exception rather than the default.
- Every facing depicts the same character, scale, costume, and gear.
- Left/right physical handedness is coherent.
- Feet sit on the same logical ground line.
- Walk frames change limbs and overlaps rather than only position.
- No frame clips hair, weapon, bow, staff, pack, cloak, or horns.
- No magenta halo, partial alpha, antialiasing, dithering, or isolated noise.
- Final visible colors do not exceed 14 and team colors match the pinned LT ramp.
- Saturated team/class color forms a broad readable mass; brown and gray do not consume nearly the entire sprite.
- Stand and move sheets match 192×144 and 192×160 exactly.

## Diagnosis of the current Winternight source pipeline

The illustration-reduction paths are retained only as rejected placeholders: changing their target height or palette budget does not create authentic 2004 sprite anatomy. The viable calibration path authors each facing directly on a logical 32×32 grid, uses a recognizable non-shipping benchmark before roster work, and preserves the resulting pixel clusters rather than deriving them from a full-size turnaround. Genuine limb-authored walk cycles remain a separate animation requirement.
