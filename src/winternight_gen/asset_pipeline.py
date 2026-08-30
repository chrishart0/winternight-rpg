from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.util import find_spec
from math import ceil
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from .models import AssetManifestEntry, CampaignBundle, TerrainLegendEntry

# Pinned LT 2026.02.17a treats this exact RGB value as transparent for
# portraits and map sprites. Alpha alone is not sufficient for these resources.
COLORKEY = (128, 160, 128, 255)
BLUE = (56, 80, 224, 255)
RED = (224, 16, 16, 255)
CAMPAIGN_LIGHTING = ("day", "night", "firelit")
CAMPAIGN_TILE_VARIANTS = 4

# Title-start wordmark. Original condensed capitals; not a TTF or commercial dump.
_TITLE_NIGHT = (7, 12, 24, 255)
_TITLE_UMBER = (24, 29, 38, 255)
_TITLE_GOLD = (220, 186, 104, 255)
_TITLE_ICE = (236, 244, 248, 255)
_TITLE_FROST = (148, 176, 196, 255)
_TITLE_CREAM = (244, 238, 211, 255)
_TITLE_LETTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ -'")
_PRESS_START_ALPHAS = (0.70, 0.85, 1.00, 1.00, 1.00, 0.85, 0.70, 0.55)

_GLYPH_DISPLAY = {
    "A": (
        "..####..",
        ".##..##.",
        ".##..##.",
        ".######.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "........",
    ),
    "B": (
        ".#####..",
        ".##..##.",
        ".##..##.",
        ".#####..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".#####..",
        "........",
    ),
    "C": (
        "..####..",
        ".##..##.",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##..##.",
        "..####..",
        "........",
    ),
    "D": (
        ".#####..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".#####..",
        "........",
    ),
    "E": (
        ".######.",
        ".##.....",
        ".##.....",
        ".#####..",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".######.",
        "........",
    ),
    "F": (
        ".######.",
        ".##.....",
        ".##.....",
        ".#####..",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        "........",
    ),
    "G": (
        "..####..",
        ".##..##.",
        ".##.....",
        ".##.....",
        ".##.###.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "..####..",
        "........",
    ),
    "H": (
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".######.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "........",
    ),
    "I": (
        "..####..",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "..####..",
        "........",
    ),
    "J": (
        ".....##.",
        ".....##.",
        ".....##.",
        ".....##.",
        ".....##.",
        ".....##.",
        ".##..##.",
        ".##..##.",
        "..####..",
        "........",
    ),
    "K": (
        ".##..##.",
        ".##.##..",
        ".####...",
        ".###....",
        ".####...",
        ".##.##..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "........",
    ),
    "L": (
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".######.",
        "........",
    ),
    "M": (
        ".##...##",
        ".###.###",
        ".##.#.##",
        ".##.#.##",
        ".##.#.##",
        ".##...##",
        ".##...##",
        ".##...##",
        ".##...##",
        "........",
    ),
    "N": (
        ".##...##",
        ".###..##",
        ".###..##",
        ".##.#.##",
        ".##.#.##",
        ".##..###",
        ".##..###",
        ".##...##",
        ".##...##",
        "........",
    ),
    "O": (
        "..####..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "..####..",
        "........",
    ),
    "P": (
        ".#####..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".#####..",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        "........",
    ),
    "Q": (
        "..####..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##.#.#.",
        ".##..##.",
        "..#####.",
        "........",
    ),
    "R": (
        ".#####..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".#####..",
        ".####...",
        ".##.##..",
        ".##..##.",
        ".##..##.",
        "........",
    ),
    "S": (
        "..#####.",
        ".##.....",
        ".##.....",
        "..####..",
        ".....##.",
        ".....##.",
        ".....##.",
        ".....##.",
        ".#####..",
        "........",
    ),
    "T": (
        ".######.",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "........",
    ),
    "U": (
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "..####..",
        "........",
    ),
    "V": (
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "..####..",
        "..####..",
        "...##...",
        "........",
    ),
    "W": (
        ".##...##",
        ".##...##",
        ".##...##",
        ".##.#.##",
        ".##.#.##",
        ".##.#.##",
        ".###.###",
        ".##...##",
        ".##...##",
        "........",
    ),
    "X": (
        ".##..##.",
        ".##..##.",
        "..####..",
        "...##...",
        "...##...",
        "...##...",
        "..####..",
        ".##..##.",
        ".##..##.",
        "........",
    ),
    "Y": (
        ".##..##.",
        ".##..##.",
        "..####..",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "........",
    ),
    "Z": (
        ".######.",
        ".....##.",
        "....##..",
        "...##...",
        "..##....",
        "..##....",
        ".##.....",
        ".##.....",
        ".######.",
        "........",
    ),
    " ": ("........",) * 10,
    "-": (
        "........",
        "........",
        "........",
        "........",
        ".######.",
        "........",
        "........",
        "........",
        "........",
        "........",
    ),
    "'": (
        "...##...",
        "...##...",
        "...#....",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
    ),
}
_GLYPH_PROMPT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    " ": (".....",) * 7,
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
}


def _title_wordmark(campaign_title: str) -> str:
    head = campaign_title.split(":", 1)[0].strip().upper()
    return "".join(character for character in head if character in _TITLE_LETTERS)


def _line_width(text: str, glyph_width: int, tracking: int) -> int:
    if not text:
        return 0
    return len(text) * glyph_width + (len(text) - 1) * tracking


def _wordmark_layout(text: str) -> tuple[tuple[str, ...], int]:
    max_width = 110
    glyph_width = 8
    if _line_width(text, glyph_width, 1) <= max_width:
        return (text,), 1
    if _line_width(text, glyph_width, 0) <= max_width:
        return (text,), 0
    words = text.split()
    for split_at in range(1, len(words)):
        first = " ".join(words[:split_at])
        second = " ".join(words[split_at:])
        tracking = (
            1
            if _line_width(first, glyph_width, 1) <= max_width
            and _line_width(second, glyph_width, 1) <= max_width
            else 0
        )
        if (
            _line_width(first, glyph_width, tracking) <= max_width
            and _line_width(second, glyph_width, tracking) <= max_width
        ):
            return (first, second), tracking
    mid = (len(text) + 1) // 2
    return (text[:mid].rstrip(), text[mid:].lstrip()), 0


def _stamp_glyph(
    pixels,
    origin_x: int,
    origin_y: int,
    rows: tuple[str, ...],
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    highlight: tuple[int, int, int, int] | None,
    size: tuple[int, int],
) -> None:
    ink = [
        (origin_x + column, origin_y + row_index)
        for row_index, row in enumerate(rows)
        for column, cell in enumerate(row)
        if cell == "#"
    ]
    marked = set(ink)
    width, height = size

    def put(x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            pixels[x, y] = color

    for x, y in ink:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            neighbor = (x + dx, y + dy)
            if neighbor not in marked:
                put(*neighbor, outline)
    for x, y in ink:
        put(x, y, fill)
    if highlight:
        top_row = {}
        for x, y in ink:
            previous = top_row.get(x)
            if previous is None or y < previous:
                top_row[x] = y
        for x, y in top_row.items():
            put(x, y, highlight)


def _draw_glyph_line(
    image: Image.Image,
    text: str,
    y: int,
    glyphs: dict[str, tuple[str, ...]],
    tracking: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    highlight: tuple[int, int, int, int] | None,
) -> tuple[int, int]:
    glyph_width = len(next(iter(glyphs.values()))[0])
    width = _line_width(text, glyph_width, tracking)
    x = max(0, (image.width - width) // 2)
    start_x = x
    pixels = image.load()
    for character in text:
        rows = glyphs.get(character, glyphs[" "])
        _stamp_glyph(pixels, x, y, rows, fill, outline, highlight, image.size)
        x += glyph_width + tracking
    return start_x, width


def _title_logo_image(campaign_title: str) -> Image.Image:
    source = Image.new("RGBA", (110, 36), (0, 0, 0, 0))
    lines, tracking = _wordmark_layout(_title_wordmark(campaign_title))
    line_height = 10
    gap = 2
    bar_gap = 1
    content_height = len(lines) * line_height + max(0, len(lines) - 1) * gap + bar_gap + 1
    y = max(1, (36 - content_height) // 2)
    last_start = 8
    last_width = source.width - 16
    for line in lines:
        last_start, last_width = _draw_glyph_line(
            source,
            line,
            y,
            _GLYPH_DISPLAY,
            tracking,
            _TITLE_GOLD,
            _TITLE_UMBER,
            _TITLE_ICE,
        )
        y += line_height + gap
    bar_y = y - gap + bar_gap
    draw = ImageDraw.Draw(source)
    draw.line(
        (last_start + 8, bar_y, last_start + last_width - 9, bar_y),
        fill=_TITLE_FROST,
        width=1,
    )
    return source.resize((220, 72), Image.Resampling.NEAREST)


def _multiply_alpha(image: Image.Image, factor: float) -> Image.Image:
    if factor >= 1.0:
        return image
    scaled = image.copy()
    alpha = scaled.getchannel("A").point(lambda value: round(value * factor))
    scaled.putalpha(alpha)
    return scaled


def _press_start_image() -> Image.Image:
    peak = Image.new("RGBA", (66, 9), (0, 0, 0, 0))
    _draw_glyph_line(
        peak,
        "PRESS START",
        1,
        _GLYPH_PROMPT,
        1,
        _TITLE_CREAM,
        _TITLE_UMBER,
        None,
    )
    scaled = peak.resize((132, 18), Image.Resampling.NEAREST)
    sheet = Image.new("RGBA", (132, 18 * 8), (0, 0, 0, 0))
    for index, factor in enumerate(_PRESS_START_ALPHAS):
        sheet.alpha_composite(_multiply_alpha(scaled, factor), (0, index * 18))
    return sheet


TerrainTileKey = tuple[str, str, int]
GuideTileKey = tuple[int, bool]


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
    guide_tileset_id: str
    guide_tileset: Path
    guide_tiles: dict[GuideTileKey, tuple[int, int]]
    map_sprites: dict[str, tuple[Path, Path]]
    ui_sprites: dict[str, Path]
    font_image: Path
    font_index: Path
    level_up_animation: Path
    miss_animation: Path
    stone_throw_animation: Path
    ball_lightning_animation: Path


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


def _portrait_sheet(
    main: Image.Image,
    *,
    eye_line: tuple[int, int, int, int],
) -> Image.Image:
    main = ImageOps.mirror(main)
    blink_x, blink_y = 30, 31
    mouth_x, mouth_y = 30, 48
    sheet = Image.new("RGBA", (160, 112), COLORKEY)
    sheet.alpha_composite(main, (32, 0))

    minimug = ImageOps.fit(main, (32, 32), method=Image.Resampling.NEAREST, centering=(0.5, 0.28))
    sheet.alpha_composite(minimug, (128, 80))

    eye = main.crop((blink_x, blink_y, blink_x + 32, blink_y + 16))
    sheet.alpha_composite(eye, (128, 48))
    closed_eye = eye.copy()
    ImageDraw.Draw(closed_eye).line((6, 9, 25, 9), fill=eye_line, width=2)
    sheet.alpha_composite(closed_eye, (128, 64))

    mouth = main.crop((mouth_x, mouth_y, mouth_x + 32, mouth_y + 16))
    sheet.alpha_composite(mouth, (96, 80))
    for x in (64, 32, 0):
        sheet.alpha_composite(mouth, (x, 80))
        sheet.alpha_composite(mouth, (x, 96))
    return _finalize_portrait_palette(sheet)


def _portrait(
    path: Path, body: tuple[int, int, int, int], accent: tuple[int, int, int, int]
) -> None:
    main = Image.new("RGBA", (96, 80), COLORKEY)
    draw = ImageDraw.Draw(main)
    draw.rectangle((8, 18, 87, 79), fill=body, outline=(24, 24, 32, 255), width=2)
    draw.ellipse((24, 12, 72, 62), fill=(207, 171, 132, 255), outline=(40, 32, 32, 255), width=2)
    draw.rectangle((29, 30, 37, 34), fill=(30, 35, 45, 255))
    draw.rectangle((58, 30, 66, 34), fill=(30, 35, 45, 255))
    draw.line((40, 49, 56, 49), fill=(85, 45, 45, 255), width=2)
    draw.polygon(((17, 24), (31, 6), (70, 8), (81, 28)), fill=accent)
    draw.rectangle((10, 60, 85, 79), fill=accent, outline=(24, 24, 32, 255), width=2)
    _save(
        _portrait_sheet(
            main,
            eye_line=(30, 35, 45, 255),
        ),
        path,
    )




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


def _font(
    image_path: Path,
    index_path: Path,
    *,
    source_font_path: Path | None = None,
    font_size: int = 9,
    cell_w: int = 10,
) -> None:
    chars = [chr(code) for code in range(32, 127)]
    cell_h, cols = 16, 16
    rows = (len(chars) + cols - 1) // cols
    image = Image.new("RGBA", (cols * cell_w, rows * cell_h * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if source_font_path is None:
        pygame_spec = find_spec("pygame")
        if not pygame_spec or not pygame_spec.origin:
            raise RuntimeError("the pinned pygame-ce runtime is required to build fonts")
        source_font_path = Path(pygame_spec.origin).with_name("freesansbold.ttf")
    if not source_font_path.is_file():
        raise RuntimeError(f"dialogue font is missing: {source_font_path}")
    font = ImageFont.truetype(source_font_path, font_size)
    lines = [f"width {cell_w}", f"height {cell_h}", "stacked", "space_offset 0"]
    for index, char in enumerate(chars):
        col, row = index % cols, index // cols
        key = "space" if char == " " else char
        width = 4 if char == " " else min(cell_w, max(1, ceil(draw.textlength(char, font=font))))
        if char != " ":
            # The left inset accommodates the face's negative left bearing
            # without clipping capitals or punctuation.
            x, y = col * cell_w + 1, row * cell_h * 2 + 1
            draw.text((x, y), char, font=font, fill=(248, 248, 248, 255))
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)):
                draw.text(
                    (x + dx, y + cell_h + dy),
                    char,
                    font=font,
                    fill=(8, 12, 16, 255),
                )
        lines.append(f"{key} {col} {row * 2} {width}")
    image.putalpha(image.getchannel("A").point(lambda alpha: 255 if alpha >= 128 else 0))
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
    draw.rectangle((38, 34, 43, 36), fill=eye_white)
    draw.rectangle((56, 34, 61, 36), fill=eye_white)
    draw.rectangle((40, 34, 41, 36), fill=eye_color)
    draw.rectangle((58, 34, 59, 36), fill=eye_color)
    draw.point((41, 35), fill=outline)
    draw.point((59, 35), fill=outline)
    draw.line((36, 31, 44, 30), fill=hair, width=1)
    draw.line((55, 30, 63, 31), fill=hair, width=1)
    draw.line((49, 36, 47, 45, 51, 46), fill=skin_shadow, width=1)
    draw.line((42, 50, 48, 51, 55, 49), fill=(92, 46, 42, 255), width=1)
    draw.point((34, 42), fill=(232, 177, 128, 255))
    draw.point((65, 42), fill=(232, 177, 128, 255))
    pixels = main.load()
    for y in range(main.height):
        for x in range(main.width):
            red, green, blue, alpha = pixels[x, y]
            if (red, green, blue, alpha) == COLORKEY:
                continue
            grain = ((digest[(x + y * 3) % len(digest)] + x * 5 + y * 7) % 13) - 6
            pixels[x, y] = (
                max(0, min(255, red + grain * 2)),
                max(0, min(255, green + grain * 2)),
                max(0, min(255, blue + grain * 2)),
                alpha,
            )

    _save(
        _portrait_sheet(main, eye_line=outline),
        path,
    )


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
        image = Image.blend(image, Image.new("RGB", image.size, (7, 12, 24)), 0.45)
        overlay = Image.new("RGBA", image.size, (7, 12, 24, 0))
        draw = ImageDraw.Draw(overlay)
        width, height = image.size
        for y in range(48):
            alpha = round(90 * (48 - y) / 48)
            draw.line((0, y, width - 1, y), fill=(7, 12, 24, alpha))
        for offset in range(72):
            y = height - 72 + offset
            alpha = round(90 * (offset + 1) / 72)
            draw.line((0, y, width - 1, y), fill=(7, 12, 24, alpha))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
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
    inset_left_x = max(4, round(cell_width * 0.04))
    inset_right_x = max(4, round(cell_width * 0.06))
    inset_y = max(4, round(cell_height * 0.04))
    return image.crop((left + inset_left_x, top + inset_y, right - inset_right_x, bottom - inset_y))


def _key_chroma_pixels(image: Image.Image) -> Image.Image:
    output = image.copy()
    source_pixels = image.load()
    output_pixels = output.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, _ = source_pixels[x, y]
            if red >= 110 and blue >= 90 and min(red, blue) - green >= 35:
                output_pixels[x, y] = (0, 0, 0, 0)
    return output


def _remove_chroma_backdrop(
    image: Image.Image, *, key_before_resize: bool = False
) -> Image.Image:
    # New direct-bust sources key before reduction so saturated chroma cannot
    # bleed into their antialiased silhouette during the thumbnail step.
    rgba = image.convert("RGBA")
    if key_before_resize:
        rgba = _key_chroma_pixels(rgba)
    if max(rgba.size) > 420:
        rgba.thumbnail((420, 420), Image.Resampling.LANCZOS)
    return rgba if key_before_resize else _key_chroma_pixels(rgba)


def _ai_portrait(path: Path, asset: AssetManifestEntry, root: Path) -> None:
    source = _grid_cell(_source_image(asset, root), asset)
    subject = _remove_chroma_backdrop(
        source, key_before_resize=asset.processing_version == "lt-ai-portrait-6"
    )
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
    _save(
        _portrait_sheet(
            full_main,
            eye_line=(35, 28, 27, 255),
        ),
        path,
    )


def _verify_processed_hash(path: Path, asset: AssetManifestEntry) -> None:
    if not asset.output_hash:
        return
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != asset.output_hash:
        raise ValueError(
            f"asset {asset.id} output hash mismatch: {actual_hash} != {asset.output_hash}"
        )

def _ai_title_logo(
    path: Path,
    asset: AssetManifestEntry,
    root: Path,
    campaign_title: str,
) -> None:
    source = _source_image(asset, root)
    bounds = source.getbbox()
    if not bounds:
        raise ValueError(f"asset {asset.id} source has no visible pixels")
    emblem = source.crop(bounds)
    emblem.thumbnail((32, 32), Image.Resampling.LANCZOS)
    logical = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    logical.alpha_composite(
        emblem,
        ((logical.width - emblem.width) // 2, (logical.height - emblem.height) // 2),
    )
    emblem = _quantize_rgba(logical, colors=16).resize(
        (64, 64), Image.Resampling.NEAREST
    )

    image = Image.new("RGBA", (220, 72), (0, 0, 0, 0))
    image.alpha_composite(emblem, (0, 4))
    lettering = _title_logo_image(campaign_title)
    lettering_bounds = lettering.getbbox()
    if lettering_bounds:
        wordmark = ImageOps.contain(
            lettering.crop(lettering_bounds),
            (154, 20),
            method=Image.Resampling.NEAREST,
        )
        image.alpha_composite(wordmark, (64, 26))
    _save(_quantize_rgba(image), path)


def _campaign_ui_sprite(
    path: Path,
    asset_id: str,
    campaign_title: str,
    weapon_types: list[str],
    items,
) -> None:
    if asset_id == "title_logo":
        image = _title_logo_image(campaign_title)
    elif asset_id == "press_start":
        image = _press_start_image()
    elif asset_id == "pennant_bg":
        image = Image.new("RGBA", (240, 16), (30, 34, 42, 244))
        draw = ImageDraw.Draw(image)
        draw.line((0, 0, 239, 0), fill=(224, 216, 184, 255), width=1)
        draw.line((0, 1, 239, 1), fill=(92, 100, 112, 255), width=1)
        for x in range(0, 240, 16):
            draw.line((x, 2, x + 8, 15), fill=(38, 43, 52, 255), width=1)
    elif asset_id == "wexp_icons":
        image = Image.new("RGBA", (16 * len(weapon_types), 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        for index, weapon_type in enumerate(weapon_types):
            digest = hashlib.sha256(weapon_type.encode("utf-8")).digest()
            x = index * 16
            color = tuple(88 + value % 104 for value in digest[:3]) + (255,)
            draw.rounded_rectangle(
                (x + 1, 1, x + 14, 14),
                radius=3,
                fill=color,
                outline=(24, 29, 38, 255),
                width=1,
            )
            label = weapon_type[0].upper()
            label_x = x + 8 - round(draw.textlength(label, font=font) / 2)
            draw.text(
                (label_x + 1, 4),
                label,
                fill=(24, 29, 38, 255),
                font=font,
            )
            draw.text((label_x, 3), label, fill=(248, 248, 232, 255), font=font)
    elif asset_id == "item_icons":
        image = Image.new("RGBA", (16 * len(items), 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        ink = (31, 25, 25, 255)
        steel = (184, 196, 201, 255)
        steel_light = (235, 241, 231, 255)
        oak = (151, 91, 43, 255)
        oak_light = (218, 151, 72, 255)
        herb = (71, 132, 63, 255)
        cloth = (220, 211, 184, 255)
        water = (80, 155, 208, 255)
        for index, item in enumerate(items):
            x = index * 16
            if item.weapon_type == "Bow":
                draw.arc((x + 2, 1, x + 12, 14), 270, 90, fill=oak_light, width=2)
                draw.line((x + 7, 1, x + 7, 14), fill=cloth, width=1)
                draw.line((x + 5, 8, x + 14, 8), fill=steel_light, width=1)
                draw.polygon(
                    ((x + 14, 8), (x + 11, 6), (x + 11, 10)),
                    fill=steel,
                )
            elif item.weapon_type == "Magic":
                draw.ellipse((x + 3, 2, x + 13, 12), fill=water)
                draw.ellipse((x + 6, 4, x + 9, 7), fill=steel_light)
                if "lightning" in item.id:
                    draw.line((x + 7, 12, x + 5, 15), fill=steel_light)
                    draw.line((x + 5, 15, x + 11, 12), fill=steel_light)
                else:
                    draw.line((x + 2, 13, x + 12, 13), fill=water)
                    draw.line((x + 5, 15, x + 14, 15), fill=water)
            elif item.kind == "weapon":
                draw.line((x + 3, 13, x + 12, 3), fill=steel_light, width=2)
                draw.line((x + 2, 11, x + 6, 15), fill=oak, width=2)
                draw.line((x + 5, 10, x + 9, 14), fill=steel, width=1)
            elif item.kind == "healing_spell":
                # A channeled mend shares the weave orb, not the herb pouch.
                draw.ellipse((x + 3, 2, x + 13, 12), fill=cloth, outline=herb)
                draw.rectangle((x + 7, 4, x + 9, 10), fill=herb)
                draw.rectangle((x + 5, 6, x + 11, 8), fill=herb)
            elif item.kind == "healing":
                draw.rectangle((x + 5, 4, x + 11, 13), fill=cloth, outline=ink)
                draw.rectangle((x + 7, 1, x + 9, 4), fill=oak_light, outline=ink)
                draw.rectangle((x + 7, 6, x + 9, 11), fill=herb)
                draw.rectangle((x + 5, 8, x + 11, 9), fill=herb)
            elif "water" in item.id:
                draw.polygon(
                    ((x + 5, 3), (x + 10, 3), (x + 12, 7), (x + 10, 14), (x + 5, 14), (x + 3, 7)),
                    fill=water,
                    outline=ink,
                )
                draw.line((x + 5, 8, x + 10, 8), fill=steel_light)
            else:
                draw.rounded_rectangle(
                    (x + 2, 3, x + 13, 13),
                    radius=2,
                    fill=cloth,
                    outline=ink,
                )
                draw.line((x + 3, 6, x + 12, 10), fill=oak, width=1)
                draw.line((x + 4, 12, x + 11, 4), fill=herb, width=1)
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


def _lit_color(color: tuple[int, int, int], lighting: str) -> tuple[int, int, int]:
    if lighting == "night":
        return _mix_color(color, (18, 29, 52), 0.54)
    if lighting == "firelit":
        return _mix_color(color, (49, 30, 31), 0.48)
    return color


class _HousePalette(NamedTuple):
    roof: tuple[int, int, int, int]
    roof_light: tuple[int, int, int, int]
    roof_shadow: tuple[int, int, int, int]
    roof_deep: tuple[int, int, int, int]
    wall: tuple[int, int, int, int]
    timber: tuple[int, int, int, int]


def _house_palette(lighting: str, occupied: bool) -> _HousePalette:
    roof_rgb = _lit_color((142, 79, 50) if occupied else (93, 81, 70), lighting)
    wall_rgb = _lit_color((171, 139, 91) if occupied else (118, 106, 88), lighting)
    return _HousePalette(
        roof=roof_rgb + (255,),
        roof_light=_shift_color(roof_rgb, 24),
        roof_shadow=_shift_color(roof_rgb, -28),
        roof_deep=_shift_color(roof_rgb, -52),
        wall=wall_rgb + (255,),
        timber=_lit_color((78, 50, 37), lighting) + (255,),
    )


def _draw_house_ground_floor(draw: ImageDraw.ImageDraw, palette: _HousePalette) -> None:
    """Timber-framed ground floor: eave band, corner posts, sill.

    Every tile in the bottom row of an Emond's Field building starts here, so a
    door tile lines up with the wall it is cut from instead of interrupting it.
    """

    draw.rectangle((0, 0, 15, 15), fill=palette.wall)
    draw.rectangle((0, 0, 15, 3), fill=palette.roof_deep)
    draw.line((0, 4, 15, 4), fill=palette.roof_light)
    draw.rectangle((0, 13, 15, 15), fill=palette.timber)
    draw.rectangle((0, 3, 1, 13), fill=palette.timber)
    draw.rectangle((14, 3, 15, 13), fill=palette.timber)


def _draw_house_door(
    draw: ImageDraw.ImageDraw, lighting: str, *, open_door: bool
) -> None:
    """Door cut into an occupied-house ground floor.

    Both states keep the facade shell so the doorway reads as part of the wall.
    Only the leaf changes: the open door shows hearth light and the gold
    threshold that marks a Visit target, the shut one a plain timber leaf.
    Hearth light is emissive, so ambient lighting never dims the marker.
    """

    palette = _house_palette(lighting, occupied=True)
    _draw_house_ground_floor(draw, palette)
    draw.rectangle((3, 5, 12, 15), fill=palette.timber)
    if open_door:
        draw.rectangle((4, 6, 11, 15), fill=_lit_color((30, 25, 25), lighting) + (255,))
        draw.rectangle((4, 11, 11, 15), fill=(126, 77, 38, 255))
        draw.rectangle((4, 13, 11, 15), fill=(244, 200, 80, 255))
        draw.line((3, 15, 12, 15), fill=(244, 200, 80, 255))
    else:
        draw.rectangle((4, 6, 11, 15), fill=_lit_color((176, 116, 60), lighting) + (255,))
        for y in (9, 12):
            draw.line((4, y, 11, y), fill=palette.timber)
        draw.point((10, 10), fill=_lit_color((90, 99, 103), lighting) + (255,))


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
        occupied = entry.terrain_id == "occupied_house"
        palette = _house_palette(lighting, occupied)
        if variant < 2:
            draw.rectangle((0, 0, 15, 15), fill=palette.roof)
            draw.line((0, 1, 15, 1), fill=palette.roof_light)
            draw.line((0, 6, 15, 6), fill=palette.roof_shadow)
            draw.line((0, 11, 15, 11), fill=palette.roof_shadow)
            shingle_offset = 2 if variant == 0 else 7
            for y in (3, 8):
                draw.line(
                    (shingle_offset, y, shingle_offset + 5, y), fill=palette.roof_light
                )
                shingle_offset = (shingle_offset + 7) % 12
            draw.rectangle((0, 13, 15, 15), fill=palette.roof_deep)
            if not occupied:
                missing_x = 3 if variant == 0 else 9
                draw.rectangle((missing_x, 4, missing_x + 3, 7), fill=palette.roof_deep)
                draw.point((missing_x + 4, 8), fill=palette.roof_shadow)
        else:
            _draw_house_ground_floor(draw, palette)
            if variant == 2:
                window = (
                    _lit_color((238, 168, 70), lighting) + (255,)
                    if occupied
                    else _lit_color((48, 43, 41), lighting) + (255,)
                )
                draw.rectangle((4, 6, 11, 12), fill=window, outline=palette.timber)
                draw.line((7, 6, 7, 12), fill=palette.timber)
                draw.line((4, 9, 11, 9), fill=palette.timber)
                if not occupied:
                    draw.line((3, 7, 12, 11), fill=palette.roof_shadow, width=2)
                    draw.line((4, 12, 11, 6), fill=palette.roof_shadow)
            else:
                draw.rectangle((7, 4, 8, 13), fill=palette.timber)
                draw.line((1, 5, 7, 12), fill=palette.roof_shadow)
                draw.line((14, 5, 8, 12), fill=palette.roof_shadow)
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

    if entry.terrain_id in {"house_door", "closed_door"}:
        _draw_house_door(draw, lighting, open_door=entry.terrain_id == "house_door")
    elif entry.visual_style == "doorway":
        timber = _lit_color((105, 63, 39), lighting) + (255,)
        timber_light = _lit_color((176, 116, 60), lighting) + (255,)
        interior = _lit_color((35, 28, 27), lighting) + (255,)
        iron = _lit_color((90, 99, 103), lighting) + (255,)
        gold = _lit_color((244, 200, 80), lighting) + (255,)
        warm_glow = _lit_color((126, 77, 38), lighting) + (255,)
        draw.rectangle((1, 0, 14, 15), fill=interior, outline=gold)
        draw.rectangle((2, 1, 4, 14), fill=timber_light)
        draw.rectangle((11, 1, 13, 14), fill=timber_light)
        draw.rectangle((2, 1, 13, 3), fill=timber)
        draw.rectangle((5, 4, 10, 13), fill=warm_glow)
        draw.polygon(((7, 4), (10, 4), (10, 13), (8, 13)), fill=interior)
        draw.line((1, 14, 14, 14), fill=gold, width=2)
        draw.rectangle((7, 1, 9, 3), fill=gold)
        draw.line((6, 5, 9, 8), fill=iron)
        draw.line((9, 8, 6, 11), fill=iron)
    elif entry.visual_style == "doorstep":
        gold = _lit_color((244, 200, 80), lighting) + (255,)
        warm_glow = _lit_color((126, 77, 38), lighting) + (255,)
        draw.rectangle((0, 0, 15, 15), outline=gold)
        draw.line((1, 1, 14, 1), fill=gold, width=2)
        draw.polygon(
            ((4, 11), (8, 6), (12, 11), (10, 11), (8, 9), (6, 11)),
            fill=warm_glow,
        )
        draw.line((3, 13, 12, 13), fill=gold)

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
                    _draw_campaign_terrain_tile(terrain_entries[terrain_id], lighting, variant),
                    (tile_x * 16, tile_y * 16),
                )
                coordinates[(terrain_id, lighting, variant)] = (tile_x, tile_y)
    _save(image, path)
    return coordinates


# Neighbour bits: 1 = north, 2 = east, 4 = south, 8 = west. This is public
# because the LT adapter must encode path deltas with the same convention.
GUIDE_DIRECTION_BITS = {
    (0, -1): 1,
    (1, 0): 2,
    (0, 1): 4,
    (-1, 0): 8,
}
_GUIDE_DIRECTIONS = {
    bit: (
        8 + dx * (7 if dx > 0 else 8),
        8 + dy * (7 if dy > 0 else 8),
    )
    for (dx, dy), bit in GUIDE_DIRECTION_BITS.items()
}
_GUIDE_ARROWHEADS = {
    1: ((8, 15), (3, 8), (13, 8)),
    2: ((0, 8), (7, 3), (7, 13)),
    4: ((8, 0), (3, 7), (13, 7)),
    8: ((15, 8), (8, 3), (8, 13)),
}
# Cyan guide glyphs: a dark edge beneath a bright core. Public because the
# input playthrough samples these exact colors to prove a guide layer is drawn.
GUIDE_LINE_EDGE = (24, 112, 144, 255)
GUIDE_LINE_CORE = (104, 224, 232, 255)


def _draw_guide_line(draw: ImageDraw.ImageDraw, mask: int) -> None:
    center = (8, 8)
    for color, width in ((GUIDE_LINE_EDGE, 4), (GUIDE_LINE_CORE, 2)):
        for bit, endpoint in _GUIDE_DIRECTIONS.items():
            if mask & bit:
                draw.line((*center, *endpoint), fill=color, width=width)


def _draw_guide_arrow(draw: ImageDraw.ImageDraw, incoming: int) -> None:
    _draw_guide_line(draw, incoming)
    tip, left, right = _GUIDE_ARROWHEADS[incoming]
    draw.polygon((tip, left, right), fill=GUIDE_LINE_EDGE)
    inner = [
        (round((x * 3 + 8) / 4), round((y * 3 + 8) / 4)) for x, y in (tip, left, right)
    ]
    draw.polygon(inner, fill=GUIDE_LINE_CORE)


def _guide_tileset(path: Path) -> dict[GuideTileKey, tuple[int, int]]:
    keys: list[GuideTileKey] = [(mask, False) for mask in range(1, 16)]
    keys += [(incoming, True) for incoming in _GUIDE_DIRECTIONS]
    image = Image.new("RGBA", (16 * len(keys), 16), (0, 0, 0, 0))
    coordinates: dict[GuideTileKey, tuple[int, int]] = {}
    for tile_x, key in enumerate(keys):
        mask, arrowhead = key
        tile = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(tile)
        if arrowhead:
            _draw_guide_arrow(draw, mask)
        else:
            _draw_guide_line(draw, mask)
        image.alpha_composite(tile, (tile_x * 16, 0))
        coordinates[key] = (tile_x, 0)
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

_MAP_SPRITE_PALETTE = (
    _MS_INK,
    _MS_SHADOW,
    _MS_STEEL,
    _MS_STEEL_LIGHT,
    _MS_BROWN,
    _MS_SKIN,
    _MS_WHITE,
    _MS_TEAM_DARK,
    _MS_TEAM_MID,
    _MS_TEAM_LIGHT,
    _MS_TEAM_GLOW,
    _MS_ACCENT,
    _MS_GOLD,
)


@dataclass(frozen=True, slots=True)
class _MapSpriteProfile:
    base: str
    half_width: int
    hair: str
    gear: str


_MAP_SPRITE_PROFILES = {
    # Generic profiles remain available to portable fixture content packs.
    "archer": _MapSpriteProfile("human", 6, "short_brown", "bow"),
    "sword": _MapSpriteProfile("human", 7, "short_dark", "sword"),
    "caster": _MapSpriteProfile("robed", 6, "dark_bob", "staff"),
    "civilian": _MapSpriteProfile("human", 7, "short_brown", "satchel"),
    "beast": _MapSpriteProfile("beast", 10, "horned", "axe"),
    "target": _MapSpriteProfile("target", 0, "none", "none"),
    # Campaign identities. Silhouette, build, hair, and carried gear all matter
    # because team colors change in LT while these identity anchors do not.
    "rand_archer": _MapSpriteProfile("human", 5, "tousled_auburn", "bow"),
    "tam_veteran": _MapSpriteProfile("human", 8, "graying_dark", "veteran_sword"),
    "mat_trickster": _MapSpriteProfile("human", 6, "messy_dark", "scarf_pouch"),
    "perrin_smith": _MapSpriteProfile("human", 9, "curly_dark", "smith_hammer"),
    "egwene_apprentice": _MapSpriteProfile("skirted", 5, "long_braid", "herb_pouch"),
    "moiraine_channeler": _MapSpriteProfile("robed", 5, "dark_bob", "channeling_staff"),
    "lan_warder": _MapSpriteProfile("human", 9, "warder_dark", "warder_sword"),
    "thom_gleeman": _MapSpriteProfile("human", 6, "white_swept", "patch_cloak"),
    "fain_peddler": _MapSpriteProfile("human", 5, "peddler_cap", "merchant_pack"),
    "villager_woman": _MapSpriteProfile("skirted", 6, "long_braid", "apron_basket"),
    "villager_man": _MapSpriteProfile("human", 8, "wool_cap", "satchel"),
    "trolloc_axe": _MapSpriteProfile("beast", 11, "horned", "axe"),
    "trolloc_spear": _MapSpriteProfile("beast", 9, "horned", "spear"),
    "trolloc_wounded": _MapSpriteProfile("beast", 10, "broken_horn", "wounded_axe"),
    # Graybox placeholders for the chapter 6-7 cast (see docs/story-plan-v2.md);
    # replaced by AI identities in the post-graybox art pass.
    "nynaeve_wisdom": _MapSpriteProfile("skirted", 6, "long_braid", "herb_pouch"),
    "bran_mayor": _MapSpriteProfile("human", 9, "wool_cap", "satchel"),
    "luhhan_smith": _MapSpriteProfile("human", 10, "curly_dark", "smith_hammer"),
    "myrddraal_rider": _MapSpriteProfile("human", 7, "warder_dark", "sword"),
    "tam_litter": _MapSpriteProfile("human", 8, "graying_dark", "none"),
    "ewin_boy": _MapSpriteProfile("human", 4, "short_brown", "none"),
    "hunter_bow": _MapSpriteProfile("human", 7, "wool_cap", "bow"),
    "militia_axe": _MapSpriteProfile("human", 9, "short_brown", "smith_hammer"),
    "militia_spear": _MapSpriteProfile("human", 8, "short_dark", "staff"),
}


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

    try:
        profile = _MAP_SPRITE_PROFILES[kind]
    except KeyError as exc:
        raise ValueError(f"unsupported map-sprite profile {kind}") from exc
    if profile.base == "target":
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

    if profile.base == "beast":
        head_x = cx + (3 * side if facing_side else 0)
        horn_tip = baseline - (34 if profile.hair == "horned" else 31)
        left_horn = (
            (head_x - 7, baseline - 24),
            (head_x - 10, horn_tip),
            (head_x - 3, baseline - 28),
        )
        right_horn = (
            (head_x + 7, baseline - 24),
            (head_x + (5 if profile.hair == "broken_horn" else 10), horn_tip + 2),
            (head_x + 3, baseline - 28),
        )
        draw.polygon(left_horn, fill=_MS_BROWN)
        draw.polygon(right_horn, fill=_MS_BROWN)
        draw.ellipse((head_x - 7, baseline - 30, head_x + 7, baseline - 17), fill=_MS_INK)
        draw.rectangle((head_x - 5, baseline - 27, head_x + 5, baseline - 19), fill=_MS_BROWN)
        if not back:
            eye_x = head_x + (3 * side if facing_side else 0)
            draw.point((eye_x, baseline - 25), fill=_MS_GOLD)
            draw.rectangle((head_x - 2, baseline - 20, head_x + 4, baseline - 18), fill=_MS_STEEL)

        half_width = profile.half_width
        shoulder_drop = 2 if profile.gear == "wounded_axe" else 0
        draw.polygon(
            (
                (cx - half_width, baseline - 20 + shoulder_drop),
                (cx - half_width - 3, baseline - 8),
                (cx - 8, baseline - 3),
                (cx + 9, baseline - 3),
                (cx + half_width + 3, baseline - 9 - shoulder_drop),
                (cx + half_width - 1, baseline - 20 - shoulder_drop),
            ),
            fill=_MS_INK,
        )
        draw.polygon(
            (
                (cx - half_width + 3, baseline - 19 + shoulder_drop),
                (cx, baseline - 22),
                (cx + half_width - 2, baseline - 18 - shoulder_drop),
                (cx + 6, baseline - 5),
                (cx - 6, baseline - 5),
            ),
            fill=_MS_TEAM_DARK,
        )
        draw.rectangle((cx - 7, baseline - 15, cx + 7, baseline - 12), fill=_MS_TEAM_MID)
        draw.point((cx - 4, baseline - 14), fill=_MS_TEAM_LIGHT)
        if profile.gear == "wounded_axe":
            draw.line((cx - 8, baseline - 21, cx + 7, baseline - 16), fill=_MS_WHITE, width=2)
            draw.line((head_x - 5, baseline - 22, head_x + 5, baseline - 24), fill=_MS_WHITE)
        draw.line((cx - 6, baseline - 3, cx - 9 - step, baseline + 1), fill=_MS_INK, width=3)
        draw.line((cx + 6, baseline - 3, cx + 9 + step, baseline + 1), fill=_MS_INK, width=3)

        weapon_side = side if facing_side else 1
        if profile.gear == "spear":
            shaft_x = cx + 11 * weapon_side
            draw.line((shaft_x, baseline, shaft_x, baseline - 30), fill=_MS_BROWN, width=2)
            draw.polygon(
                (
                    (shaft_x, baseline - 34),
                    (shaft_x - 3 * weapon_side, baseline - 29),
                    (shaft_x + 3 * weapon_side, baseline - 29),
                ),
                fill=_MS_STEEL_LIGHT,
            )
        else:
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

    head_raise = 2 if kind in {"rand_archer", "lan_warder"} else 0
    head_x = cx + (2 * side if facing_side else 0)
    body_left = cx - profile.half_width
    body_right = cx + profile.half_width

    # Legs and boots go down first so coats, skirts, and robes overlap them.
    if profile.base in {"robed", "skirted"}:
        hem_width = profile.half_width + (4 if profile.base == "robed" else 3)
        draw.polygon(
            (
                (cx - profile.half_width + 1, baseline - 11),
                (cx - hem_width, baseline),
                (cx + hem_width, baseline),
                (cx + profile.half_width - 1, baseline - 11),
            ),
            fill=_MS_TEAM_DARK,
        )
        draw.rectangle(
            (cx - hem_width + 2, baseline - 4, cx + hem_width - 2, baseline - 2),
            fill=_MS_TEAM_LIGHT,
        )
    else:
        draw.line((cx - 3, baseline - 8, cx - 5 - step, baseline), fill=_MS_INK, width=3)
        draw.line((cx + 3, baseline - 8, cx + 5 + step, baseline), fill=_MS_INK, width=3)
        draw.point((cx - 6 - step, baseline), fill=_MS_STEEL)
        draw.point((cx + 6 + step, baseline), fill=_MS_STEEL)

    draw.polygon(
        (
            (body_left, baseline - 20 - head_raise),
            (body_left - 2, baseline - 8),
            (cx, baseline - 5),
            (body_right + 2, baseline - 8),
            (body_right, baseline - 20 - head_raise),
        ),
        fill=_MS_TEAM_DARK,
    )
    draw.rectangle(
        (body_left + 1, baseline - 18 - head_raise, body_right - 1, baseline - 8),
        fill=_MS_TEAM_MID,
    )
    draw.line((cx, baseline - 17 - head_raise, cx, baseline - 8), fill=_MS_TEAM_LIGHT)

    # Character-specific clothing reads before the face at tactical scale.
    if profile.gear == "veteran_sword":
        draw.rectangle(
            (body_left - 1, baseline - 20, body_right + 1, baseline - 16), fill=_MS_STEEL
        )
        draw.line((body_left, baseline - 19, cx, baseline - 13), fill=_MS_STEEL_LIGHT, width=2)
    elif profile.gear == "scarf_pouch":
        draw.rectangle((body_left, baseline - 19, body_right, baseline - 16), fill=_MS_ACCENT)
        draw.rectangle((body_right, baseline - 10, body_right + 4, baseline - 6), fill=_MS_BROWN)
    elif profile.gear == "smith_hammer":
        draw.polygon(
            (
                (cx - 5, baseline - 17),
                (cx + 5, baseline - 17),
                (cx + 7, baseline - 7),
                (cx - 7, baseline - 7),
            ),
            fill=_MS_BROWN,
        )
        draw.point((cx, baseline - 14), fill=_MS_GOLD)
    elif profile.gear in {"herb_pouch", "apron_basket"}:
        draw.rectangle((cx - 5, baseline - 16, cx + 5, baseline - 7), fill=_MS_WHITE)
        draw.line((cx - 4, baseline - 14, cx + 4, baseline - 14), fill=_MS_BROWN)
    elif profile.gear == "channeling_staff":
        draw.line((body_left - 1, baseline - 19, body_right + 1, baseline - 9), fill=_MS_TEAM_GLOW)
        draw.point((cx, baseline - 14), fill=_MS_WHITE)
    elif profile.gear == "warder_sword":
        draw.polygon(
            (
                (body_left - 3, baseline - 21),
                (cx, baseline - 18),
                (body_right + 3, baseline - 21),
                (body_right + 1, baseline - 14),
                (body_left - 1, baseline - 14),
            ),
            fill=_MS_SHADOW,
        )
        draw.rectangle(
            (body_left - 1, baseline - 19, body_right + 1, baseline - 17), fill=_MS_STEEL
        )
    elif profile.gear == "patch_cloak":
        draw.rectangle((body_left - 2, baseline - 19, cx - 1, baseline - 14), fill=_MS_ACCENT)
        draw.rectangle((cx, baseline - 14, body_right + 2, baseline - 9), fill=_MS_GOLD)
        draw.rectangle((body_left, baseline - 9, cx + 1, baseline - 6), fill=_MS_WHITE)
    elif profile.gear == "merchant_pack":
        pack_side = -side if facing_side else -1
        pack_x = cx + (profile.half_width + 3) * pack_side
        draw.rectangle((pack_x - 4, baseline - 21, pack_x + 4, baseline - 7), fill=_MS_BROWN)
        draw.line((pack_x - 3, baseline - 16, pack_x + 3, baseline - 16), fill=_MS_GOLD)
    elif profile.gear == "satchel":
        draw.line((body_left, baseline - 18, body_right, baseline - 8), fill=_MS_BROWN)
        draw.rectangle(
            (body_right - 1, baseline - 10, body_right + 4, baseline - 6), fill=_MS_BROWN
        )

    # Head and hair use deliberately different profiles for the named cast.
    head_top = baseline - 31 - head_raise
    head_bottom = baseline - 19 - head_raise
    draw.ellipse((head_x - 5, head_top + 2, head_x + 5, head_bottom), fill=_MS_INK)
    draw.rectangle((head_x - 4, head_top + 4, head_x + 4, head_bottom - 1), fill=_MS_SKIN)
    hair_top = head_top
    if profile.hair == "tousled_auburn":
        draw.polygon(
            (
                (head_x - 5, head_top + 6),
                (head_x - 3, hair_top),
                (head_x, hair_top + 1),
                (head_x + 2, hair_top),
                (head_x + 6, head_top + 4),
            ),
            fill=_MS_BROWN,
        )
    elif profile.hair == "graying_dark":
        draw.rectangle((head_x - 5, hair_top, head_x + 5, head_top + 4), fill=_MS_SHADOW)
        draw.line((head_x - 3, hair_top, head_x + 1, hair_top), fill=_MS_STEEL_LIGHT)
    elif profile.hair == "messy_dark":
        draw.polygon(
            (
                (head_x - 6, head_top + 5),
                (head_x - 4, hair_top),
                (head_x - 1, hair_top + 2),
                (head_x + 2, hair_top - 1),
                (head_x + 6, head_top + 5),
            ),
            fill=_MS_INK,
        )
    elif profile.hair == "curly_dark":
        draw.ellipse((head_x - 6, hair_top - 1, head_x + 6, head_top + 6), fill=_MS_INK)
        draw.rectangle((head_x - 4, head_top + 4, head_x + 4, head_top + 7), fill=_MS_SKIN)
    elif profile.hair == "long_braid":
        draw.rectangle((head_x - 5, hair_top, head_x + 5, head_top + 4), fill=_MS_BROWN)
        braid_side = -side if facing_side else -1
        braid_x = head_x + 5 * braid_side
        draw.line(
            (braid_x, head_top + 4, braid_x + braid_side, baseline - 12), fill=_MS_BROWN, width=2
        )
        draw.point((braid_x + braid_side, baseline - 11), fill=_MS_GOLD)
    elif profile.hair == "dark_bob":
        draw.rectangle((head_x - 6, hair_top, head_x + 6, head_top + 5), fill=_MS_INK)
        draw.line((head_x - 6, head_top + 3, head_x - 6, head_bottom), fill=_MS_INK, width=2)
        draw.line((head_x + 6, head_top + 3, head_x + 6, head_bottom), fill=_MS_INK, width=2)
    elif profile.hair == "warder_dark":
        draw.polygon(
            (
                (head_x - 6, head_top + 4),
                (head_x - 4, hair_top),
                (head_x + 6, hair_top),
                (head_x + 5, head_top + 6),
            ),
            fill=_MS_INK,
        )
        draw.line((head_x - 5, head_top + 1, head_x + 5, head_top + 1), fill=_MS_SHADOW)
    elif profile.hair == "white_swept":
        draw.polygon(
            (
                (head_x - 6, head_top + 5),
                (head_x - 4, hair_top),
                (head_x + 3, hair_top - 1),
                (head_x + 7, head_top + 2),
            ),
            fill=_MS_WHITE,
        )
        if not back:
            draw.line((head_x - 4, head_bottom - 1, head_x + 4, head_bottom - 1), fill=_MS_WHITE)
    elif profile.hair in {"peddler_cap", "wool_cap"}:
        cap_color = _MS_SHADOW if profile.hair == "peddler_cap" else _MS_BROWN
        draw.ellipse((head_x - 6, hair_top - 1, head_x + 6, head_top + 4), fill=cap_color)
        brim_side = side if facing_side else 1
        draw.line(
            (head_x, head_top + 3, head_x + 8 * brim_side, head_top + 3), fill=cap_color, width=2
        )
    else:
        hair_color = _MS_BROWN if profile.hair == "short_brown" else _MS_INK
        draw.rectangle((head_x - 5, hair_top, head_x + 5, head_top + 4), fill=hair_color)
        draw.point((head_x - 5, head_top + 5), fill=hair_color)
    if back:
        if profile.hair in {"tousled_auburn", "long_braid", "short_brown", "wool_cap"}:
            back_hair = _MS_BROWN
        elif profile.hair == "white_swept":
            back_hair = _MS_WHITE
        elif profile.hair in {"graying_dark", "peddler_cap"}:
            back_hair = _MS_SHADOW
        else:
            back_hair = _MS_INK
        draw.rectangle(
            (head_x - 4, head_top + 4, head_x + 4, head_bottom - 1),
            fill=back_hair,
        )

    if not back:
        eye_x = head_x + (3 * side if facing_side else 0)
        draw.point((eye_x, head_top + 7), fill=_MS_INK)

    gear_side = side if facing_side else 1
    if profile.gear in {"sword", "veteran_sword", "warder_sword"}:
        tip_y = baseline - (
            34 if active and profile.gear == "warder_sword" else 33 if active else 29
        )
        draw.line(
            (cx + 6 * gear_side, baseline - 10, cx + 13 * gear_side, tip_y),
            fill=_MS_WHITE,
            width=2,
        )
        draw.point((cx + 13 * gear_side, tip_y), fill=_MS_GOLD)
    elif profile.gear == "bow":
        bow_x = cx + (8 * side if facing_side else 9)
        draw.arc(
            (bow_x - 5, baseline - 25, bow_x + 5, baseline - 4), 80, 280, fill=_MS_BROWN, width=2
        )
        draw.line((bow_x, baseline - 24, bow_x, baseline - 5), fill=_MS_WHITE)
        draw.line((cx - 8, baseline - 21, cx - 8, baseline - 7), fill=_MS_BROWN, width=2)
        draw.point((cx - 9, baseline - 22), fill=_MS_WHITE)
    elif profile.gear in {"staff", "channeling_staff"}:
        staff_side = side if facing_side else -1
        staff_x = cx + 9 * staff_side
        draw.line((staff_x, baseline - 23, staff_x, baseline), fill=_MS_BROWN, width=2)
        draw.point((staff_x, baseline - 26), fill=_MS_TEAM_GLOW)
        if active or profile.gear == "channeling_staff":
            draw.point((staff_x - 2, baseline - 28), fill=_MS_GOLD)
            draw.point((staff_x + 3, baseline - 25), fill=_MS_WHITE)
            draw.point((staff_x - 3, baseline - 23), fill=_MS_TEAM_LIGHT)
    elif profile.gear == "smith_hammer":
        hammer_x = cx + 10 * gear_side
        draw.line((hammer_x, baseline - 5, hammer_x, baseline - 26), fill=_MS_BROWN, width=2)
        draw.rectangle((hammer_x - 5, baseline - 29, hammer_x + 5, baseline - 25), fill=_MS_STEEL)
    elif profile.gear == "apron_basket":
        basket_x = cx + 10 * gear_side
        draw.rectangle((basket_x - 4, baseline - 12, basket_x + 4, baseline - 5), fill=_MS_BROWN)
        draw.arc((basket_x - 4, baseline - 16, basket_x + 4, baseline - 7), 180, 360, fill=_MS_GOLD)
    elif profile.gear == "patch_cloak":
        flute_x = cx + 9 * gear_side
        draw.line(
            (flute_x, baseline - 18, flute_x + 4 * gear_side, baseline - 8), fill=_MS_WHITE, width=2
        )
    elif profile.gear == "merchant_pack":
        staff_x = cx + 10 * gear_side
        draw.line((staff_x, baseline - 24, staff_x, baseline), fill=_MS_BROWN, width=2)


def _remove_map_sprite_chroma(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, _ = pixels[x, y]
            if red >= 160 and blue >= 150 and green <= 145 and min(red, blue) - green >= 45:
                pixels[x, y] = (0, 0, 0, 0)
    return rgba



def _reduce_map_sprite(
    image: Image.Image, *, maximum_colors: int | None = 8
) -> Image.Image:
    """Map source art to LT colors while preserving the requested cluster budget."""

    rgba = image.convert("RGBA")

    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        relative_y = y / max(1, height - 1)
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha < 128:
                pixels[x, y] = (0, 0, 0, 0)
                continue

            brightness = (red + green + blue) / 3
            source_red = red > 160 and green < 60 and blue < 80
            central = abs(x - (width - 1) / 2) <= width * 0.31
            warm = red > blue * 1.18 and red >= green * 1.05
            source_blue = blue > red * 1.08
            skin = red > 190 and green > 135 and blue < 180

            if brightness < 32:
                color = _MS_INK
            elif skin:
                color = _MS_SKIN
            elif source_red:
                color = _MS_ACCENT
            elif relative_y < 0.35:
                if warm and brightness > 55:
                    color = _MS_BROWN
                elif brightness > 155:
                    color = _MS_WHITE
                elif brightness > 85:
                    color = _MS_STEEL_LIGHT
                else:
                    color = _MS_INK
            elif relative_y < 0.73 and central:
                if brightness < 58:
                    color = _MS_TEAM_DARK
                elif brightness < 95:
                    color = _MS_TEAM_MID
                elif brightness < 145:
                    color = _MS_TEAM_LIGHT
                else:
                    color = _MS_TEAM_GLOW
            elif source_blue:
                color = _MS_TEAM_LIGHT if brightness > 110 else _MS_TEAM_MID
            elif warm:
                color = _MS_GOLD if brightness > 145 and not central else _MS_BROWN
            else:
                color = min(
                    _MAP_SPRITE_PALETTE,
                    key=lambda candidate: sum(
                        (value - target) ** 2
                        for value, target in zip(
                            (red, green, blue), candidate[:3], strict=True
                        )
                    ),
                )
            pixels[x, y] = color
    if maximum_colors:
        return _limit_map_sprite_subject_palette(rgba, maximum_colors=maximum_colors)
    return rgba


def _limit_map_sprite_subject_palette(
    image: Image.Image, *, maximum_colors: int = 8
) -> Image.Image:
    """Keep each tiny unit readable within the project's compact color budget."""

    rgba = image.convert("RGBA")
    counts: dict[tuple[int, int, int, int], int] = {}
    for color in rgba.getdata():
        if color[3] >= 128:
            counts[color] = counts.get(color, 0) + 1
    if len(counts) <= maximum_colors:
        return rgba

    team_colors = {_MS_TEAM_DARK, _MS_TEAM_MID, _MS_TEAM_LIGHT, _MS_TEAM_GLOW}
    retained = [color for color in counts if color in team_colors or color == _MS_INK]
    retained.extend(
        color
        for color, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if color not in retained
    )
    retained = retained[:maximum_colors]

    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            color = pixels[x, y]
            if color[3] < 128 or color in retained:
                continue
            pixels[x, y] = min(
                retained,
                key=lambda candidate: sum(
                    (value - target) ** 2
                    for value, target in zip(color[:3], candidate[:3], strict=True)
                ),
            )
    return rgba

def _direct_grid_map_sprite_frames(
    asset: AssetManifestEntry, root: Path
) -> list[Image.Image]:
    source = _source_image(asset, root).convert("RGB")
    if source.size != (1024, 256):
        raise ValueError(
            f"direct-grid map-sprite source {asset.id} must be 1024x256, got {source.size}"
        )

    logical = source.resize((128, 32), Image.Resampling.NEAREST)
    reconstructed = logical.resize(source.size, Image.Resampling.NEAREST)
    if reconstructed.tobytes() != source.tobytes():
        raise ValueError(
            f"direct-grid map-sprite source {asset.id} is not an exact 8x pixel enlargement"
        )

    frames: list[Image.Image] = []
    for column in range(4):
        cell = _remove_map_sprite_chroma(logical.crop((column * 32, 0, (column + 1) * 32, 32)))
        bounds = cell.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError(f"direct-grid map-sprite source {asset.id} column {column} is empty")
        subject = cell.crop(bounds)
        frames.append(_reduce_map_sprite(subject, maximum_colors=None))
    return frames






def _ai_map_sprite_frames(asset: AssetManifestEntry, root: Path) -> list[Image.Image]:
    if asset.processing_version == "lt-direct-grid-sprite-1":
        return _direct_grid_map_sprite_frames(asset, root)

    source = _source_image(asset, root)
    if source.width % 4 or source.width < 4 or source.height < 1:
        raise ValueError(f"map-sprite source {asset.id} must contain four equal columns")

    cell_width = source.width // 4
    maximum_height = 20 if "trolloc" in asset.subject_id else 18
    maximum_width = 24 if "trolloc" in asset.subject_id else 18
    frames: list[Image.Image] = []
    for column in range(4):
        cell = _remove_map_sprite_chroma(
            source.crop((column * cell_width, 0, (column + 1) * cell_width, source.height))
        )
        bounds = cell.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError(f"map-sprite source {asset.id} column {column} is empty")
        left, top, right, bottom = bounds
        subject = cell.crop(
            (
                max(0, left - 2),
                max(0, top - 2),
                min(cell.width, right + 2),
                min(cell.height, bottom + 2),
            )
        )
        subject.thumbnail((maximum_width, maximum_height), Image.Resampling.NEAREST)
        frames.append(_reduce_map_sprite(subject))
    return frames


def _composite_map_sprite(
    sheet: Image.Image,
    sprite: Image.Image,
    *,
    cell_x: int,
    cell_y: int,
    cell_width: int,
    cell_height: int,
    offset_x: int = 0,
    offset_y: int = 0,
) -> None:
    x = cell_x + (cell_width - sprite.width) // 2 + offset_x
    y = cell_y + cell_height - 2 - sprite.height + offset_y
    sheet.alpha_composite(sprite, (x, y))


def _ai_map_sprite(
    stand_path: Path,
    move_path: Path,
    asset: AssetManifestEntry,
    root: Path,
) -> None:
    directions = _ai_map_sprite_frames(asset, root)

    move = Image.new("RGBA", (192, 160), COLORKEY)
    move_offsets = ((-1, 0), (0, -1), (1, 0), (0, 0))
    for row, sprite in enumerate(directions):
        for column, (offset_x, offset_y) in enumerate(move_offsets):
            _composite_map_sprite(
                move,
                sprite,
                cell_x=column * 48,
                cell_y=row * 40,
                cell_width=48,
                cell_height=40,
                offset_x=offset_x,
                offset_y=offset_y,
            )

    stand = Image.new("RGBA", (192, 144), COLORKEY)
    stand_offsets = ((-1, 0), (0, -1), (1, 0))
    for row in range(3):
        for column, (offset_x, offset_y) in enumerate(stand_offsets):
            _composite_map_sprite(
                stand,
                directions[0],
                cell_x=column * 64,
                cell_y=row * 48,
                cell_width=64,
                cell_height=48,
                offset_x=offset_x,
                offset_y=offset_y - (1 if row == 2 else 0),
            )

    _save(stand, stand_path)
    _save(move, move_path)


def _verify_map_sprite_hashes(
    stand_path: Path,
    move_path: Path,
    asset: AssetManifestEntry,
) -> None:
    for label, path, expected in (
        ("stand", stand_path, asset.stand_output_hash),
        ("move", move_path, asset.move_output_hash),
    ):
        if expected is None:
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(
                f"asset {asset.id} {label} output hash mismatch: {actual} != {expected}"
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


def _level_up_animation(path: Path) -> None:
    """Draw an original four-frame level-up burst sheet (engine 'LevelUpMap').

    The pinned engine dereferences this animation unguarded when any unit
    levels up, so every compiled project must ship one.
    """

    frame_size = 32
    sheet = Image.new("RGBA", (frame_size * 4, frame_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    gold = (248, 248, 64, 255)
    white = (248, 248, 248, 255)
    blue = (144, 184, 232, 255)
    for frame in range(4):
        cx = frame * frame_size + frame_size // 2
        cy = frame_size // 2
        radius = 3 + frame * 3
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            draw.line(
                (cx + dx * 3, cy + dy * 3, cx + dx * radius, cy + dy * radius),
                fill=gold if frame % 2 else white,
                width=2,
            )
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            draw.line(
                (cx + dx * 2, cy + dy * 2, cx + dx * (radius - 1), cy + dy * (radius - 1)),
                fill=blue,
                width=1,
            )
        draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=white if frame < 3 else gold)
    _save(sheet, path)

_MISS_GLYPHS = {
    "M": ("10001", "11011", "10101", "10101", "10001"),
    "I": ("1", "1", "1", "1", "1"),
    "S": ("1111", "1000", "1111", "0001", "1111"),
    "!": ("1", "1", "1", "0", "1"),
}


def _miss_animation(path: Path) -> None:
    frame_width, frame_height = 24, 12
    y_offsets = (4, 3, 2, 2, 3, 4)
    sheet = Image.new(
        "RGBA",
        (frame_width * len(y_offsets), frame_height),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(sheet)
    text = "MISS!"
    glyph_width = sum(len(_MISS_GLYPHS[character][0]) for character in text)
    text_width = glyph_width + len(text) - 1
    for frame, y_offset in enumerate(y_offsets):
        pixels = []
        x = frame * frame_width + (frame_width - text_width) // 2
        for character in text:
            glyph = _MISS_GLYPHS[character]
            for y, row in enumerate(glyph):
                for dx, value in enumerate(row):
                    if value == "1":
                        pixels.append((x + dx, y + y_offset))
            x += len(glyph[0]) + 1
        for px, py in pixels:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                draw.point((px + dx, py + dy), fill=(32, 24, 24, 255))
        for px, py in pixels:
            draw.point((px, py), fill=(248, 240, 208, 255))
    _save(sheet, path)


def _stone_throw_animation(path: Path) -> None:
    frame_size = 32
    positions = ((4, 28), (7, 25), (10, 22), (13, 19), (17, 15), (21, 11))
    sheet = Image.new(
        "RGBA",
        (frame_size * len(positions), frame_size),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(sheet)
    for frame, (x, y) in enumerate(positions):
        x += frame * frame_size
        draw.line((x - 5, y + 5, x - 2, y + 2), fill=(184, 192, 200, 180))
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(40, 32, 32, 255))
        draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=(128, 136, 112, 255))
        draw.point((x, y - 1), fill=(216, 232, 240, 255))
    _save(sheet, path)


def _ball_lightning_animation(path: Path) -> None:
    """Draw an original six-frame ball-lightning sheet (engine 'BallLightning').

    Frames 0-2 drop a blue-white sphere down the target tile, frame 3 is the
    strike, and frames 4-5 fade an arcing burst, so Moiraine's signature weave
    reads as lightning called out of the sky rather than a thrown projectile.
    """
    frame_size, frames = 32, 6
    core = (248, 252, 255, 255)
    glow = (176, 216, 255, 255)
    arc = (96, 144, 232, 255)
    sheet = Image.new("RGBA", (frame_size * frames, frame_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    for frame in range(frames):
        cx = frame * frame_size + frame_size // 2
        if frame < 3:
            cy = 4 + frame * 6
            radius = 3 + frame
            draw.line((cx, 0, cx, cy - radius), fill=arc, width=1)
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=glow)
            draw.ellipse(
                (cx - radius + 2, cy - radius + 2, cx + radius - 2, cy + radius - 2),
                fill=core,
            )
            continue
        cy = frame_size // 2
        spread = 6 + (frame - 3) * 4
        bolt = core if frame == 3 else glow
        for index, (dx, dy) in enumerate(
            ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))
        ):
            # Uneven reach and a sideways kink keep the burst from resolving
            # into an even spoked wheel.
            reach = spread - index % 3
            midx = cx + dx * (reach // 2) + dy * 2
            midy = cy + dy * (reach // 2) - dx * 2
            draw.line((cx + dx * 2, cy + dy * 2, midx, midy), fill=bolt, width=1)
            draw.line((midx, midy, cx + dx * reach, cy + dy * reach), fill=arc, width=1)
        if frame == 3:
            draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=core)
        else:
            draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=glow)
    _save(sheet, path)


def generate_campaign_assets(
    directory: Path, bundle: CampaignBundle, root: Path
) -> CampaignAssetPaths:
    directory.mkdir(parents=True, exist_ok=True)
    font_image = directory / "font.png"
    font_index = directory / "font.idx"
    _font(
        font_image,
        font_index,
        source_font_path=root / "assets/fonts/DepartureMono-Regular.otf",
        font_size=11,
        cell_w=9,
    )

    backgrounds: dict[str, Path] = {}
    portraits: dict[str, Path] = {}
    map_sprites: dict[str, tuple[Path, Path]] = {}
    ui_sprites: dict[str, Path] = {}
    for asset in sorted(bundle.asset_manifest.assets, key=lambda entry: entry.id):
        if asset.approval_status not in {"placeholder", "approved"} and asset.type != "map_sprite":
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
            stand = directory / f"map-{asset.id}-stand.png"
            move = directory / f"map-{asset.id}-move.png"
            if asset.provenance == "ai_generated" and asset.approval_status == "approved":
                _ai_map_sprite(stand, move, asset, root)
                _verify_map_sprite_hashes(stand, move, asset)
            elif (
                asset.provenance == "programmatic_placeholder"
                or asset.approval_status == "pending"
            ):
                _campaign_map_sprite(stand, move, asset.variant)
            else:
                raise ValueError(f"unsupported map-sprite provenance for {asset.id}")
            map_sprites[asset.id] = (stand, move)
        elif asset.type == "ui":
            path = directory / f"ui-{asset.id}.png"
            if asset.provenance in {"ai_generated", "original", "licensed"}:
                if asset.id != "title_logo":
                    raise ValueError(f"unsupported sourced UI asset {asset.id}")
                _ai_title_logo(path, asset, root, bundle.campaign.title)
            else:
                _campaign_ui_sprite(
                    path,
                    asset.id,
                    bundle.campaign.title,
                    bundle.gameplay.weapon_types,
                    bundle.gameplay.items,
                )
            _verify_processed_hash(path, asset)
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
    guide_tileset_id = f"{approved_tilesets[0].id}__guides"
    guide_tileset = directory / "campaign-guide-lines.png"
    guide_tiles = _guide_tileset(guide_tileset)
    level_up_animation = directory / "map-animation-level-up.png"
    _level_up_animation(level_up_animation)
    miss_animation = directory / "map-animation-miss.png"
    _miss_animation(miss_animation)
    stone_throw_animation = directory / "map-animation-stone-throw.png"
    _stone_throw_animation(stone_throw_animation)
    ball_lightning_animation = directory / "map-animation-ball-lightning.png"
    _ball_lightning_animation(ball_lightning_animation)
    return CampaignAssetPaths(
        backgrounds=backgrounds,
        portraits=portraits,
        tileset_id=approved_tilesets[0].id,
        tileset=tileset,
        terrain_tiles=terrain_tiles,
        guide_tileset_id=guide_tileset_id,
        guide_tileset=guide_tileset,
        guide_tiles=guide_tiles,
        map_sprites=map_sprites,
        ui_sprites=ui_sprites,
        font_image=font_image,
        font_index=font_index,
        level_up_animation=level_up_animation,
        miss_animation=miss_animation,
        stone_throw_animation=stone_throw_animation,
        ball_lightning_animation=ball_lightning_animation,
    )
