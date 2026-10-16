"""Compose Chrome Web Store screenshots (1280x800) from raw captures.

    pip install pillow   # dev only; not a Kavach dependency
    python scripts/make_store_screenshots.py <captures-dir>

Each output places one capture, scaled to fit, under a short caption on a
dark background. Captures must contain made-up data only; crops below remove
anything personal (for example a chat sidebar with real conversation titles).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "extension" / "store" / "screenshots"
W, H = 1280, 800
BG = (13, 17, 23)
CAPTION = (230, 237, 243)
SUBTLE = (145, 152, 161)
ACCENT = (68, 147, 248)
FONT_DIR = Path("C:/Windows/Fonts")

# (output name, capture file, crop box as fractions (l, t, r, b) or None, caption, subcaption)
SHOTS = [
    (
        "1-paste-warning.png",
        "26.png",
        None,
        "Warns before personal details reach an AI chat",
        "Aadhaar, PAN, UPI, IFSC, bank account, phone, GSTIN and email",
    ),
    (
        "2-masked.png",
        "27.png",
        None,
        "Mask swaps them for placeholders",
        "A one-line note tells the AI to keep them as they are",
    ),
    (
        "3-claude-hinglish.png",
        "29.png",
        (0.21, 0.0, 1.0, 1.0),  # drop the sidebar: it shows personal chat titles and a name
        "Works on ChatGPT, Claude and Gemini",
        "Understands English, Hinglish and Hindi",
    ),
    (
        "4-ai-keeps-placeholders.png",
        "37.png",
        None,
        "The AI helps without ever seeing the real values",
        "Placeholders come back untouched in its reply",
    ),
    (
        "5-popup.png",
        "38.png",
        (0.7023, 0.047, 0.9613, 0.6858),  # just the popup, not the chat behind it

        "Runs entirely on your device",
        "No network requests. Stores only on/off switches and counts.",
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for name in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        path = FONT_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size)


def compose(capture: Image.Image, caption: str, sub: str) -> Image.Image:
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    title_font, sub_font = font(40, bold=True), font(22)
    draw.rectangle((0, 0, W, 6), fill=ACCENT)
    draw.text((W // 2, 62), caption, font=title_font, fill=CAPTION, anchor="mm")
    draw.text((W // 2, 108), sub, font=sub_font, fill=SUBTLE, anchor="mm")

    top, margin = 142, 40
    box_w, box_h = W - 2 * margin, H - top - margin
    scale = min(box_w / capture.width, box_h / capture.height, 1.6)
    size = (round(capture.width * scale), round(capture.height * scale))
    shot = capture.convert("RGB").resize(size, Image.LANCZOS)

    x, y = (W - size[0]) // 2, top + (box_h - size[1]) // 2
    draw.rounded_rectangle((x - 2, y - 2, x + size[0] + 1, y + size[1] + 1), radius=10, outline=(61, 68, 77), width=2)
    canvas.paste(shot, (x, y))
    return canvas


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    source = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    for name, file, crop, caption, sub in SHOTS:
        capture = Image.open(source / file)
        if crop:
            l, t, r, b = crop
            capture = capture.crop(
                (round(l * capture.width), round(t * capture.height), round(r * capture.width), round(b * capture.height))
            )
        compose(capture, caption, sub).save(OUT / name, optimize=True)
        print(f"wrote extension/store/screenshots/{name}")


if __name__ == "__main__":
    main()
