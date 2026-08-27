from __future__ import annotations

import hashlib
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from .models import AssetManifestEntry, CampaignBundle, TerrainLegendEntry

# Pinned LT 2026.02.17a treats this exact RGB value as transparent for
# portraits and map sprites. Alpha alone is not sufficient for these resources.
COLORKEY = (128, 160, 128, 255)
BLUE = (56, 80, 224, 255)
RED = (224, 16, 16, 255)
CAMPAIGN_LIGHTING = ("day", "night", "firelit")
CAMPAIGN_TILE_VARIANTS = 4

TerrainTileKey = tuple[str, str, int]


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
    tileset_id: str
    tileset: Path
    terrain_tiles: dict[TerrainTileKey, tuple[int, int]]
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


def _villager_portrait(path: Path, identity: str) -> None:
    """Draw a deterministic LT portrait sheet for generic civilian dialogue."""

    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    feminine = "woman" in identity
    outline = (34, 27, 25, 255)
    skin = (190 + digest[0] % 20, 142 + digest[1] % 22, 102 + digest[2] % 18, 255)
    skin_shadow = tuple(max(0, channel - 42) for channel in skin[:3]) + (255,)
    hair = (43 + digest[3] % 35, 28 + digest[4] % 28, 20 + digest[5] % 20, 255)
    tunic = (55 + digest[6] % 55, 68 + digest[7] % 55, 77 + digest[8] % 55, 255)
    tunic_shadow = tuple(max(0, channel - 28) for channel in tunic[:3]) + (255,)
    main = Image.new("RGBA", (96, 80), COLORKEY)
    draw = ImageDraw.Draw(main)

    # Clothing and shoulders occupy the lower third so the dialogue portrait
    # reads as a person rather than a floating geometric head.
    draw.polygon(((3, 79), (9, 67), (28, 57), (47, 54), (69, 59), (91, 70), (95, 79)), fill=outline)
    draw.polygon(((7, 79), (13, 69), (31, 60), (47, 58), (67, 62), (87, 72), (91, 79)), fill=tunic)
    draw.polygon(((7, 79), (13, 69), (31, 64), (29, 79)), fill=tunic_shadow)
    draw.rectangle((39, 46, 57, 62), fill=outline)
    draw.rectangle((42, 46, 55, 61), fill=skin_shadow)

    if feminine:
        draw.polygon(
            (
                (21, 20),
                (27, 8),
                (43, 3),
                (62, 7),
                (75, 19),
                (72, 60),
                (62, 68),
                (57, 48),
                (30, 49),
                (27, 68),
                (18, 57),
            ),
            fill=outline,
        )
        draw.polygon(
            (
                (24, 20),
                (29, 10),
                (44, 6),
                (60, 9),
                (71, 20),
                (67, 56),
                (61, 61),
                (58, 44),
                (29, 46),
                (26, 59),
                (22, 55),
            ),
            fill=hair,
        )
    else:
        draw.polygon(
            ((22, 18), (29, 7), (44, 3), (63, 8), (74, 20), (69, 31), (25, 31)),
            fill=outline,
        )

    draw.ellipse((24, 11, 72, 59), fill=outline)
    draw.ellipse((27, 13, 69, 57), fill=skin)
    draw.polygon(((27, 36), (34, 52), (48, 58), (31, 54)), fill=skin_shadow)
    if feminine:
        draw.polygon(
            (
                (25, 22),
                (29, 10),
                (45, 6),
                (63, 10),
                (70, 21),
                (61, 18),
                (53, 25),
                (44, 17),
                (35, 24),
            ),
            fill=hair,
        )
    else:
        draw.polygon(
            (
                (24, 21),
                (30, 9),
                (44, 5),
                (64, 10),
                (72, 21),
                (62, 18),
                (55, 24),
                (47, 17),
                (38, 23),
                (30, 19),
            ),
            fill=hair,
        )

    eye_white = (226, 211, 181, 255)
    eye_color = (43 + digest[9] % 35, 48 + digest[10] % 45, 42 + digest[11] % 35, 255)
    draw.rectangle((37, 34, 44, 37), fill=eye_white)
    draw.rectangle((55, 34, 62, 37), fill=eye_white)
    draw.rectangle((40, 34, 42, 37), fill=eye_color)
    draw.rectangle((58, 34, 60, 37), fill=eye_color)
    draw.point((41, 35), fill=outline)
    draw.point((59, 35), fill=outline)
    draw.line((36, 31, 44, 30), fill=hair, width=1)
    draw.line((55, 30, 63, 31), fill=hair, width=1)
    draw.line((49, 36, 47, 45, 51, 46), fill=skin_shadow, width=1)
    draw.line((41, 50, 48, 52, 56, 49), fill=(92, 46, 42, 255), width=1)
    draw.point((34, 42), fill=(232, 177, 128, 255))
    draw.point((65, 42), fill=(232, 177, 128, 255))

    sheet = Image.new("RGBA", (160, 112), COLORKEY)
    sheet.alpha_composite(main, (0, 0))
    minimug = ImageOps.fit(main, (32, 32), method=Image.Resampling.NEAREST, centering=(0.5, 0.32))
    sheet.alpha_composite(minimug, (128, 80))
    eye_frame = main.crop((30, 26, 68, 42)).resize((32, 16), Image.Resampling.NEAREST)
    sheet.alpha_composite(eye_frame, (128, 32))
    closed_eye = eye_frame.copy()
    closed_draw = ImageDraw.Draw(closed_eye)
    closed_draw.line((6, 10, 25, 10), fill=outline, width=2)
    sheet.alpha_composite(closed_eye, (128, 48))
    mouth = main.crop((33, 42, 65, 58))
    for frame_index, (x, y) in enumerate(((64, 80), (96, 80), (64, 96), (96, 96))):
        frame = mouth.copy()
        frame_draw = ImageDraw.Draw(frame)
        if frame_index:
            half_width = 4 + frame_index
            frame_draw.line(
                (16 - half_width, 10, 16 + half_width, 10),
                fill=(92, 46, 42, 255),
                width=1 + (frame_index == 3),
            )
        sheet.alpha_composite(frame, (x, y))
    _save(_finalize_portrait_palette(sheet), path)


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
    if asset.processing_profile == "dark_wounded":
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


def _campaign_ui_sprite(path: Path, asset_id: str, campaign_title: str) -> None:
    if asset_id == "title_logo":
        source = Image.new("RGBA", (110, 26), (0, 0, 0, 0))
        draw = ImageDraw.Draw(source)
        title_lines = textwrap.wrap(campaign_title.upper(), width=18)[:2]
        for line_index, line in enumerate(title_lines):
            x = max(0, (110 - len(line) * 6) // 2)
            y = line_index * 11
            draw.text(
                (x + 1, y + 1),
                line,
                fill=(24, 29, 38, 255),
                font=ImageFont.load_default(),
            )
            draw.text(
                (x, y),
                line,
                fill=(236, 215, 144, 255),
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
    elif asset_id == "pennant_bg":
        image = Image.new("RGBA", (240, 16), (30, 34, 42, 244))
        draw = ImageDraw.Draw(image)
        draw.line((0, 0, 239, 0), fill=(224, 216, 184, 255), width=1)
        draw.line((0, 1, 239, 1), fill=(92, 100, 112, 255), width=1)
        for x in range(0, 240, 16):
            draw.line((x, 2, x + 8, 15), fill=(38, 43, 52, 255), width=1)
    else:
        raise ValueError(f"unsupported graybox UI sprite {asset_id}")
    _save(image, path)


def _mix_color(
    color: tuple[int, int, int], target: tuple[int, int, int], amount: float
) -> tuple[int, int, int]:
    return tuple(
        round(channel * (1 - amount) + target_channel * amount)
        for channel, target_channel in zip(color, target, strict=True)
    )


def _shift_color(color: tuple[int, int, int], amount: int) -> tuple[int, int, int, int]:
    return tuple(max(0, min(255, channel + amount)) for channel in color) + (255,)


def _lit_color(
    color: tuple[int, int, int], lighting: str
) -> tuple[int, int, int]:
    if lighting == "night":
        return _mix_color(color, (18, 29, 52), 0.54)
    if lighting == "firelit":
        return _mix_color(color, (49, 30, 31), 0.48)
    return color


def _draw_campaign_terrain_tile(
    entry: TerrainLegendEntry, lighting: str, variant: int
) -> Image.Image:
    """Draw one original 16x16 rural-fantasy terrain tile.

    The source map still owns terrain identity and topology. This renderer only
    turns its semantic platform/minimap fields into a small, deterministic
    pixel vocabulary suitable for LT's native resolution.
    """

    base_rgb = _lit_color(entry.color, lighting)
    base = base_rgb + (255,)
    shadow = _shift_color(base_rgb, -24)
    deep = _shift_color(base_rgb, -46)
    highlight = _shift_color(base_rgb, 24)
    tile = Image.new("RGBA", (16, 16), base)
    draw = ImageDraw.Draw(tile)
    offset = (variant * 3) % 7

    if entry.minimap == "Lava":
        char = _lit_color((55, 45, 43), lighting)
        draw.rectangle((0, 0, 15, 15), fill=char + (255,))
        draw.rectangle((2 + variant, 10, 4 + variant, 14), fill=(151, 44, 27, 255))
        draw.polygon(
            ((3 + variant, 11), (5 + variant, 3), (7 + variant, 11)),
            fill=(235, 91, 31, 255),
        )
        draw.polygon(
            ((5 + variant, 11), (8 + variant, 6), (10 + variant, 13)),
            fill=(247, 159, 43, 255),
        )
        draw.rectangle((5 + variant, 10, 7 + variant, 13), fill=(255, 217, 96, 255))
        draw.point((12 - variant, 5 + variant), fill=(236, 85, 37, 255))
    elif entry.platform == "Plains":
        draw.point((2 + offset, 3), fill=highlight)
        draw.point((11 - variant, 12), fill=shadow)
        draw.line((4 + variant, 11, 4 + variant, 8), fill=deep)
        draw.point((3 + variant, 9), fill=highlight)
        draw.point((5 + variant, 9), fill=highlight)
        draw.line((12 - variant, 6, 12 - variant, 4), fill=shadow)
    elif entry.platform == "Road":
        draw.rectangle((0, 0, 15, 1), fill=highlight)
        draw.rectangle((0, 14, 15, 15), fill=shadow)
        draw.rectangle((2 + variant * 2, 5, 4 + variant * 2, 6), fill=shadow)
        draw.point((11 - variant, 10), fill=deep)
        draw.point((12 - variant, 10), fill=highlight)
    elif entry.platform in {"Forest", "Thicket"}:
        if entry.platform == "Thicket":
            draw.rectangle((0, 0, 15, 15), fill=deep)
        trunk = _lit_color((82, 57, 37), lighting) + (255,)
        leaf_shadow = deep
        leaf_light = highlight
        draw.rectangle((7, 9, 8, 15), fill=trunk)
        draw.ellipse((-3 + variant, 2, 8 + variant, 12), fill=leaf_shadow)
        draw.ellipse((5, 0 + variant // 2, 17, 11 + variant // 2), fill=shadow)
        draw.rectangle((3 + variant, 4, 10 + variant, 9), fill=base)
        draw.rectangle((5 + variant, 3, 8 + variant, 5), fill=leaf_light)
        if entry.platform == "Thicket":
            draw.line((1, 14, 6, 8), fill=shadow)
            draw.line((14, 15, 10, 9), fill=shadow)
    elif entry.platform == "House":
        draw.rectangle((0, 0, 15, 15), fill=base)
        for y in (3, 8, 13):
            draw.line((0, y, 15, y), fill=deep)
        seam = 4 + variant
        for y in (0, 10):
            draw.line((seam, y, seam, min(15, y + 3)), fill=shadow)
            draw.line((seam + 7, y, seam + 7, min(15, y + 3)), fill=shadow)
        draw.line((0, 0, 15, 0), fill=highlight)
    elif entry.platform == "Wall":
        draw.rectangle((0, 0, 15, 15), fill=base)
        draw.line((0, 2, 15, 2), fill=highlight)
        draw.line((0, 13, 15, 13), fill=deep)
        for x in (2 + variant, 10 + variant):
            draw.rectangle((x % 16, 0, min(15, x % 16 + 1), 15), fill=shadow)
        draw.point((6 + variant, 7), fill=deep)
    elif entry.platform == "Floor":
        draw.rectangle((0, 0, 15, 15), fill=base)
        for y in (4, 9, 14):
            draw.line((0, y, 15, y), fill=shadow)
        draw.line((4 + variant, 0, 4 + variant, 4), fill=deep)
        draw.line((11 - variant, 5, 11 - variant, 9), fill=deep)
        draw.point((7 + variant, 12), fill=highlight)
    elif entry.platform == "Pillar":
        ground = _lit_color((59, 87, 61), lighting)
        draw.rectangle((0, 0, 15, 15), fill=ground + (255,))
        stone = _lit_color((119, 123, 117), lighting)
        draw.ellipse(
            (1, 3, 14, 14),
            fill=_shift_color(stone, -30),
            outline=_shift_color(stone, -48),
        )
        draw.ellipse(
            (3, 2, 12, 10),
            fill=_shift_color(stone, 18),
            outline=_shift_color(stone, -30),
        )
        draw.ellipse((5, 4, 10, 8), fill=_lit_color((43, 79, 108), lighting) + (255,))
        draw.line((4, 3, 10, 3), fill=_shift_color(stone, 35))
    elif entry.platform == "Ruins":
        draw.rectangle((0, 0, 15, 15), fill=base)
        draw.polygon(((1, 11), (4, 5), (8, 8), (7, 13)), fill=shadow)
        draw.polygon(((9, 13), (10, 7), (15, 5), (15, 14)), fill=deep)
        draw.line((2, 10, 6, 8), fill=highlight)
        draw.rectangle((10 + variant % 2, 2, 13 + variant % 2, 4), fill=shadow)
    else:
        draw.point((3 + offset, 5), fill=highlight)
        draw.point((12 - variant, 11), fill=shadow)

    if lighting == "firelit" and entry.minimap != "Lava":
        fire_glint = _mix_color(base_rgb, (210, 91, 43), 0.3) + (255,)
        draw.line((0, 0, 15, 0), fill=fire_glint)
    return tile


def _campaign_tileset(
    path: Path, terrain_entries: dict[str, TerrainLegendEntry]
) -> dict[TerrainTileKey, tuple[int, int]]:
    terrain_ids = sorted(terrain_entries)
    width_in_tiles = len(terrain_ids) * CAMPAIGN_TILE_VARIANTS
    image = Image.new("RGBA", (16 * width_in_tiles, 16 * len(CAMPAIGN_LIGHTING)))
    coordinates: dict[TerrainTileKey, tuple[int, int]] = {}
    for lighting_index, lighting in enumerate(CAMPAIGN_LIGHTING):
        for terrain_index, terrain_id in enumerate(terrain_ids):
            for variant in range(CAMPAIGN_TILE_VARIANTS):
                tile_x = terrain_index * CAMPAIGN_TILE_VARIANTS + variant
                tile_y = lighting_index
                image.alpha_composite(
                    _draw_campaign_terrain_tile(
                        terrain_entries[terrain_id], lighting, variant
                    ),
                    (tile_x * 16, tile_y * 16),
                )
                coordinates[(terrain_id, lighting, variant)] = (tile_x, tile_y)
    _save(image, path)
    return coordinates


# LT recolors map sprites by replacing these exact entries from its pinned
# sixteen-color blue-team palette. Keeping every sprite color inside that
# palette makes player, enemy, ally, and waited variants work without separate
# sheets while still leaving enough values for skin, hair, cloth, and metal.
_MS_INK = (64, 56, 56, 255)
_MS_SHADOW = (88, 72, 120, 255)
_MS_STEEL = (112, 96, 96, 255)
_MS_STEEL_LIGHT = (128, 136, 112, 255)
_MS_BROWN = (176, 144, 88, 255)
_MS_SKIN = (248, 248, 208, 255)
_MS_WHITE = (248, 248, 248, 255)
_MS_TEAM_DARK = (56, 56, 144, 255)
_MS_TEAM_MID = (56, 80, 224, 255)
_MS_TEAM_LIGHT = (40, 160, 248, 255)
_MS_TEAM_GLOW = (24, 240, 248, 255)
_MS_ACCENT = (232, 16, 24, 255)
_MS_GOLD = (248, 248, 64, 255)


def _map_sprite_target(draw: ImageDraw.ImageDraw, cx: int, baseline: int, phase: int) -> None:
    """Draw an original straw practice target with a subtle wind animation."""

    lean = (-1, 0, 1)[phase % 3]
    draw.rectangle((cx - 1 + lean, baseline - 19, cx + 1 + lean, baseline), fill=_MS_BROWN)
    draw.rectangle((cx - 9, baseline - 1, cx + 9, baseline + 1), fill=_MS_INK)
    draw.line((cx - 1, baseline - 5, cx - 7, baseline + 2), fill=_MS_BROWN, width=2)
    draw.line((cx + 1, baseline - 5, cx + 7, baseline + 2), fill=_MS_BROWN, width=2)
    draw.ellipse(
        (cx - 9 + lean, baseline - 31, cx + 9 + lean, baseline - 13),
        fill=_MS_INK,
    )
    draw.ellipse(
        (cx - 7 + lean, baseline - 29, cx + 7 + lean, baseline - 15),
        fill=_MS_SKIN,
    )
    draw.ellipse(
        (cx - 4 + lean, baseline - 26, cx + 4 + lean, baseline - 18),
        fill=_MS_ACCENT,
    )
    draw.rectangle(
        (cx - 1 + lean, baseline - 23, cx + 1 + lean, baseline - 21),
        fill=_MS_GOLD,
    )
    draw.point((cx - 5 + lean, baseline - 27), fill=_MS_BROWN)
    draw.point((cx + 6 + lean, baseline - 19), fill=_MS_BROWN)


def _map_sprite_body(
    draw: ImageDraw.ImageDraw,
    cx: int,
    baseline: int,
    kind: str,
    direction: str,
    phase: int,
    *,
    active: bool = False,
) -> None:
    """Draw one tiny but readable, legally clean tactical-map unit frame."""

    if kind == "target":
        _map_sprite_target(draw, cx, baseline, phase)
        return

    step = (-1, 0, 1, 0)[phase % 4]
    bob = (0, -1, 0, 0)[phase % 4]
    if active:
        bob = (0, -2, 0)[phase % 3]
    baseline += bob
    side = -1 if direction == "left" else 1
    facing_side = direction in {"left", "right"}
    back = direction == "up"

    if kind == "beast":
        # Trollocs are wider, hunched, horned, and top-heavy. Their team-color
        # armor still converts to the enemy palette through LT.
        head_x = cx + (2 * side if facing_side else 0)
        draw.polygon(
            (
                (head_x - 7, baseline - 24),
                (head_x - 9, baseline - 33),
                (head_x - 3, baseline - 28),
            ),
            fill=_MS_BROWN,
        )
        draw.polygon(
            (
                (head_x + 7, baseline - 24),
                (head_x + 9, baseline - 33),
                (head_x + 3, baseline - 28),
            ),
            fill=_MS_BROWN,
        )
        draw.ellipse((head_x - 7, baseline - 30, head_x + 7, baseline - 17), fill=_MS_INK)
        draw.rectangle((head_x - 5, baseline - 27, head_x + 5, baseline - 19), fill=_MS_BROWN)
        if not back:
            eye_x = head_x + (3 * side if facing_side else 0)
            draw.point((eye_x, baseline - 25), fill=_MS_GOLD)
            draw.rectangle((head_x - 2, baseline - 20, head_x + 4, baseline - 18), fill=_MS_STEEL)
        draw.polygon(
            (
                (cx - 10, baseline - 20),
                (cx - 13, baseline - 8),
                (cx - 8, baseline - 3),
                (cx + 9, baseline - 3),
                (cx + 13, baseline - 9),
                (cx + 9, baseline - 20),
            ),
            fill=_MS_INK,
        )
        draw.polygon(
            (
                (cx - 7, baseline - 19),
                (cx, baseline - 22),
                (cx + 8, baseline - 18),
                (cx + 6, baseline - 5),
                (cx - 6, baseline - 5),
            ),
            fill=_MS_TEAM_DARK,
        )
        draw.rectangle((cx - 7, baseline - 15, cx + 7, baseline - 12), fill=_MS_TEAM_MID)
        draw.point((cx - 4, baseline - 14), fill=_MS_TEAM_LIGHT)
        draw.line((cx - 6, baseline - 3, cx - 9 - step, baseline + 1), fill=_MS_INK, width=3)
        draw.line((cx + 6, baseline - 3, cx + 9 + step, baseline + 1), fill=_MS_INK, width=3)
        weapon_side = side if facing_side else 1
        draw.line(
            (cx + 10 * weapon_side, baseline - 16, cx + 15 * weapon_side, baseline - 30),
            fill=_MS_BROWN,
            width=2,
        )
        draw.polygon(
            (
                (cx + 12 * weapon_side, baseline - 31),
                (cx + 18 * weapon_side, baseline - 33),
                (cx + 17 * weapon_side, baseline - 25),
            ),
            fill=_MS_STEEL,
        )
        return

    head_x = cx + (2 * side if facing_side else 0)
    body_left, body_right = (cx - 5, cx + 5) if facing_side else (cx - 7, cx + 7)

    # Legs and boots go down first so the coat/robe overlaps them cleanly.
    if kind == "caster":
        draw.polygon(
            (
                (cx - 5, baseline - 10),
                (cx - 9, baseline),
                (cx + 9, baseline),
                (cx + 5, baseline - 10),
            ),
            fill=_MS_TEAM_DARK,
        )
        draw.rectangle((cx - 7, baseline - 4, cx + 7, baseline - 2), fill=_MS_TEAM_LIGHT)
    else:
        draw.line((cx - 3, baseline - 8, cx - 5 - step, baseline), fill=_MS_INK, width=3)
        draw.line((cx + 3, baseline - 8, cx + 5 + step, baseline), fill=_MS_INK, width=3)
        draw.point((cx - 6 - step, baseline), fill=_MS_STEEL)
        draw.point((cx + 6 + step, baseline), fill=_MS_STEEL)

    draw.polygon(
        (
            (body_left, baseline - 20),
            (body_left - 2, baseline - 8),
            (cx, baseline - 5),
            (body_right + 2, baseline - 8),
            (body_right, baseline - 20),
        ),
        fill=_MS_TEAM_DARK,
    )
    draw.rectangle((body_left + 1, baseline - 18, body_right - 1, baseline - 8), fill=_MS_TEAM_MID)
    draw.line((cx, baseline - 17, cx, baseline - 8), fill=_MS_TEAM_LIGHT)
    draw.point((cx, baseline - 16), fill=_MS_TEAM_GLOW)

    # Head, hair, and one-pixel features remain distinct at native 240x160.
    draw.ellipse((head_x - 5, baseline - 29, head_x + 5, baseline - 19), fill=_MS_INK)
    draw.rectangle((head_x - 4, baseline - 27, head_x + 4, baseline - 20), fill=_MS_SKIN)
    if kind == "archer":
        draw.polygon(
            (
                (head_x - 5, baseline - 25),
                (head_x - 3, baseline - 31),
                (head_x + 5, baseline - 28),
                (head_x + 5, baseline - 23),
            ),
            fill=_MS_BROWN,
        )
    elif kind == "sword":
        draw.rectangle((head_x - 5, baseline - 30, head_x + 5, baseline - 26), fill=_MS_SHADOW)
        draw.point((head_x - 5, baseline - 25), fill=_MS_SHADOW)
    elif kind == "caster":
        if back:
            draw.polygon(
                (
                    (head_x - 6, baseline - 20),
                    (head_x - 5, baseline - 31),
                    (head_x + 4, baseline - 32),
                    (head_x + 7, baseline - 20),
                ),
                fill=_MS_INK,
            )
        else:
            draw.rectangle(
                (head_x - 5, baseline - 31, head_x + 5, baseline - 27),
                fill=_MS_INK,
            )
            draw.line(
                (head_x - 5, baseline - 27, head_x - 5, baseline - 20),
                fill=_MS_INK,
                width=2,
            )
            draw.line(
                (head_x + 5, baseline - 27, head_x + 5, baseline - 20),
                fill=_MS_INK,
                width=2,
            )
    else:  # civilian
        draw.polygon(
            (
                (head_x - 5, baseline - 25),
                (head_x - 2, baseline - 30),
                (head_x + 5, baseline - 27),
                (head_x + 5, baseline - 24),
            ),
            fill=_MS_BROWN,
        )
        draw.rectangle((body_left + 1, baseline - 18, body_right - 1, baseline - 14), fill=_MS_SKIN)
        draw.rectangle((cx - 5, baseline - 11, cx + 5, baseline - 9), fill=_MS_BROWN)

    if not back:
        eye_x = head_x + (3 * side if facing_side else 0)
        draw.point((eye_x, baseline - 24), fill=_MS_INK)
    if kind == "sword":
        draw.rectangle(
            (body_left - 2, baseline - 19, body_right + 2, baseline - 16), fill=_MS_STEEL
        )
        weapon_side = side if facing_side else 1
        tip_y = baseline - 34 if active else baseline - 29
        draw.line(
            (cx + 6 * weapon_side, baseline - 10, cx + 13 * weapon_side, tip_y),
            fill=_MS_WHITE,
            width=2,
        )
        draw.point((cx + 13 * weapon_side, tip_y), fill=_MS_GOLD)
    elif kind == "archer":
        bow_x = cx + (8 * side if facing_side else 9)
        draw.arc(
            (bow_x - 5, baseline - 24, bow_x + 5, baseline - 5), 80, 280, fill=_MS_BROWN, width=2
        )
        draw.line((bow_x, baseline - 23, bow_x, baseline - 6), fill=_MS_WHITE)
        draw.line((cx - 8, baseline - 20, cx - 8, baseline - 8), fill=_MS_BROWN, width=2)
        draw.point((cx - 9, baseline - 21), fill=_MS_WHITE)
    elif kind == "caster":
        staff_side = side if facing_side else -1
        staff_x = cx + 9 * staff_side
        draw.line((staff_x, baseline - 22, staff_x, baseline), fill=_MS_BROWN, width=2)
        draw.point((staff_x, baseline - 25), fill=_MS_TEAM_GLOW)
        if active:
            draw.point((staff_x - 2, baseline - 27), fill=_MS_GOLD)
            draw.point((staff_x + 3, baseline - 24), fill=_MS_WHITE)
            draw.point((staff_x - 3, baseline - 22), fill=_MS_TEAM_LIGHT)
    else:
        # A tiny satchel turns the civilian into a readable noncombatant rather
        # than a recolored fighter.
        bag_side = side if facing_side else 1
        draw.line((cx, baseline - 17, cx + 7 * bag_side, baseline - 8), fill=_MS_BROWN)
        draw.rectangle(
            (cx + 5 * bag_side - 2, baseline - 10, cx + 5 * bag_side + 2, baseline - 6),
            fill=_MS_BROWN,
        )


def _campaign_map_sprite(stand_path: Path, move_path: Path, kind: str) -> None:
    """Assemble LT's pinned 3x3 stand and 4x4 directional move layouts."""

    stand = Image.new("RGBA", (192, 144), COLORKEY)
    stand_draw = ImageDraw.Draw(stand)
    for frame in range(3):
        _map_sprite_body(stand_draw, frame * 64 + 32, 36, kind, "down", frame)
        # LT reserves the middle row for waited sprites. This project asks the
        # engine to derive that tint, but the reserved cells still receive a
        # complete silhouette instead of being left as accidental empty data.
        _map_sprite_body(stand_draw, frame * 64 + 32, 48 + 36, kind, "down", frame)
        _map_sprite_body(
            stand_draw,
            frame * 64 + 32,
            96 + 36,
            kind,
            "down",
            frame,
            active=True,
        )

    move = Image.new("RGBA", (192, 160), COLORKEY)
    move_draw = ImageDraw.Draw(move)
    for row, direction in enumerate(("down", "left", "right", "up")):
        for frame in range(4):
            _map_sprite_body(
                move_draw,
                frame * 48 + 24,
                row * 40 + 36,
                kind,
                direction,
                frame,
            )
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
            if asset.provenance in {"ai_generated", "original", "licensed"}:
                _ai_background(path, asset, root)
            else:
                _campaign_background(path, asset.id)
            _verify_processed_hash(path, asset)
            backgrounds[asset.id] = path
        elif asset.type == "portrait":
            path = directory / f"portrait-{asset.id}.png"
            if asset.provenance in {"ai_generated", "original", "licensed"}:
                _ai_portrait(path, asset, root)
            elif asset.subject_id in {"villager_man", "villager_woman"}:
                _villager_portrait(path, asset.subject_id)
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
                asset.variant,
            )
            map_sprites[asset.id] = (stand, move)
        elif asset.type == "ui":
            if asset.provenance != "programmatic_placeholder":
                raise ValueError(f"unsupported UI provenance for {asset.id}")
            path = directory / f"ui-{asset.id}.png"
            _campaign_ui_sprite(path, asset.id, bundle.campaign.title)
            ui_sprites[asset.id] = path

    approved_tilesets = [
        asset
        for asset in bundle.asset_manifest.assets
        if asset.type == "tileset" and asset.approval_status in {"placeholder", "approved"}
    ]
    if len(approved_tilesets) != 1:
        raise ValueError("campaign requires exactly one approved tileset manifest entry")

    terrain_entries: dict[str, TerrainLegendEntry] = {}
    for layout in bundle.maps:
        for entry in layout.legend.values():
            terrain_entries.setdefault(entry.terrain_id, entry)
    tileset = directory / "campaign-tileset.png"
    terrain_tiles = _campaign_tileset(tileset, terrain_entries)
    return CampaignAssetPaths(
        backgrounds,
        portraits,
        approved_tilesets[0].id,
        tileset,
        terrain_tiles,
        map_sprites,
        ui_sprites,
        font_image,
        font_index,
    )
