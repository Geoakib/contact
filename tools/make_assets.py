#!/usr/bin/env python3
"""Generate the digital card's image assets and refresh the vCard PHOTO field.

    python tools/make_assets.py          regenerate icon.png, og-image.jpg, contact.vcf PHOTO
    python tools/make_assets.py --check  verify the artefacts on disk, write nothing

Rerun this after replacing 35-45.jpg, or after changing a name/title string below.
Pillow only, no other dependency. The assertions at the bottom are the check: they fail loudly
if the framing overflows, the vCard photo is truncated, or the .vcf grows past the size that
contact importers tolerate.
"""

from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "35-45.jpg"
ICON = ROOT / "icon.png"
OG = ROOT / "og-image.jpg"
VCF = ROOT / "contact.vcf"

# Square crop of the 413x531 headshot: the top square, nudged down so the hair sits flush to
# the top edge and the beard is not clipped at the bottom. Framed this way the head fills the
# frame at any size, which is what a round avatar, a tab icon and a vCard thumbnail all want.
CROP = (0, 28, 413, 441)

NAME = "Akib Javed, PhD"
TITLE_LINES = ("Hydrology &", "Geoinformatics Specialist")
ORG = "C4RE International"

# Palette, lifted from index.html's :root.
BG = (11, 17, 32)               # --bg              #0B1120
ACCENT = (14, 165, 233)         # --accent          #0EA5E9
ACCENT_BRIGHT = (56, 189, 248)  # --accent-hover    #38BDF8
MUTED = (148, 163, 184)         # --text-muted      #94A3B8
MAIN = (248, 250, 252)          # --text-main       #F8FAFC

FONT_DIR = Path("C:/Windows/Fonts")
FONT_FILES = {
    "bold": ("segoeuib.ttf", "arialbd.ttf"),
    "semibold": ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"),
    "regular": ("segoeui.ttf", "arial.ttf"),
}

OG_SIZE = (1200, 630)
OG_SUPERSAMPLE = 2  # draw at 2x and downscale, so text edges are clean
PHOTO_PX = 200      # vCard PHOTO, square
PHOTO_QUALITY = 88

OG_MAX = 300_000         # WhatsApp silently drops link thumbnails heavier than this
VCF_PHOTO_MAX = 30_000   # base64 chars
VCF_MAX = 40_960         # whole file


def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    for name in FONT_FILES[weight]:
        path = FONT_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise SystemExit(f"make_assets: no usable {weight} font in {FONT_DIR}")


def portrait(size: int) -> Image.Image:
    """The headshot, cropped square and resized. It carries its own white background, so
    there is nothing to composite behind it — unlike the transparent cut-out it replaced."""
    src = Image.open(SOURCE).convert("RGB").crop(CROP)
    return src.resize((size, size), Image.Resampling.LANCZOS)


def glow(canvas: Image.Image, centre: tuple[int, int], radius: int, colour, alpha: int) -> None:
    """Approximate a CSS radial-gradient glow: opaque at `centre`, gone by `radius`."""
    mask = Image.new("L", canvas.size, 0)
    radial = Image.radial_gradient("L")  # black at centre -> white at edge
    radial = radial.resize((radius * 2, radius * 2), Image.Resampling.BICUBIC)
    radial = radial.point(lambda v: (255 - v) * alpha // 255)
    # A low-alpha ramp over ~1500px quantises into visible bands; ~1 level of noise dithers
    # them away and costs nothing.
    radial = ImageChops.add(radial, Image.effect_noise(radial.size, 8).point(lambda v: (v - 128) // 3))
    mask.paste(radial, (centre[0] - radius, centre[1] - radius))  # paste clips at the edges
    layer = Image.new("RGBA", canvas.size, tuple(colour) + (255,))
    layer.putalpha(mask)
    canvas.alpha_composite(layer)


def build_icon() -> None:
    portrait(256).save(ICON, "PNG", optimize=True)


def build_og() -> None:
    """Left-hand round portrait, left-aligned text: reads as a business card at thumbnail
    size, and mirrors the page it previews."""
    s = OG_SUPERSAMPLE
    w, h = OG_SIZE[0] * s, OG_SIZE[1] * s
    canvas = Image.new("RGBA", (w, h), BG + (255,))
    glow(canvas, (0, 0), int(w * 0.62), ACCENT, 38)          # rgba(14,165,233,.15)
    glow(canvas, (w, h), int(w * 0.62), ACCENT_BRIGHT, 26)   # rgba(56,189,248,.10)

    disc = portrait(340 * s).convert("RGBA")
    circle = Image.new("L", disc.size, 0)
    ImageDraw.Draw(circle).ellipse((0, 0, disc.size[0] - 1, disc.size[1] - 1), fill=255)
    disc.putalpha(circle)
    canvas.alpha_composite(disc, (110 * s, (h - disc.size[1]) // 2))

    draw = ImageDraw.Draw(canvas)
    x = 520 * s
    right = w - 40 * s  # keep this much clear on the right

    def text(y: int, body: str, weight: str, size: int, fill, label: str) -> None:
        f = font(weight, size * s)
        width = draw.textlength(body, font=f)
        if x + width > right:
            raise SystemExit(
                f"make_assets: og text overflows by {int((x + width - right) / s)}px "
                f"({label} at {size}px) — shorten it or drop the size"
            )
        draw.text((x, y * s), body, font=f, fill=fill, anchor="lm")

    text(240, NAME, "bold", 78, MAIN, "name")
    draw.rectangle((x, 305 * s, x + 140 * s, 311 * s), fill=ACCENT)
    for i, line in enumerate(TITLE_LINES):
        text(375 + i * 57, line, "semibold", 44, ACCENT_BRIGHT, f"title line {i + 1}")
    text(505, ORG, "regular", 40, MUTED, "org")

    # JPEG, not PNG: the same picture is ~half the bytes, which matters because WhatsApp
    # drops link thumbnails it deems too heavy.
    canvas.convert("RGB").resize(OG_SIZE, Image.Resampling.LANCZOS).save(
        OG, "JPEG", quality=90, optimize=True, progressive=True
    )


def photo_b64() -> str:
    buf = io.BytesIO()
    portrait(PHOTO_PX).save(buf, "JPEG", quality=PHOTO_QUALITY, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def refresh_vcf(b64: str) -> int:
    """Rewrite the PHOTO line. Reads bytes, not text: read_text() normalises CRLF to LF, and
    a vCard is supposed to keep CRLF (RFC 2426), so line endings are captured before decoding
    and restored on the way out."""
    raw_bytes = VCF.read_bytes()
    nl = "\r\n" if b"\r\n" in raw_bytes else "\n"
    raw = raw_bytes.decode("utf-8").replace("\r\n", "\n")
    line = f"PHOTO;ENCODING=b;TYPE=JPEG:{b64}"
    if re.search(r"^PHOTO;[^\n]*$", raw, re.M):
        out = re.sub(r"^PHOTO;[^\n]*$", lambda _: line, raw, count=1, flags=re.M)
    else:
        # Insert before END:VCARD, where every importer expects it.
        out = raw.replace("\nEND:VCARD", f"\n{line}\nEND:VCARD", 1)
    data = out.replace("\n", nl).encode("utf-8")
    VCF.write_bytes(data)
    return len(data)


def verify(b64: str | None = None) -> None:
    """The check. Fails if the framing overflowed, the photo got truncated, or the vCard
    is too big for contact importers (Outlook is the tightest)."""
    for path, size in ((ICON, (256, 256)), (OG, OG_SIZE)):
        with Image.open(path) as im:
            assert im.size == size, f"{path.name} is {im.size}, expected {size}"
    og_bytes = OG.stat().st_size
    assert og_bytes <= OG_MAX, f"og-image is {og_bytes:,}B, over the {OG_MAX:,}B crawler limit"

    raw = VCF.read_text(encoding="utf-8")
    assert raw.count("BEGIN:VCARD") == 1 and raw.count("END:VCARD") == 1, "unbalanced vCard"
    assert "VERSION:3.0" in raw, "vCard version changed"
    assert "X-ABLabel" not in raw and "item1." not in raw, "Apple-only label groups returned"
    assert "UID:" in raw, "no UID: re-importing will duplicate the contact"
    assert "https://geoakib.github.io/contact/" in raw, "card URL missing from the vCard"

    m = re.search(r"^PHOTO;ENCODING=b;TYPE=JPEG:(\S+)$", raw, re.M)
    assert m, "no PHOTO field"
    encoded = m.group(1)
    if b64 is not None:
        assert encoded == b64, "PHOTO does not match the current photo pipeline"
    with Image.open(io.BytesIO(base64.b64decode(encoded, validate=True))) as im:
        assert im.format == "JPEG", f"PHOTO is {im.format}, not JPEG"
        assert im.size == (PHOTO_PX, PHOTO_PX), f"PHOTO is {im.size}, expected {PHOTO_PX} square"

    size = len(raw.encode("utf-8"))
    assert len(encoded) <= VCF_PHOTO_MAX, f"PHOTO base64 is {len(encoded)} chars"
    assert size <= VCF_MAX, f"contact.vcf is {size} bytes"
    print(
        f"ok  icon.png {ICON.stat().st_size:,}B  {OG.name} {OG.stat().st_size:,}B  "
        f"photo {len(encoded):,}B b64  contact.vcf {size:,}B"
    )


def main() -> None:
    if "--check" in sys.argv:
        verify()
        return
    if not SOURCE.exists():
        raise SystemExit(f"make_assets: missing source photo {SOURCE}")
    with Image.open(SOURCE) as src:
        # A replaced photo is the likeliest way CROP silently goes wrong: it would crop the
        # wrong region or paste a short image into a long box instead of failing.
        assert src.size[0] >= CROP[2] and src.size[1] >= CROP[3], (
            f"make_assets: crop {CROP} does not fit {SOURCE.name} {src.size} — adjust CROP"
        )
    build_icon()
    build_og()
    b64 = photo_b64()
    refresh_vcf(b64)
    verify(b64)


if __name__ == "__main__":
    main()
