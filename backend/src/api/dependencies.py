"""
FastAPI dependencies for dependency injection
"""

from typing import Optional, Dict
from fastapi import Header, HTTPException, status
from functools import lru_cache

from ..services.preprocessor import PreprocessorService
from ..services.textrank_service import TextRankService
from ..services.embedding_service import EmbeddingService
from ..services.llm_service import LLMService
from ..pipeline.extractive_pipeline import ExtractivePipeline
from ..pipeline.semantic_pipeline import SemanticPipeline
from ..pipeline.abstractive_pipeline import AbstractivePipeline
from ..models.schemas import PipelineMode


# Global service instances (singleton pattern)
_services = None


def get_services():
    """Get or create service instances"""
    global _services
    
    if _services is None:
        preprocessor = PreprocessorService()
        textrank = TextRankService()
        embeddings = EmbeddingService()
        llm = LLMService()
        
        pipelines = {
            PipelineMode.EXTRACTIVE: ExtractivePipeline(preprocessor, textrank),
            PipelineMode.SEMANTIC: SemanticPipeline(preprocessor, textrank, embeddings),
            PipelineMode.ABSTRACTIVE: AbstractivePipeline(preprocessor, textrank, embeddings, llm),
        }
        
        _services = {
            'preprocessor': preprocessor,
            'textrank': textrank,
            'embeddings': embeddings,
            'llm': llm,
            'pipelines': pipelines
        }
    
    return _services


async def get_pipeline_services() -> Dict:
    """Dependency for getting pipeline services"""
    return get_services()


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key (if authentication is enabled)
    
    Args:
        x_api_key: API key from header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException if invalid
    """
    # In production, implement actual key verification
    # For now, allow all requests
    return x_api_key or "anonymous"


async def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from header
    
    Args:
        x_user_id: User ID from header
        
    Returns:
        User ID or 'anonymous'
    """
    return x_user_id or "anonymous"


