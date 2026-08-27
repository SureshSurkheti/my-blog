"""Draw static/favicon-source.png, the artwork every site icon is cut from.

Run from the project root, then regenerate the sizes:

    .venv/bin/python scripts/make_icon_source.py
    .venv/bin/python scripts/make_favicon.py

The mark is drawn from a font rather than traced from an existing PNG, because
the icons this replaced had been through at least one downscale and the letter
had gone soft — visible as fuzz on the 512px file long before anyone looked at
a tab.

Two things here are deliberate and easy to undo wrongly:

* The letter is centred on its own ink, not on the font's line box. Ascender
  and descender space is not the same above and below a capital S, so centring
  the text box leaves the glyph sitting visibly high.
* There is no red dot in the top-right corner. A red circle in that exact spot
  is the notification-badge pattern every operating system uses, and in a tab
  strip it reads as "this site wants your attention" rather than as part of a
  logo. RED below is kept for anyone who wants to reintroduce it somewhere
  that does not collide with that convention.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "favicon-source.png"

SIZE = 1024
TILE = (0, 56, 147)  # the blue this icon has always used
RED = (214, 26, 47)  # unused; see the note above
CORNER = 0.158  # of the tile's width, matching the original
LETTER = "S"
INK_HEIGHT = 0.56  # how much of the tile the letter's ink fills

# Avenir Next Heavy: a humanist sans close in feel to Lato, which the site
# sets its headings in.
FONT_PATH = "/System/Library/Fonts/Avenir Next.ttc"
FONT_INDEX = 8


def main():
    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle(
        [0, 0, SIZE - 1, SIZE - 1], radius=int(SIZE * CORNER), fill=TILE + (255,)
    )

    # Scale until the ink — not the line box — is the height we asked for.
    target = SIZE * INK_HEIGHT
    size = 100
    font = ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)
    left, top, right, bottom = draw.textbbox((0, 0), LETTER, font=font)
    size = int(size * target / (bottom - top))
    font = ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)
    left, top, right, bottom = draw.textbbox((0, 0), LETTER, font=font)

    draw.text(
        ((SIZE - (right - left)) // 2 - left, (SIZE - (bottom - top)) // 2 - top),
        LETTER,
        font=font,
        fill=(255, 255, 255, 255),
    )

    icon.save(OUT)
    print(
        f"  {OUT.relative_to(ROOT)}  {SIZE}px, {font.getname()[0]} {font.getname()[1]}"
    )
    print("  now run: .venv/bin/python scripts/make_favicon.py")


if __name__ == "__main__":
    main()
