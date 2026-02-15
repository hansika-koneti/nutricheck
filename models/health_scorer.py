from config import DAILY_REFERENCE, SCORE_HEALTHY, SCORE_MODERATE


def calculate_health_score(nutrients):
    """
    Hybrid Nutri-Score inspired health scoring model.
    
    Scoring logic:
    1. Negative points (0-40): based on calories, sugar, sodium, fat
       - Higher values of these = more negative points = lower score
    2. Positive points (0-15): based on protein, fiber
       - Higher values of these = more positive points = higher score
    3. Final score = max(0, min(100, 100 - negative + positive))
    
    Args:
        nutrients: dict with keys calories, sugar, fat, sodium, protein, fiber
    
    Returns:
        dict with health_score, verdict, explanation, recommendation
    """
    # Extract values, default to 0 if missing
    cal = nutrients.get('calories') or 0
    sugar = nutrients.get('sugar') or 0
    fat = nutrients.get('fat') or 0
    sodium = nutrients.get('sodium') or 0
    protein = nutrients.get('protein') or 0
    fiber = nutrients.get('fiber') or 0

    # --- Negative Points Calculation ---
    # Each is 0-10, based on % of daily reference
    cal_pct = (cal / DAILY_REFERENCE['calories']) * 100
    sugar_pct = (sugar / DAILY_REFERENCE['sugar']) * 100
    fat_pct = (fat / DAILY_REFERENCE['fat']) * 100
    sodium_pct = (sodium / DAILY_REFERENCE['sodium']) * 100

    neg_cal = _scale_negative(cal_pct)
    neg_sugar = _scale_negative(sugar_pct)
    neg_fat = _scale_negative(fat_pct)
    neg_sodium = _scale_negative(sodium_pct)

    total_negative = neg_cal + neg_sugar + neg_fat + neg_sodium  # 0-40

    # --- Positive Points Calculation ---
    protein_pct = (protein / DAILY_REFERENCE['protein']) * 100
    fiber_pct = (fiber / DAILY_REFERENCE['fiber']) * 100

    pos_protein = _scale_positive(protein_pct)
    pos_fiber = _scale_positive(fiber_pct)

    total_positive = pos_protein + pos_fiber  # 0-15 (capped)

    # --- Final Score ---
    score = max(0, min(100, 100 - total_negative + total_positive))
    score = round(score)

    # --- Verdict ---
    if score >= SCORE_HEALTHY:
        verdict = 'Healthy Choice'
    elif score >= SCORE_MODERATE:
        verdict = 'Consume in Moderation'
    else:
        verdict = 'Limit Consumption'

    # --- Explanation ---
    explanation = _generate_explanation(nutrients, {
        'calories': neg_cal,
        'sugar': neg_sugar,
        'fat': neg_fat,
        'sodium': neg_sodium,
    }, {
        'protein': pos_protein,
        'fiber': pos_fiber,
    })

    # --- Recommendation ---
    recommendation = _generate_recommendation(verdict, nutrients)

    return {
        'health_score': score,
        'verdict': verdict,
        'explanation': explanation,
        'recommendation': recommendation,
        'breakdown': {
            'negative': {
                'calories': neg_cal,
                'sugar': neg_sugar,
                'fat': neg_fat,
                'sodium': neg_sodium,
                'total': total_negative,
            },
            'positive': {
                'protein': pos_protein,
                'fiber': pos_fiber,
                'total': total_positive,
            }
        }
    }


def _scale_negative(pct):
    """Scale a percentage to 0-10 negative points."""
    if pct <= 5:
        return 0
    elif pct <= 15:
        return 2
    elif pct <= 25:
        return 4
    elif pct <= 40:
        return 6
    elif pct <= 60:
        return 8
    else:
        return 10


def _scale_positive(pct):
    """Scale a percentage to 0-7.5 positive points."""
    if pct >= 30:
        return 7.5
    elif pct >= 20:
        return 5
    elif pct >= 10:
        return 3
    elif pct >= 5:
        return 1.5
    else:
        return 0


def _generate_explanation(nutrients, neg_scores, pos_scores):
    """Generate human-readable explanation of the score."""
    parts = []

    # Find top negative contributors
    worst = sorted(neg_scores.items(), key=lambda x: x[1], reverse=True)
    for nutrient, score in worst:
        if score >= 6:
            val = nutrients.get(nutrient, 0) or 0
            unit = 'mg' if nutrient == 'sodium' else ('kcal' if nutrient == 'calories' else 'g')
            pct = round((val / DAILY_REFERENCE[nutrient]) * 100)
            parts.append(
                f"High {nutrient} ({val}{unit}, {pct}% of daily value) "
                f"negatively impacts the health score."
            )
        elif score >= 4:
            val = nutrients.get(nutrient, 0) or 0
            unit = 'mg' if nutrient == 'sodium' else ('kcal' if nutrient == 'calories' else 'g')
            parts.append(
                f"Moderate {nutrient} level ({val}{unit}) contributes to a lower score."
            )

    # Highlight positives
    for nutrient, score in pos_scores.items():
        if score >= 5:
            val = nutrients.get(nutrient, 0) or 0
            parts.append(
                f"Good {nutrient} content ({val}g) positively contributes to the score."
            )

    if not parts:
        parts.append("Nutrient levels are within acceptable ranges.")

    return ' '.join(parts)


def _generate_recommendation(verdict, nutrients):
    """Generate dietary recommendation based on verdict and nutrient profile."""
    recs = []

    if verdict == 'Healthy Choice':
        recs.append("This product has a balanced nutritional profile and can be part of a healthy diet.")
    elif verdict == 'Consume in Moderation':
        recs.append("This product is acceptable in moderate quantities as part of a balanced diet.")
    else:
        recs.append("This product should be consumed sparingly due to its nutritional profile.")

    # Specific advice
    sugar = nutrients.get('sugar') or 0
    sodium = nutrients.get('sodium') or 0
    fat = nutrients.get('fat') or 0
    protein = nutrients.get('protein') or 0
    fiber = nutrients.get('fiber') or 0

    if sugar > DAILY_REFERENCE['sugar'] * 0.25:
        recs.append("Consider lower-sugar alternatives to reduce added sugar intake.")
    if sodium > DAILY_REFERENCE['sodium'] * 0.25:
        recs.append("High sodium content — watch your total daily sodium intake.")
    if fat > DAILY_REFERENCE['fat'] * 0.25:
        recs.append("Significant fat content — balance with lower-fat meals.")
    if protein < DAILY_REFERENCE['protein'] * 0.05:
        recs.append("Low in protein — pair with protein-rich foods.")
    if fiber < DAILY_REFERENCE['fiber'] * 0.05:
        recs.append("Low in fiber — consider adding whole grains, fruits, or vegetables.")

    return ' '.join(recs)
