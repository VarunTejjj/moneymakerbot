import pytesseract
from PIL import Image
import re
import os

def check_screenshot(image_path):
    try:
        # OCR to text
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)

        # Debug: print OCR output to check what it sees
        print("OCR Result:", text)

        # Look for UPI ID format
        upi_pattern = r'\b[\w.-]+@[\w]+\b'
        matches = re.findall(upi_pattern, text)

        if matches:
            return True, matches  # UPI Found
        else:
            return False, []  # UPI Not Found

    except Exception as e:
        print("Error in screenshot_checker:", e)
        return False, []
