from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DUCK_DIR = ROOT / "static" / "duck"
THUMB_DIR = DUCK_DIR / "thumbs"

CANVAS_SIZE = 1024
ALPHA_THRESHOLD = 16
MAX_BOX_BY_TYPE = {
    "hat": (820, 660),
    "cloth": (820, 760),
    "shoe": (860, 420),
}


def outfit_type(path):
    name = path.name
    for prefix in MAX_BOX_BY_TYPE:
        if name.startswith(f"{prefix}_"):
            return prefix
    return None


def alpha_bbox(image):
    alpha = image.getchannel("A").point(lambda value: 255 if value > ALPHA_THRESHOLD else 0)
    return alpha.getbbox()


def build_thumbnail(source):
    kind = outfit_type(source)
    if not kind:
        return

    image = Image.open(source).convert("RGBA")
    bbox = alpha_bbox(image)
    if not bbox:
        return

    cropped = image.crop(bbox)
    max_width, max_height = MAX_BOX_BY_TYPE[kind]
    scale = min(max_width / cropped.width, max_height / cropped.height)
    width = max(1, round(cropped.width * scale))
    height = max(1, round(cropped.height * scale))

    resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255, 0))
    x = (CANVAS_SIZE - width) // 2
    y = (CANVAS_SIZE - height) // 2
    canvas.alpha_composite(resized, (x, y))

    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(THUMB_DIR / source.name)


def main():
    for source in sorted(DUCK_DIR.glob("*.png")):
        build_thumbnail(source)


if __name__ == "__main__":
    main()
