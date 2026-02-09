# utils/translate_utils.py
from googletrans import Translator

translator = Translator()

def auto_translate(text: str, src: str = "auto", dest: str = "en") -> str:
    try:
        result = translator.translate(text, src=src, dest=dest)
        return result.text
    except Exception as e:
        return f"Translation failed: {e}"
