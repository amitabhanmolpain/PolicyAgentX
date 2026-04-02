import re
from functools import lru_cache
from typing import List

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer


@lru_cache(maxsize=1)
def _english_stopwords() -> set[str]:
    """Load NLTK English stopwords once; download corpus if missing."""
    try:
        return set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        return set(stopwords.words("english"))


def stem_and_remove_stopwords(text: str) -> List[str]:
    """Stem and remove stopwords from input text; returns clean tokens."""
    if not text:
        return []

    stemmer = PorterStemmer()
    stop_words = _english_stopwords()

    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    clean_tokens = [
        stemmer.stem(token)
        for token in tokens
        if token not in stop_words and len(token) > 1
    ]
    return clean_tokens
