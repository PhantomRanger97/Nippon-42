from deep_translator import GoogleTranslator

def ja_to_en(text: str, max_chars: int = 500) -> str:
    """
    Translate Japanese text to English.
    Truncates input to max_chars to stay within API limits.
    Returns original text if translation fails.
    """
    if not text or not text.strip():
        return text
    try:
        chunk = text[:max_chars]
        return GoogleTranslator(source='ja', target='en').translate(chunk)
    except Exception:
        return text

def batch_translate(items: list, field: str = "title") -> list:
    """
    Translate a specific field across a list of dicts.
    Example: batch_translate(articles, field="title")
    """
    translated = []
    for item in items:
        new_item = item.copy()
        if field in new_item:
            new_item[field] = ja_to_en(new_item[field])
        translated.append(new_item)
    return translated
