"""
profile_card.py — CSIA Cyberfox bot: /profile level card feature

Pure helper module (no dependency on the `bot` object) — bot.py imports
`build_profile_card()` and wires it into a slash command itself, the same
way it already talks to attendance_store.py.

Requires Pillow:  pip install Pillow --break-system-packages
(add "Pillow>=10.0.0" to requirements.txt too)

Reads specialization styling and the attendance threshold straight from
config.py, so if you ever change ATTENDANCE_THRESHOLD or add/re-map a
specialization role there, this file picks it up automatically — nothing
to update here.
"""

import io
import discord
from PIL import Image, ImageDraw, ImageFont
import aiohttp

import config
import attendance_store

# ---- Visual configuration -----------------------------------------------

CARD_WIDTH = 900
CARD_HEIGHT = 300

BG_COLOR = (20, 20, 24)        # near-black, matches CSIA dark theme
ACCENT_COLOR = (163, 23, 18)   # CSIA red (#A31712)
TEXT_COLOR = (235, 235, 235)
SUBTEXT_COLOR = (170, 170, 170)
BAR_BG_COLOR = (45, 45, 50)

# Optional: drop real .ttf files here for nicer typography.
# Falls back to Pillow's default bitmap font if missing — won't crash.
FONT_BOLD_PATH = "./assets/fonts/Inter-Bold.ttf"
FONT_REGULAR_PATH = "./assets/fonts/Inter-Regular.ttf"


def _load_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _level_tiers() -> list[tuple[int, str]]:
    """
    Builds level tiers from config.ATTENDANCE_THRESHOLD, so the /profile
    card auto-adjusts if that number ever changes — no separate constant
    to keep in sync.
    """
    threshold = config.ATTENDANCE_THRESHOLD  # currently 3
    return [
        (0, "Newcomer"),
        (1, "Fox in Training"),
        (threshold, "Active Member"),          # matches the real auto-upgrade point
        (threshold * 2, "Veteran Fox"),
        (threshold * 3 + 1, "Alliance Elder"),
    ]


def _level_for_count(count: int) -> tuple[str, int, int | None]:
    """Returns (label, current_tier_floor, next_tier_floor_or_None)."""
    tiers = _level_tiers()
    current_label = tiers[0][1]
    current_floor = 0
    next_floor = None
    for i, (floor, label) in enumerate(tiers):
        if count >= floor:
            current_label = label
            current_floor = floor
            next_floor = tiers[i + 1][0] if i + 1 < len(tiers) else None
    return current_label, current_floor, next_floor


def get_specialization(member: discord.Member) -> tuple[str, tuple[int, int, int]]:
    """Finds the first matching specialization role (by ID) on the member."""
    for role in member.roles:
        style = config.SPECIALIZATION_ROLE_STYLES.get(role.id)
        if style:
            label, hex_color = style
            return label, _hex_to_rgb(hex_color)
    return "Unspecialized", (100, 100, 100)


async def _fetch_avatar_bytes(member: discord.Member) -> bytes:
    url = str(member.display_avatar.replace(size=256).url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


def _circular_avatar(avatar_bytes: bytes, size: int = 200) -> Image.Image:
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((size, size))
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(avatar, (0, 0), mask)
    return result


async def build_profile_card(member: discord.Member) -> discord.File:
    """Builds the PNG card and returns it as a discord.File ready to send."""
    event_count = attendance_store.get_attendance_count(member.id)
    spec_label, spec_color = get_specialization(member)
    level_label, tier_floor, next_floor = _level_for_count(event_count)

    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(card)

    draw.rectangle([(0, 0), (14, CARD_HEIGHT)], fill=ACCENT_COLOR)

    avatar_bytes = await _fetch_avatar_bytes(member)
    avatar_img = _circular_avatar(avatar_bytes, size=200)
    card.paste(avatar_img, (50, 50), avatar_img)
    draw.ellipse((46, 46, 250, 250), outline=spec_color, width=6)

    font_name = _load_font(FONT_BOLD_PATH, 40)
    font_sub = _load_font(FONT_REGULAR_PATH, 24)
    font_label = _load_font(FONT_REGULAR_PATH, 20)

    draw.text((280, 55), member.display_name, font=font_name, fill=TEXT_COLOR)
    draw.text((280, 110), f"Specialization: {spec_label}", font=font_sub, fill=spec_color)
    draw.text((280, 150), f"Level: {level_label}", font=font_sub, fill=TEXT_COLOR)
    draw.text((280, 185), f"Events attended: {event_count}", font=font_label, fill=SUBTEXT_COLOR)

    bar_x, bar_y, bar_w, bar_h = 280, 230, 550, 26
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=13, fill=BAR_BG_COLOR)

    if next_floor is not None:
        span = next_floor - tier_floor
        progress = min(1.0, (event_count - tier_floor) / span) if span > 0 else 1.0
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=13, fill=spec_color)
        draw.text(
            (bar_x, bar_y + bar_h + 6),
            f"{event_count}/{next_floor} events to next level",
            font=font_label, fill=SUBTEXT_COLOR,
        )
    else:
        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=13, fill=spec_color)
        draw.text((bar_x, bar_y + bar_h + 6), "Max level reached", font=font_label, fill=SUBTEXT_COLOR)

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename=f"profile_{member.id}.png")