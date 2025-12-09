"""
Text processing utilities
"""

import re
from typing import List, Set

def remove_urls(text: str)-> str:
     """Remove URLs from text"""
     return re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)


def remove_emails(text: str) -> str:
    """Remove email addresses from text"""
    return re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    return re.sub(r'\s+', ' ', text).strip()

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract top keywords from text"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    try:
        vectorizer = TfidfVectorizer(max_features=top_n, stop_words='english')
        vectors = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        return list(feature_names)
    except:
        return []

def calculate_readability_score(text: str) -> float:
     """Calculate Flesch Reading Ease score"""
     sentences = text.count('.') + text.count('!') + text.count('?')
     words = len(text.split())
     syllables = sum(count_syllables(word) for word in text.split())

     if sentences == 0 or words == 0:
        return 0.0
    
     score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
     return max(0, min(100, score))

def count_syllables(word: str) -> int:
    """Count syllables in a word (approximation)"""
    word = word.lower()
    count = 0
    vowels = 'aeiouy'
    previous_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            count += 1
        previous_was_vowel = is_vowel

    if word.endswith('e'):
        count -= 1
    if count == 0:
        count = 1
    
    return count

def get_unique_words(text: str) -> Set[str]:
    """Get set of unique words from text"""
    words = re.findall(r'\b\w+\b', text.lower())
    return set(words)

def calculate_text_diversity(text: str) -> float:
    """Calculate lexical diversity (unique words / total words)"""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)