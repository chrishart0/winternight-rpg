from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from .models import AssetManifestEntry, CampaignBundle

# Pinned LT 2026.02.17a treats this exact RGB value as transparent for
# portraits and map sprites. Alpha alone is not sufficient for these resources.
COLORKEY = (128, 160, 128, 255)
BLUE = (56, 80, 224, 255)
RED = (224, 16, 16, 255)


@dataclass(frozen=True)
class AssetPaths:
    background: Path
    portraits: dict[str, Path]
    tileset: Path
    map_sprite_stand: Path
    map_sprite_move: Path
    font_image: Path
    font_index: Path


@dataclass(frozen=True)
class CampaignAssetPaths:
    backgrounds: dict[str, Path]
    portraits: dict[str, Path]
    tileset: Path
    terrain_tiles: dict[str, tuple[int, int]]
    map_sprites: dict[str, tuple[Path, Path]]
    ui_sprites: dict[str, Path]
    font_image: Path
    font_index: Path


def _save(image: Image.Image, path: Path) -> None:
    image.save(path, format="PNG", optimize=False, compress_level=9)


def _background(path: Path) -> None:
    image = Image.new("RGBA", (240, 160), (29, 38, 51, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 105, 239, 159), fill=(53, 62, 67, 255))
    for x in range(0, 240, 24):
        draw.line((x, 105, x + 20, 159), fill=(70, 78, 80, 255), width=1)
    draw.rectangle((45, 25, 195, 112), outline=(190, 156, 80, 255), width=3)
    draw.rectangle((54, 34, 186, 103), fill=(24, 31, 42, 255))
    draw.polygon(((120, 40), (146, 92), (94, 92)), fill=(83, 111, 127, 255))
    draw.text(
        (73, 126),
        "ENGINE INTEGRATION",
        fill=(224, 224, 210, 255),
        font=ImageFont.load_default(),
    )
    _save(image, path)


def _portrait(
    path: Path, body: tuple[int, int, int, int], accent: tuple[int, int, int, int]
) -> None:
    image = Image.new("RGBA", (160, 112), COLORKEY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 18, 87, 103), fill=body, outline=(24, 24, 32, 255), width=2)
    draw.ellipse((24, 12, 72, 62), fill=(207, 171, 132, 255), outline=(40, 32, 32, 255), width=2)
    draw.rectangle((29, 30, 37, 34), fill=(30, 35, 45, 255))
    draw.rectangle((58, 30, 66, 34), fill=(30, 35, 45, 255))
    draw.line((40, 49, 56, 49), fill=(85, 45, 45, 255), width=2)
    draw.polygon(((17, 24), (31, 6), (70, 8), (81, 28)), fill=accent)
    draw.rectangle((10, 73, 85, 103), fill=accent, outline=(24, 24, 32, 255), width=2)
    # Current pinned LT layout: minimug at 128,80; face/eye/mouth frames at right/bottom.
    draw.rectangle((128, 80, 159, 111), fill=body)
    draw.ellipse((134, 83, 153, 105), fill=(207, 171, 132, 255), outline=(40, 32, 32, 255))
    for y in (32, 48):
        draw.rectangle((128, y, 159, y + 15), fill=(207, 171, 132, 255))
        draw.line((136, y + 8, 151, y + 8), fill=(30, 35, 45, 255), width=2)
    for x in (64, 96):
        for y in (80, 96):
            draw.rectangle((x, y, x + 31, y + 15), fill=(207, 171, 132, 255))
            draw.line((x + 8, y + 8, x + 23, y + 8), fill=(85, 45, 45, 255), width=2)
    _save(image, path)


def _tileset(path: Path) -> None:
    image = Image.new("RGBA", (32, 16), (93, 113, 104, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 15, 15), fill=(91, 112, 95, 255))
    draw.line((0, 8, 15, 8), fill=(75, 94, 80, 255))
    draw.line((8, 0, 8, 15), fill=(75, 94, 80, 255))
    draw.rectangle((16, 0, 31, 15), fill=(109, 92, 72, 255))
    _save(image, path)


def _map_sprites(stand_path: Path, move_path: Path) -> None:
    stand = Image.new("RGBA", (192, 144), COLORKEY)
    move = Image.new("RGBA", (192, 160), COLORKEY)
    for image, cell_w, cell_h, cols, rows in ((stand, 64, 48, 3, 3), (move, 48, 40, 4, 4)):
        draw = ImageDraw.Draw(image)
        for row in range(rows):
            for col in range(cols):
                ox, oy = col * cell_w, row * cell_h
                color = BLUE if row % 2 == 0 else (96, 104, 120, 255)
                draw.ellipse(
                    (ox + cell_w // 2 - 7, oy + 7, ox + cell_w // 2 + 7, oy + 21),
                    fill=(220, 190, 150, 255),
                )
                draw.polygon(
                    (
                        (ox + cell_w // 2, oy + 17),
                        (ox + 14, oy + cell_h - 5),
                        (ox + cell_w - 14, oy + cell_h - 5),
                    ),
                    fill=color,
                    outline=(32, 32, 40, 255),
                )
    _save(stand, stand_path)
    _save(move, move_path)


def _font(image_path: Path, index_path: Path) -> None:
    chars = [chr(code) for code in range(32, 127)]
    cell_w, cell_h, cols = 8, 16, 16
    rows = (len(chars) + cols - 1) // cols
    image = Image.new("RGBA", (cols * cell_w, rows * cell_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = [f"width {cell_w}", f"height {cell_h}", "space_offset 0"]
    for index, char in enumerate(chars):
        col, row = index % cols, index // cols
        key = "space" if char == " " else char
        width = 4 if char == " " else min(cell_w, max(1, int(draw.textlength(char, font=font))))
        if char != " ":
            draw.text((col * cell_w, row * cell_h + 2), char, font=font, fill=(248, 248, 248, 255))
        lines.append(f"{key} {col} {row} {width}")
    _save(image, image_path)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_assets(directory: Path, portrait_ids: list[str]) -> AssetPaths:
    directory.mkdir(parents=True, exist_ok=True)
    background = directory / "background.png"
    tileset = directory / "tileset.png"
    stand = directory / "map-stand.png"
    move = directory / "map-move.png"
    font_image = directory / "font.png"
    font_index = directory / "font.idx"
    _background(background)
    _tileset(tileset)
    _map_sprites(stand, move)
    _font(font_image, font_index)
    portraits: dict[str, Path] = {}
    palette = [((65, 92, 125, 255), (92, 130, 175, 255)), ((104, 74, 64, 255), RED)]
    for index, portrait_id in enumerate(portrait_ids):
        portrait = directory / f"portrait-{index}.png"
        _portrait(portrait, *palette[index % len(palette)])
        portraits[portrait_id] = portrait
    return AssetPaths(background, portraits, tileset, stand, move, font_image, font_index)


def _identity_colors(identity: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    body = tuple(56 + value % 112 for value in digest[:3]) + (255,)
    accent = tuple(72 + value % 144 for value in digest[3:6]) + (255,)
    return body, accent


def _campaign_background(path: Path, asset_id: str) -> None:
    digest = hashlib.sha256(asset_id.encode("utf-8")).digest()
    sky = tuple(24 + value % 88 for value in digest[:3]) + (255,)
    ground = tuple(35 + value % 76 for value in digest[3:6]) + (255,)
    accent = tuple(90 + value % 120 for value in digest[6:9]) + (255,)
    image = Image.new("RGBA", (240, 160), sky)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 92, 239, 159), fill=ground)
    draw.polygon(
        ((0, 110), (55, 68), (105, 106), (165, 55), (239, 105), (239, 159), (0, 159)),
        fill=accent,
    )
    if asset_id != "title_background":
        draw.rectangle((6, 132, 233, 154), fill=(14, 18, 24, 210))
        label = asset_id.replace("_", " ").upper()[:32]
        draw.text((11, 138), label, fill=(244, 238, 211, 255), font=ImageFont.load_default())
    _save(image, path)


def _source_image(asset: AssetManifestEntry, root: Path) -> Image.Image:
    if not asset.source_path:
        raise ValueError(f"asset {asset.id} has no source_path")
    repository = root.resolve()
    source = (root / asset.source_path).resolve()
    if not source.is_relative_to(repository):
        raise ValueError(f"asset {asset.id} source escapes repository: {source}")
    if not source.is_file():
        raise ValueError(f"asset {asset.id} source does not exist: {source}")
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if asset.source_hash and actual_hash != asset.source_hash:
        raise ValueError(
            f"asset {asset.id} source hash mismatch: {actual_hash} != {asset.source_hash}"
        )
    with Image.open(source) as image:
        return image.convert("RGBA")


def _quantize_rgba(image: Image.Image, colors: int = 64) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    reduced = (
        rgba.convert("RGB")
        .quantize(
            colors=colors,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )
        .convert("RGBA")
    )
    reduced.putalpha(alpha)
    return reduced


def _finalize_portrait_palette(sheet: Image.Image) -> Image.Image:
    original = sheet.convert("RGBA")
    key_mask = Image.new("L", original.size, 0)
    source_pixels = original.load()
    mask_pixels = key_mask.load()
    for y in range(original.height):
        for x in range(original.width):
            if source_pixels[x, y] == COLORKEY:
                mask_pixels[x, y] = 255
    reduced = (
        original.convert("RGB")
        .quantize(
            colors=63,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )
        .convert("RGBA")
    )
    reduced.paste(COLORKEY, (0, 0, *original.size), key_mask)
    return reduced


def _ai_background(path: Path, asset: AssetManifestEntry, root: Path) -> None:
    source = _source_image(asset, root).convert("RGB")
    # Reduce to a 2x working canvas before palette conversion. The final nearest-
    # neighbor step preserves deliberately chunky pixels without aliasing the
    # source's non-integer aspect crop directly into the engine resolution.
    image = ImageOps.fit(
        source,
        (480, 320),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.44),
    )
    if asset.variant == "title":
        image = Image.blend(image, Image.new("RGB", image.size, (7, 12, 24)), 0.32)
    elif asset.variant == "ending_card":
        overlay = Image.new("RGBA", image.size, (8, 14, 24, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle((0, 212, 479, 319), fill=(8, 14, 24, 76))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    image = image.quantize(
        colors=64,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    ).convert("RGBA")
    image = image.resize((240, 160), Image.Resampling.NEAREST)
    _save(image, path)


def _grid_cell(image: Image.Image, asset: AssetManifestEntry) -> Image.Image:
    if not asset.source_grid or not asset.source_cell:
        return image.copy()
    columns, rows = asset.source_grid
    column, row = asset.source_cell
    left = round(image.width * column / columns)
    top = round(image.height * row / rows)
    right = round(image.width * (column + 1) / columns)
    bottom = round(image.height * (row + 1) / rows)
    cell_width, cell_height = right - left, bottom - top
    inset_x = max(4, round(cell_width * 0.04))
    inset_y = max(4, round(cell_height * 0.04))
    return image.crop((left + inset_x, top + inset_y, right - inset_x, bottom - inset_y))


def _remove_chroma_backdrop(image: Image.Image) -> Image.Image:
    # The approved portrait sources use a deliberately saturated magenta key.
    # Remove that chroma directly instead of sampling cell corners: corner
    # sampling can mistake dark hair or the black grid gutter for background
    # and then flood-fill holes through the subject.
    rgba = image.convert("RGBA")
    if max(rgba.size) > 420:
        rgba.thumbnail((420, 420), Image.Resampling.LANCZOS)
    output = rgba.copy()
    source_pixels = rgba.load()
    output_pixels = output.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, _ = source_pixels[x, y]
            if red >= 110 and blue >= 90 and min(red, blue) - green >= 35:
                output_pixels[x, y] = (0, 0, 0, 0)
    return output


def _ai_portrait(path: Path, asset: AssetManifestEntry, root: Path) -> None:
    source = _grid_cell(_source_image(asset, root), asset)
    subject = _remove_chroma_backdrop(source)
    if asset.variant == "wounded" and asset.subject_id == "wounded_trolloc":
        subject = ImageEnhance.Brightness(subject).enhance(0.78)
        tint = Image.new("RGBA", subject.size, (84, 20, 20, 0))
        tint.putalpha(subject.getchannel("A").point(lambda value: 48 if value else 0))
        subject = Image.alpha_composite(subject, tint)

    full_main = ImageOps.fit(
        subject,
        (192, 160),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.34),
    ).resize((96, 80), Image.Resampling.NEAREST)
    full_main = _quantize_rgba(full_main)
    sheet = Image.new("RGBA", (160, 112), COLORKEY)
    sheet.alpha_composite(full_main, (0, 0))

    minimug = ImageOps.fit(
        full_main, (32, 32), method=Image.Resampling.LANCZOS, centering=(0.5, 0.28)
    )
    sheet.alpha_composite(minimug, (128, 80))

    eye = full_main.crop((24, 21, 72, 37)).resize((32, 16), Image.Resampling.LANCZOS)
    eye = _quantize_rgba(eye)
    sheet.alpha_composite(eye, (128, 32))
    closed_eye = eye.copy()
    closed_draw = ImageDraw.Draw(closed_eye)
    closed_draw.line((6, 9, 25, 9), fill=(35, 28, 27, 255), width=2)
    sheet.alpha_composite(closed_eye, (128, 48))

    mouth = full_main.crop((32, 48, 68, 64)).resize((32, 16), Image.Resampling.LANCZOS)
    mouth = _quantize_rgba(mouth)
    for frame_index, (x, y) in enumerate(((64, 80), (96, 80), (64, 96), (96, 96))):
        frame = mouth.copy()
        if frame_index:
            frame_draw = ImageDraw.Draw(frame)
            half_width = 5 + frame_index * 2
            frame_draw.line(
                (16 - half_width, 9, 16 + half_width, 9),
                fill=(77, 37, 34, 255),
                width=1 + (frame_index == 3),
            )
        sheet.alpha_composite(frame, (x, y))
    _save(_finalize_portrait_palette(sheet), path)


def _verify_processed_hash(path: Path, asset: AssetManifestEntry) -> None:
    if not asset.output_hash:
        return
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != asset.output_hash:
        raise ValueError(
            f"asset {asset.id} output hash mismatch: {actual_hash} != {asset.output_hash}"
        )


def _campaign_ui_sprite(path: Path, asset_id: str) -> None:
    if asset_id == "title_logo":
        source = Image.new("RGBA", (110, 26), (0, 0, 0, 0))
        draw = ImageDraw.Draw(source)
        draw.text((1, 1), "WINTERNIGHT", fill=(24, 29, 38, 255), font=ImageFont.load_default())
        draw.text((0, 0), "WINTERNIGHT", fill=(236, 215, 144, 255), font=ImageFont.load_default())
        draw.text(
            (21, 12),
            "A TACTICAL RPG",
            fill=(194, 205, 218, 255),
            font=ImageFont.load_default(),
        )
        image = source.resize((220, 52), Image.Resampling.NEAREST)
    elif asset_id == "press_start":
        # LT's title widget treats this texture as eight vertically stacked
        # animation frames. Repeat a stable graybox prompt in every frame so
        # it remains readable throughout the animation cycle.
        frame = Image.new("RGBA", (66, 9), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        draw.text((1, 1), "PRESS X", fill=(20, 24, 32, 255), font=ImageFont.load_default())
        draw.text((0, 0), "PRESS X", fill=(244, 238, 211, 255), font=ImageFont.load_default())
        scaled_frame = frame.resize((132, 18), Image.Resampling.NEAREST)
        image = Image.new("RGBA", (132, 18 * 8), (0, 0, 0, 0))
        for frame_index in range(8):
            image.alpha_composite(scaled_frame, (0, frame_index * 18))
    else:
        raise ValueError(f"unsupported graybox UI sprite {asset_id}")
    _save(image, path)


def _campaign_tileset(
    path: Path, terrain_colors: dict[str, tuple[int, int, int]]
) -> dict[str, tuple[int, int]]:
    terrain_ids = sorted(terrain_colors)
    image = Image.new("RGBA", (16 * len(terrain_ids), 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    coordinates: dict[str, tuple[int, int]] = {}
    for index, terrain_id in enumerate(terrain_ids):
        x = index * 16
        base = terrain_colors[terrain_id] + (255,)
        shadow = tuple(max(0, channel - 22) for channel in terrain_colors[terrain_id]) + (255,)
        draw.rectangle((x, 0, x + 15, 15), fill=base)
        draw.line((x, 8, x + 15, 8), fill=shadow)
        draw.line((x + 8, 0, x + 8, 15), fill=shadow)
        coordinates[terrain_id] = (index, 0)
    _save(image, path)
    return coordinates


def _campaign_map_sprite(
    stand_path: Path,
    move_path: Path,
    color: tuple[int, int, int, int],
    kind: str,
) -> None:
    stand = Image.new("RGBA", (192, 144), COLORKEY)
    move = Image.new("RGBA", (192, 160), COLORKEY)
    for image, cell_w, cell_h, cols, rows in ((stand, 64, 48, 3, 3), (move, 48, 40, 4, 4)):
        draw = ImageDraw.Draw(image)
        for row in range(rows):
            for col in range(cols):
                ox, oy = col * cell_w, row * cell_h
                cx = ox + cell_w // 2
                baseline = oy + min(cell_h - 4, 36)
                ink = (24, 24, 32, 255)
                skin = (208, 172, 128, 255)
                if "target" in kind:
                    draw.line((cx, baseline - 17, cx, baseline), fill=ink, width=2)
                    draw.ellipse(
                        (cx - 7, baseline - 28, cx + 7, baseline - 14),
                        fill=(224, 214, 181, 255),
                        outline=ink,
                    )
                    draw.ellipse(
                        (cx - 3, baseline - 24, cx + 3, baseline - 18),
                        fill=color,
                        outline=ink,
                    )
                    draw.line((cx - 6, baseline, cx + 6, baseline), fill=ink, width=2)
                    continue
                if "trolloc" in kind:
                    draw.polygon(
                        ((cx - 6, baseline - 23), (cx - 2, baseline - 30), (cx, baseline - 22)),
                        fill=(95, 73, 54, 255),
                        outline=ink,
                    )
                    draw.polygon(
                        ((cx + 6, baseline - 23), (cx + 2, baseline - 30), (cx, baseline - 22)),
                        fill=(95, 73, 54, 255),
                        outline=ink,
                    )
                    skin = (116, 91, 66, 255)
                draw.ellipse(
                    (cx - 4, baseline - 27, cx + 4, baseline - 19),
                    fill=skin,
                    outline=ink,
                )
                draw.polygon(
                    ((cx, baseline - 20), (cx - 7, baseline - 5), (cx + 7, baseline - 5)),
                    fill=color,
                    outline=ink,
                )
                draw.line((cx - 5, baseline - 5, cx - 7, baseline), fill=ink, width=2)
                draw.line((cx + 5, baseline - 5, cx + 7, baseline), fill=ink, width=2)
                if "archer" in kind:
                    draw.arc(
                        (cx + 3, baseline - 23, cx + 13, baseline - 7),
                        80,
                        280,
                        fill=(121, 77, 40, 255),
                        width=2,
                    )
                elif "sword" in kind:
                    draw.line((cx + 5, baseline - 17, cx + 11, baseline - 27), fill=ink, width=2)
                elif "magic" in kind:
                    draw.line(
                        (cx - 8, baseline - 17, cx - 8, baseline),
                        fill=(91, 61, 36, 255),
                        width=2,
                    )
                    draw.point((cx - 8, baseline - 20), fill=(245, 210, 85, 255))
    _save(stand, stand_path)
    _save(move, move_path)


def generate_campaign_assets(
    directory: Path, bundle: CampaignBundle, root: Path
) -> CampaignAssetPaths:
    directory.mkdir(parents=True, exist_ok=True)
    font_image = directory / "font.png"
    font_index = directory / "font.idx"
    _font(font_image, font_index)

    backgrounds: dict[str, Path] = {}
    portraits: dict[str, Path] = {}
    map_sprites: dict[str, tuple[Path, Path]] = {}
    ui_sprites: dict[str, Path] = {}
    for asset in sorted(bundle.asset_manifest.assets, key=lambda entry: entry.id):
        if asset.approval_status not in {"placeholder", "approved"}:
            continue
        if asset.type == "background":
            path = directory / f"background-{asset.id}.png"
            if asset.provenance == "ai_generated":
                _ai_background(path, asset, root)
            else:
                _campaign_background(path, asset.id)
            _verify_processed_hash(path, asset)
            backgrounds[asset.id] = path
        elif asset.type == "portrait":
            path = directory / f"portrait-{asset.id}.png"
            if asset.provenance == "ai_generated":
                _ai_portrait(path, asset, root)
            else:
                _portrait(path, *_identity_colors(asset.subject_id))
            _verify_processed_hash(path, asset)
            portraits[asset.id] = path
        elif asset.type == "map_sprite":
            if asset.provenance != "programmatic_placeholder":
                raise ValueError(f"unsupported map-sprite provenance for {asset.id}")
            stand = directory / f"map-{asset.id}-stand.png"
            move = directory / f"map-{asset.id}-move.png"
            _campaign_map_sprite(
                stand,
                move,
                _identity_colors(asset.subject_id)[1],
                asset.id,
            )
            map_sprites[asset.id] = (stand, move)
        elif asset.type == "ui":
            if asset.provenance != "programmatic_placeholder":
                raise ValueError(f"unsupported UI provenance for {asset.id}")
            path = directory / f"ui-{asset.id}.png"
            _campaign_ui_sprite(path, asset.id)
            ui_sprites[asset.id] = path

    terrain_colors: dict[str, tuple[int, int, int]] = {}
    for layout in bundle.maps:
        for entry in layout.legend.values():
            terrain_colors.setdefault(entry.terrain_id, entry.color)
    tileset = directory / "campaign-tileset.png"
    terrain_tiles = _campaign_tileset(tileset, terrain_colors)
    return CampaignAssetPaths(
        backgrounds,
        portraits,
        tileset,
        terrain_tiles,
        map_sprites,
        ui_sprites,
        font_image,
        font_index,
    )
