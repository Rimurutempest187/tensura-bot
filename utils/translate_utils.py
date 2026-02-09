# utils/translate_utils.py
from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

def detect_myanmar(text: str) -> bool:
    # simple heuristic: contains Myanmar Unicode block
    return any("\u1000" <= ch <= "\u109F" for ch in text)

def translate_auto(text: str, target: str = None) -> str:
    """
    Auto-detect source and translate.
    If target is None: translate Myanmar -> en, else translate to target.
    """
    try:
        if target:
            return GoogleTranslator(source='auto', target=target).translate(text)
        if detect_myanmar(text):
            return GoogleTranslator(source='my', target='en').translate(text)
        else:
            return GoogleTranslator(source='auto', target='my').translate(text)
    except Exception as e:
        logger.exception("Translation failed: %s", e)
        raise
