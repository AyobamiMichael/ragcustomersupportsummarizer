"""
Test preprocessor service 

"""

import pytest
from src.services.preprocessor import PreprocessorService


def test_clean_text(preprocessor):
    """Test text cleaning"""
    text = "<p>Hello   world</p>  \n\n\n  test"
    cleaned = preprocessor._clean_text(text)
    
    assert "<p>" not in cleaned
    assert "Hello world" in cleaned
    assert cleaned.count('\n') <= 2


def test_extract_sections(preprocessor, sample_text):
    """Test section extraction"""
    result = preprocessor.preprocess(sample_text)
    sections = result.sections
    
    assert len(sections) > 0
    assert any('resolution' in key.lower() for key in sections.keys())



def test_extract_sentences(preprocessor, sample_text):
    """Test sentence extraction"""
    sentences = preprocessor.extract_sentences(sample_text)
    
    assert len(sentences) > 0
    assert all(isinstance(s, str) for s in sentences)
    assert all(len(s.split()) >= preprocessor.settings.MIN_SENTENCE_LENGTH 
               for s in sentences)


def test_heuristic_scoring(preprocessor):
    """Test heuristic sentence scoring"""
    sentence = "The issue was resolved by clearing the cache."
    score = preprocessor.score_sentence_heuristic(sentence, 0, 10)
    
    assert score > 0
    assert isinstance(score, float)


def test_remove_boilerplate(preprocessor):
    """Test boilerplate removal"""
    text = """
    Please do not reply to this email.
    This is the actual content.
    Sent from my iPhone.
    """
    
    cleaned = preprocessor.remove_boilerplate(text)
    
    assert "do not reply" not in cleaned.lower()
    assert "actual content" in cleaned


def test_extract_metadata(preprocessor):
    """Test metadata extraction"""
    text = "Contact us at support@atlantisugarsoft.com or visit https://atlantisugarsoft.com"
    cleaned = preprocessor._clean_text(text)
    metadata = preprocessor._extract_metadata(cleaned)
    
    assert 'emails' in metadata or 'urls' in metadata
    assert 'stats' in metadata
    assert metadata['stats']['word_count'] > 0

