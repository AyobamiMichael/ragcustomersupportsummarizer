"""
API routes for RAG Summarizer
"""

from fastapi import APIRouter, HTTPException, status, Depends
import time
import structlog

from ..config import get_settings
from ..models.schemas import (
    SummarizationRequest,
    SummarizationResponse,
    HealthResponse,
    PipelineMode
)
from .dependencies import get_pipeline_services

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service health status and version information
    """
    settings = get_settings()
    services = await get_pipeline_services()
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        services={
            "preprocessor": "ok",
            "textrank": "ok",
            "embeddings": "ok" if services['embeddings'].model else "not_loaded",
            "llm": "ok" if services['llm'] else "not_configured"
        }
    )


@router.post("/summarize", response_model=SummarizationResponse)
async def summarize_text(
    request: SummarizationRequest,
    services: dict = Depends(get_pipeline_services)
):
    """
    Summarize customer support text
    
    **Pipeline Modes:**
    - `extractive`: Fast TextRank-only (~200ms) - Best for real-time
    - `semantic`: TextRank + DistilBERT (~350ms) - Balanced quality/speed
    - `abstractive`: Full LLM pipeline (~1200ms) - Best quality
    
    **Parameters:**
    - `text`: Input text to summarize (10-10000 characters)
    - `mode`: Pipeline mode to use
    - `top_k`: Number of sentences to extract (1-10)
    - `include_provenance`: Include sentence provenance data
    
    **Returns:**
    - Summary text
    - Extracted sentences
    - Performance metrics
    - Provenance information (if requested)
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Summarization request",
            mode=request.mode,
            text_length=len(request.text),
            top_k=request.top_k
        )
        
        # Get appropriate pipeline
        pipeline = services['pipelines'].get(request.mode)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid pipeline mode: {request.mode}"
            )
        
        # Run pipeline
        result = await pipeline.process(
            text=request.text,
            top_k=request.top_k,
            include_provenance=request.include_provenance
        )
        
        total_duration = (time.time() - start_time) * 1000
        
        logger.info(
            "Summarization complete",
            mode=request.mode,
            duration_ms=total_duration,
            sentences_extracted=len(result.sentences_extracted)
        )
        
        return result
    
    except ValueError as e:
        logger.warning("Invalid request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Summarization failed", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )

@router.get("/")
async def root():
    """
    Root endpoint - API information
    """
    settings = get_settings()
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "summarize": "POST /api/v1/summarize",
            "health": "GET /health"
        }
    }

@router.get("/models")
async def list_models():
    """
    List available models and their status
    """
    settings = get_settings()
    
    return {
        "sentence_transformer": {
            "model": settings.SENTENCE_TRANSFORMER_MODEL,
            "status": "available"
        },
        "llm": {
            "provider": "Groq",
            "model": settings.LLM_MODEL,
            "status": "configured" if settings.GROQ_API_KEY else "not_configured"
        },
        "pipeline_modes": {
            "extractive": {
                "latency_target": f"{settings.SLO_EXTRACTIVE_P95}ms",
                "description": "Fast TextRank-only summarization"
            },
            "semantic": {
                "latency_target": f"{settings.SLO_SEMANTIC_P95}ms",
                "description": "TextRank + DistilBERT re-ranking"
            },
            "abstractive": {
                "latency_target": f"{settings.SLO_ABSTRACTIVE_P95}ms",
                "description": "Full LLM-based abstractive summarization"
            }
        }
    }

@router.get("/stats")
async def get_stats(services: dict = Depends(get_pipeline_services)):
    """
    Get system statistics and metrics
    """
    # This would integrate with metrics collector in production
    return {
        "status": "operational",
        "requests_processed": "N/A",
        "average_latency_ms": "N/A",
        "cache_hit_rate": "N/A",
        "note": "Detailed metrics require metrics collector integration"
    }


