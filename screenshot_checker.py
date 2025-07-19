# screenshot_checker.py (improved)

import pytesseract
from PIL import Image

def check_screenshot(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img).lower().strip()

        print("[DEBUG] Extracted Text:", text)  # Optional: Helps in debugging

        # Flexible matching
        keywords = ["upi", "payment", "paid", "received", "credited", "₹", "rs", "transaction", "successful"]

        matches = [word for word in keywords if word in text]

        return len(matches) >= 2  # Minimum 2 keywords required
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return False
