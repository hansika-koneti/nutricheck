import re


# Patterns to match nutrient lines on food labels
NUTRIENT_PATTERNS = {
    'calories': [
        r'(?:calories|energy|cal|kcal|kilocal)[:\s]*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:kcal|cal|calories)',
        r'(?:energy)\s*[:=]?\s*(\d+\.?\d*)\s*(?:kcal)?',
    ],
    'sugar': [
        r'(?:sugar|sugars|total sugar|total sugars)[:\s]*(\d+\.?\d*)\s*(?:g|gm|grams)?',
        r'(\d+\.?\d*)\s*(?:g|gm)\s*(?:sugar|sugars)',
    ],
    'fat': [
        r'(?:total fat|fat|fats)[:\s]*(\d+\.?\d*)\s*(?:g|gm|grams)?',
        r'(\d+\.?\d*)\s*(?:g|gm)\s*(?:fat|fats)',
    ],
    'sodium': [
        r'(?:sodium|salt|na)[:\s]*(\d+\.?\d*)\s*(?:mg|g|gm)?',
        r'(\d+\.?\d*)\s*(?:mg|g)\s*(?:sodium|salt)',
    ],
    'protein': [
        r'(?:protein|proteins)[:\s]*(\d+\.?\d*)\s*(?:g|gm|grams)?',
        r'(\d+\.?\d*)\s*(?:g|gm)\s*(?:protein|proteins)',
    ],
    'fiber': [
        r'(?:dietary fiber|fibre|fiber|fibres)[:\s]*(\d+\.?\d*)\s*(?:g|gm|grams)?',
        r'(\d+\.?\d*)\s*(?:g|gm)\s*(?:fiber|fibre|dietary fiber)',
    ],
}

# Unit conversion multipliers → normalize to standard units
# calories: kcal, sugar/fat/protein/fiber: g, sodium: mg
UNIT_CONVERSIONS = {
    'calories': {
        'kj': 0.239006,   # kJ → kcal
        'kilojoule': 0.239006,
        'kilojoules': 0.239006,
    },
    'sodium': {
        'g': 1000,    # g → mg
        'gm': 1000,
        'grams': 1000,
    }
}


def parse_nutrients(ocr_text):
    """
    Parse OCR text to extract nutrient values.
    
    Args:
        ocr_text: string of OCR-detected text
    
    Returns:
        dict with nutrient keys and float values (or None if not found)
    """
    text = ocr_text.lower()
    
    # Fix common OCR misreads
    text = text.replace('|', 'l')
    text = text.replace('O', '0').replace('o', '0')
    # But restore words that got mangled
    text = re.sub(r's0dium', 'sodium', text)
    text = re.sub(r'pr0tein', 'protein', text)
    text = re.sub(r'cal0ries', 'calories', text)
    text = re.sub(r'fiber', 'fiber', text)
    text = re.sub(r'sugar', 'sugar', text)
    text = re.sub(r't0tal', 'total', text)

    nutrients = {}

    for nutrient, patterns in NUTRIENT_PATTERNS.items():
        value = None
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        nutrients[nutrient] = value

    # Apply unit conversions where needed
    nutrients = normalize_units(nutrients, text)

    # Sanity check: clamp obviously wrong values
    nutrients = sanity_check(nutrients)

    return nutrients


def normalize_units(nutrients, text):
    """Convert units to standard (kcal, g, mg)."""
    # Check if calories are in kJ
    if nutrients.get('calories') and re.search(r'kj|kilojoule', text):
        nutrients['calories'] *= 0.239006

    # Check if sodium is in grams instead of mg
    if nutrients.get('sodium') is not None and nutrients['sodium'] < 10:
        # Likely reported in grams, convert to mg
        if re.search(r'sodium[:\s]*[\d.]+\s*g(?:m|rams)?', text):
            nutrients['sodium'] *= 1000

    return nutrients


def sanity_check(nutrients):
    """Clamp nutrient values to reasonable ranges."""
    limits = {
        'calories': (0, 2000),
        'sugar': (0, 200),
        'fat': (0, 200),
        'sodium': (0, 10000),  # mg
        'protein': (0, 200),
        'fiber': (0, 100),
    }
    for key, (low, high) in limits.items():
        if nutrients.get(key) is not None:
            nutrients[key] = max(low, min(high, nutrients[key]))
    return nutrients


def extract_product_name(ocr_texts):
    """
    Attempt to extract a product name from OCR text lines.
    Heuristic: first non-nutrient text line that is 3+ characters.
    """
    nutrient_keywords = {
        'calories', 'sugar', 'fat', 'sodium', 'protein', 'fiber',
        'nutrition', 'facts', 'amount', 'serving', 'daily', 'value',
        'total', 'percent', 'ingredients', 'contains', 'allergen',
        'carbohydrate', 'cholesterol', 'vitamin', 'mineral', 'energy'
    }

    for text in ocr_texts:
        cleaned = text.strip()
        if len(cleaned) < 3:
            continue
        words = cleaned.lower().split()
        # Skip lines that are mostly nutrient-related
        if any(kw in words for kw in nutrient_keywords):
            continue
        # Skip lines that are mostly numbers
        digits = sum(c.isdigit() for c in cleaned)
        if digits > len(cleaned) * 0.5:
            continue
        return cleaned

    return 'Unknown Product'
