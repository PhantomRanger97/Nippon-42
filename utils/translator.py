# utils/translator.py
from deep_translator import GoogleTranslator


def ja_to_en(text: str, max_chars: int = 500) -> str:
    """Translate Japanese text to English. Returns original on failure."""
    if not text or not text.strip():
        return text
    try:
        return GoogleTranslator(source="ja", target="en").translate(text[:max_chars])
    except Exception:
        return text


def batch_translate(items: list[dict], field: str = "title") -> list[dict]:
    """Translate a specific field across a list of dicts in-place (copy)."""
    result = []
    for item in items:
        new_item = item.copy()
        if field in new_item:
            new_item[field] = ja_to_en(new_item[field])
        result.append(new_item)
    return result
