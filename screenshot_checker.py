# screenshot_checker.py

import pytesseract
from PIL import Image
from config import UPI_ID

def check_screenshot(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img).lower().strip()
        print("[OCR TEXT]:", text)
        return UPI_ID.lower() in text
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return False
