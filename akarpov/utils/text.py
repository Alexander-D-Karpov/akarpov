from fuzzywuzzy import fuzz
from unidecode import unidecode


def normalize_text(text):
    return unidecode(text.lower().strip())


def is_similar_artist(name1, name2, threshold=90):
    return fuzz.ratio(normalize_text(name1), normalize_text(name2)) > threshold
