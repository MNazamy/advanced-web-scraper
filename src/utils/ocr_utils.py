import re

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_urls_from_screenshot(path: str) -> str:
    """Run OCR on a screenshot PNG and return the raw text."""
    try:
        print(f"[OCR] Processing screenshot: {path}")
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        print(f"[OCR] Extracted {len(text)} characters of text")
        print(f"[OCR] Raw text:\n{text}")
        urls = re.findall(r'https?://[^\s<>"\']+', text)
        print(f"[OCR] Found {len(urls)} links")
        return urls

    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return ""