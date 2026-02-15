import os
from services.image_processor import preprocess_image
from services.ocr_service import extract_text
from models.nutrient_parser import parse_nutrients, extract_product_name
from models.health_scorer import calculate_health_score
from database import save_analysis


def analyze_image(image_path):
    """
    Full analysis pipeline: preprocess → OCR → parse → score → save.
    
    Args:
        image_path: path to the uploaded image file
    
    Returns:
        dict with all analysis results and the database row ID
    """
    # Step 1: Preprocess image for OCR
    preprocessed = preprocess_image(image_path)

    # Step 2: Run OCR on preprocessed image
    ocr_result = extract_text(preprocessed)

    # Also run OCR on original for product name detection
    original_ocr = extract_text(image_path)

    # Step 3: Parse nutrients from OCR text
    # Try preprocessed first, fall back to original
    nutrients = parse_nutrients(ocr_result['full_text'])

    # If preprocessed missed some, try original image OCR
    original_nutrients = parse_nutrients(original_ocr['full_text'])
    for key, val in original_nutrients.items():
        if nutrients.get(key) is None and val is not None:
            nutrients[key] = val

    # Step 4: Extract product name
    product_name = extract_product_name(original_ocr['texts'])

    # Step 5: Calculate health score
    health_result = calculate_health_score(nutrients)

    # Step 6: Build result object
    result = {
        'product_name': product_name,
        'image_path': image_path,
        'calories': nutrients.get('calories'),
        'sugar': nutrients.get('sugar'),
        'fat': nutrients.get('fat'),
        'sodium': nutrients.get('sodium'),
        'protein': nutrients.get('protein'),
        'fiber': nutrients.get('fiber'),
        'health_score': health_result['health_score'],
        'verdict': health_result['verdict'],
        'explanation': health_result['explanation'],
        'recommendation': health_result['recommendation'],
        'raw_ocr_text': ocr_result['full_text'],
        'breakdown': health_result['breakdown'],
    }

    # Step 7: Save to database
    row_id = save_analysis(result)
    result['id'] = row_id

    return result
