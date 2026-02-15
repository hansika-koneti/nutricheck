import cv2
import numpy as np
from config import IMG_MAX_WIDTH, IMG_MAX_HEIGHT


def preprocess_image(image_path):
    """
    Advanced image preprocessing pipeline for OCR optimization.
    Steps: Resize → Grayscale → CLAHE → Denoise → Adaptive Threshold
    Returns the preprocessed image (numpy array).
    """
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Step 1: Resize while maintaining aspect ratio
    img = resize_image(img, IMG_MAX_WIDTH, IMG_MAX_HEIGHT)

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 3: CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Step 4: Gaussian denoise
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)

    # Step 5: Adaptive threshold for binarization
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2
    )

    return thresh


def resize_image(img, max_width, max_height):
    """Resize image to fit within max dimensions, preserving aspect ratio."""
    h, w = img.shape[:2]
    if w <= max_width and h <= max_height:
        return img

    scale = min(max_width / w, max_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def get_image_for_display(image_path):
    """Read and resize original image for PDF/display (keeps color)."""
    img = cv2.imread(image_path)
    if img is None:
        return None
    return resize_image(img, 600, 800)
