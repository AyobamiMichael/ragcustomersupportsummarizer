"""
Tests for TextRank service
"""

import pytest
from src.services.textrank_service import TextRankService


def test_rank_sentences(textrank):
    """Test basic sentence ranking"""
    sentences = [
        "The customer reported a login issue.",
        "The issue was with password reset.",
        "We resolved the problem quickly.",
        "Customer is now able to log in."
    ]
    
    result = textrank.rank_sentences(sentences, top_k=2)
    
    assert len(result.ranked_sentences) <= 2
    assert all(len(item) == 3 for item in result.ranked_sentences)



def test_empty_sentences(textrank):
    """Test with empty input"""
    result = textrank.rank_sentences([], top_k=3)
    
    assert len(result.ranked_sentences) == 0
    assert isinstance(result.graph_stats, dict)

def test_single_sentence(textrank):
    """Test with single sentence"""
    sentences = ["This is a single sentence."]
    result = textrank.rank_sentences(sentences, top_k=1)
    
    assert len(result.ranked_sentences) == 1


def test_similarity_matrix(textrank):
    """Test similarity matrix construction"""
    sentences = [
        "The cat sat on the mat.",
        "The dog sat on the log.",
        "Python is a programming language."
    ]
    
    matrix = textrank._build_similarity_matrix(sentences)
    
    assert matrix.shape == (3, 3)
    assert matrix[0][1] > matrix[0][2]  # First two more similar


def test_mmr_ranking(textrank):
    """Test MMR diverse ranking"""
    sentences = [
        "The customer reported an issue.",
        "Customer reported issue with login.",  # Similar to first
        "We provided a resolution.",
        "The problem was resolved quickly."
    ]
    
    result = textrank.rank_with_mmr(sentences, top_k=2)
    
    assert len(result) == 2
    # Should select diverse sentences


