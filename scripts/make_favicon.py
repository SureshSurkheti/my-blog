"""Generate every site icon size from one source image.

Run from the project root:

    .venv/bin/python scripts/make_favicon.py

Source, in order of preference:

1. ``static/favicon-source.png`` — a square PNG, 512x512 or larger. Use this if
   you have the original artwork; it is the only way the large iOS and Android
   icons come out sharp.
2. ``static/favicon.ico`` — the largest frame inside it. An .ico usually tops
   out at 48x48, so the 180px and 512px icons are then upscaled and will look
   soft. The script says so when that happens.

Outputs (all committed, so deploying needs no image tooling):
  favicon.ico            16/32/48 in one file, for older browsers
  favicon-32.png         browsers that prefer a PNG
  apple-touch-icon.png   iOS home screen, 180px, alpha flattened
  icon-192/512.png       Android and installable web apps

The manifest is not generated here: it lives at templates/site.webmanifest and
is rendered by a view, because it has to name the hashed static filenames that
only {% static %} can resolve.
"""

from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

SOURCE_PNG = STATIC / "favicon-source.png"
SOURCE_ICO = STATIC / "favicon.ico"

PNG_SIZES = {
    "favicon-32.png": 32,
    "icon-192.png": 192,
    "icon-512.png": 512,
}
APPLE_TOUCH_SIZE = 180
ICO_SIZES = [(16, 16), (32, 32), (48, 48)]



def load_source():
    """Return (image, native_size, description)."""
    if SOURCE_PNG.exists():
        image = Image.open(SOURCE_PNG).convert("RGBA")
        return image, min(image.size), f"{SOURCE_PNG.name} ({image.size[0]}px)"

    if not SOURCE_ICO.exists():
        raise SystemExit(
            f"No source found. Add {SOURCE_PNG.name} (512px or larger) or "
            f"{SOURCE_ICO.name} to static/."
        )

    with Image.open(SOURCE_ICO) as handle:
        largest = max(handle.ico.sizes())
        handle.size = largest
        image = handle.convert("RGBA")
    return image, min(largest), f"{SOURCE_ICO.name} (largest frame {largest[0]}px)"


def dominant_colour(image):
    """The most common fully opaque colour — used behind the iOS icon.

    iOS ignores transparency and composites onto black, which puts a dark ring
    around a rounded icon; filling with the icon's own colour avoids that.
    """
    colours = image.getcolors(maxcolors=image.size[0] * image.size[1]) or []
    counts = Counter(
        {colour[:3]: count for count, colour in colours if colour[3] > 250}
    )
    return counts.most_common(1)[0][0] if counts else (255, 255, 255)


def resize(image, size):
    return image.resize((size, size), Image.LANCZOS)


def main():
    source, native, described = load_source()
    if source.size[0] != source.size[1]:
        side = min(source.size)
        left = (source.size[0] - side) // 2
        top = (source.size[1] - side) // 2
        source = source.crop((left, top, left + side, top + side))
        print(f"  note: source was not square; cropped to {side}x{side}")

    print(f"  source: {described}")

    background = dominant_colour(source)
    largest_needed = max(max(PNG_SIZES.values()), APPLE_TOUCH_SIZE)
    if native < largest_needed:
        print(
            f"  WARNING: the source is only {native}px, so the "
            f"{largest_needed}px icon is upscaled and will look soft."
        )
        print(
            "           Add static/favicon-source.png at 512px or larger and "
            "re-run for sharp icons."
        )

    for name, size in PNG_SIZES.items():
        resize(source, size).save(STATIC / name)

    # iOS shows no transparency, so flatten onto the icon's own colour.
    apple = Image.new("RGB", (APPLE_TOUCH_SIZE, APPLE_TOUCH_SIZE), background)
    scaled = resize(source, APPLE_TOUCH_SIZE)
    apple.paste(scaled, (0, 0), scaled)
    apple.save(STATIC / "apple-touch-icon.png")

    # Rebuild the .ico from the source unless it *is* the source.
    if SOURCE_PNG.exists():
        resize(source, 48).save(STATIC / "favicon.ico", sizes=ICO_SIZES)

    theme = "#{:02x}{:02x}{:02x}".format(*background)
    print(f"  icon's dominant colour: {theme}")
    print("  note: templates/site.webmanifest is rendered by a view and names")
    print("        the hashed static files, so it is not written from here.")

    for name in sorted(["favicon.ico", "apple-touch-icon.png", *PNG_SIZES]):
        path = STATIC / name
        print(f"  {name:24} {path.stat().st_size:>7,} bytes")


if __name__ == "__main__":
    main()
