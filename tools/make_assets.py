#!/usr/bin/env python3
"""Generate the digital card's image assets and refresh the vCard PHOTO field.

    python tools/make_assets.py          regenerate icon.png, og-image.png, contact.vcf PHOTO
    python tools/make_assets.py --check  verify the artefacts on disk, write nothing

Rerun this after replacing Akib_Javed_Photo_Square.png, or after changing a name/title
string below. Pillow only, no other dependency. The assertions at the bottom are the check:
they fail loudly if the framing overflows, the vCard photo is truncated, or the .vcf grows
past the size contact importers tolerate.
"""

from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Akib_Javed_Photo_Square.png"
ICON = ROOT / "icon.png"
OG = ROOT / "og-image.jpg"
VCF = ROOT / "contact.vcf"

# Framing inside the 960x960 cut-out. Keeps the head centred with a little headroom so the
# same crop works as a tab icon, a round avatar, and a vCard thumbnail.
CROP = (100, 0, 860, 760)

NAME = "Akib Javed, PhD"
TITLE_LINES = ("Hydrology &", "Geoinformatics Specialist")
ORG = "C4RE International"

# Palette, lifted from index.html's :root and .avatar-circle.
BG = (11, 17, 32)               # --bg              #0B1120
ACCENT = (14, 165, 233)         # --accent          #0EA5E9
ACCENT_BRIGHT = (56, 189, 248)  # --accent-hover    #38BDF8
MUTED = (148, 163, 184)         # --text-muted      #94A3B8
MAIN = (248, 250, 252)          # --text-main       #F8FAFC
GRAD = ((2, 132, 199), (14, 165, 233), (56, 189, 248))  # 135deg gradient stops

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


def diagonal_gradient(size: int) -> Image.Image:
    """135deg blend of the three avatar stops. A 2x2 corner image resized up is smooth
    enough at these sizes and needs no per-pixel loop."""
    small = Image.new("RGB", (2, 2))
    small.putpixel((0, 0), GRAD[0])
    small.putpixel((1, 0), GRAD[1])
    small.putpixel((0, 1), GRAD[1])
    small.putpixel((1, 1), GRAD[2])
    return small.resize((size, size), Image.Resampling.BILINEAR)


def portrait(size: int) -> Image.Image:
    """The cut-out, cropped and resized to a square, alpha intact."""
    src = Image.open(SOURCE).convert("RGBA").crop(CROP)
    return src.resize((size, size), Image.Resampling.LANCZOS)


def portrait_on_gradient(size: int) -> Image.Image:
    """Opaque square: brand gradient with the portrait over it. Used for the favicon and the
    vCard photo, both of which need something behind a transparent cut-out."""
    base = diagonal_gradient(size).convert("RGBA")
    base.alpha_composite(portrait(size))
    return base.convert("RGB")


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
    portrait_on_gradient(256).save(ICON, "PNG", optimize=True)


def build_og() -> None:
    """Left-hand round portrait, left-aligned text: reads as a business card at thumbnail
    size, and mirrors the page it previews."""
    s = OG_SUPERSAMPLE
    w, h = OG_SIZE[0] * s, OG_SIZE[1] * s
    canvas = Image.new("RGBA", (w, h), BG + (255,))
    glow(canvas, (0, 0), int(w * 0.62), ACCENT, 38)          # rgba(14,165,233,.15)
    glow(canvas, (w, h), int(w * 0.62), ACCENT_BRIGHT, 26)   # rgba(56,189,248,.10)

    disc = diagonal_gradient(340 * s).convert("RGBA")
    disc.alpha_composite(portrait(340 * s))
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
    portrait_on_gradient(PHOTO_PX).save(buf, "JPEG", quality=PHOTO_QUALITY, optimize=True)
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
    build_icon()
    build_og()
    b64 = photo_b64()
    refresh_vcf(b64)
    verify(b64)


if __name__ == "__main__":
    main()
