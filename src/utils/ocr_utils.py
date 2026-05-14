import re

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Sparse text mode: find text anywhere on the page without assuming layout.
# Faster than the default page-segmentation mode for screenshots.
_OCR_CONFIG = "--psm 11"
_MAX_WIDTH = 960  # downscale anything wider than this before OCR


def extract_urls_from_screenshot(path: str) -> list:
    """Run OCR on a screenshot and return any http(s) URLs found."""
    try:
        print(f"[OCR] Processing: {path}")
        img = Image.open(path).convert("L")  # grayscale — faster + more accurate

        # Downscale to cap width, preserving aspect ratio
        w, h = img.size
        if w > _MAX_WIDTH:
            img = img.resize((_MAX_WIDTH, int(h * _MAX_WIDTH / w)), Image.LANCZOS)

        text = pytesseract.image_to_string(img, config=_OCR_CONFIG)
        urls = re.findall(r'https?://[^\s<>"\']+', text)
        print(f"[OCR] Found {len(urls)} URLs")
        return urls

    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return []
