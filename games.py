import json
import random
from config import QUIZZES_FILE

def get_random_quiz():
    try:
        with open(QUIZZES_FILE, "r", encoding="utf-8") as f:
            quizzes = json.load(f)
        if quizzes:
            return random.choice(quizzes)
    except Exception as e:
        print("Failed to load quizzes:", e)
    return None

def check_answer(user_answer, correct_answer):
    return user_answer.strip().lower() == correct_answer.strip().lower()
