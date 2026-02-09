# utils/translate_utils.py
from deep_translator import GoogleTranslator

def auto_translate(text: str) -> str:
    try:
        # auto-detect source, translate to English if input contains Myanmar unicode,
        # otherwise translate to Myanmar
        if any("\u1000" <= ch <= "\u109F" for ch in text):
            return GoogleTranslator(source='my', target='en').translate(text)
        else:
            return GoogleTranslator(source='auto', target='my').translate(text)
    except Exception as e:
        return f"Translation failed: {e}"
