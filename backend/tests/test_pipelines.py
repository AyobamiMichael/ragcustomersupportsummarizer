"""
Tests for pipeline implementations
"""

import pytest
from src.pipeline.extractive_pipeline import ExtractivePipeline
from src.services.preprocessor import PreprocessorService
from src.services.textrank_service import TextRankService


@pytest.mark.asyncio
async def test_extractive_pipeline(sample_text):
    """Test extractive pipeline"""
    preprocessor = PreprocessorService()
    textrank = TextRankService()
    pipeline = ExtractivePipeline(preprocessor, textrank)
    
    result = await pipeline.process(sample_text, top_k=3)
    
    assert result.summary
    assert len(result.sentences_extracted) <= 3
    assert result.total_duration_ms > 0
    assert len(result.pipeline_stages) > 0



@pytest.mark.asyncio
async def test_pipeline_empty_input():
    """Test pipeline with empty input"""
    preprocessor = PreprocessorService()
    textrank = TextRankService()
    pipeline = ExtractivePipeline(preprocessor, textrank)
    
    result = await pipeline.process("", top_k=3)
    
    assert result.summary == "No content to summarize"
    assert len(result.sentences_extracted) == 0


@pytest.mark.asyncio
async def test_pipeline_performance(sample_text):
    """Test pipeline meets latency target"""
    preprocessor = PreprocessorService()
    textrank = TextRankService()
    pipeline = ExtractivePipeline(preprocessor, textrank)
    
    result = await pipeline.process(sample_text, top_k=3)
    
    # Extractive should be under 500ms
    assert result.total_duration_ms < 500

