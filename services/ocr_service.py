import easyocr
from config import OCR_LANGUAGES, OCR_GPU

# Lazy-loaded global reader
_reader = None


def get_reader():
    """Get or initialize the EasyOCR reader (lazy singleton)."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(OCR_LANGUAGES, gpu=OCR_GPU)
    return _reader


def extract_text(image_input):
    """
    Run EasyOCR on the given image.
    
    Args:
        image_input: file path (str) or numpy array (preprocessed image)
    
    Returns:
        List of detected text strings and the raw result list.
    """
    reader = get_reader()
    results = reader.readtext(image_input, detail=1, paragraph=False)

    # Extract text strings
    texts = [entry[1] for entry in results]

    # Build full text block
    full_text = '\n'.join(texts)

    return {
        'texts': texts,
        'full_text': full_text,
        'raw_results': results  # [(bbox, text, confidence), ...]
    }


def extract_text_from_path(image_path):
    """Convenience: run OCR directly on an image file path."""
    return extract_text(image_path)
