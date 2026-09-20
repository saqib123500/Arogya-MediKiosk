import cv2
import pytesseract
import numpy as np
import re

def extract_text_from_image(image_path):
    """
    Extract text using a multi-strategy approach to avoid over-processing.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image at {image_path}")

    # 1. Upscale for better character recognition
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. Create different versions of the image
    # Version A: Enhanced Grayscale (Best for most modern OCR)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    denoised_gray = cv2.fastNlMeansDenoising(enhanced_gray, h=10)

    # Version B: Clean Binary (Traditional approach)
    binary = cv2.adaptiveThreshold(
        denoised_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )

    # Version C: Simple Global Threshold (Best for high-contrast documents)
    _, simple_binary = cv2.threshold(denoised_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    strategies = {
        "enhanced_gray": denoised_gray,
        "adaptive_binary": binary,
        "simple_binary": simple_binary
    }

    best_text = ""
    max_score = -1

    # 3. Try each strategy and score the result
    for name, img in strategies.items():
        config = r'--oem 3 --psm 3 -l eng+hin'
        text = pytesseract.image_to_string(img, config=config)
        
        # Scoring function: We prefer text with more alphanumeric characters 
        # and fewer "garbage" symbols like % $ # @ in a row.
        score = calculate_text_quality(text)
        
        if score > max_score:
            max_score = score
            best_text = text

    # 4. Post-process and clean
    lines = best_text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    
    return "\n".join(cleaned_lines)

def calculate_text_quality(text):
    """
    Scores the OCR output. High score = likely real text.
    Low score = likely OCR noise/garbage.
    """
    if not text: return -1
    
    # Count alphanumeric characters
    alnum_count = sum(1 for c in text if c.isalnum())
    # Count noise characters (symbols that rarely appear in medical reports)
    noise_count = sum(1 for c in text if c in "@#$%^&*()_+{}[]|\\")
    
    # Basic score: Alphanumeric density minus noise penalty
    return alnum_count - (noise_count * 5)

