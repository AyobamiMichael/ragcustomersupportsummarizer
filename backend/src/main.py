# backend/src/main.py
"""
FastAPI application entry point - SIMPLIFIED VERSION FOR DEPLOYMENT
All routes in one file to avoid import issues
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import structlog
from datetime import datetime

from .config import get_settings
from .models.schemas import (
    SummarizationRequest,
    SummarizationResponse,
    HealthResponse,
    ErrorResponse,
    PipelineMode
)
from .services.preprocessor import PreprocessorService
from .services.textrank_service import TextRankService
from .services.embedding_service import EmbeddingService
from .services.llm_service import LLMService
from .pipeline.extractive_pipeline import ExtractivePipeline
from .pipeline.semantic_pipeline import SemanticPipeline
from .pipeline.abstractive_pipeline import AbstractivePipeline

logger = structlog.get_logger()

# Global services
preprocessor = None
textrank = None
embeddings = None
llm = None
pipelines = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    logger.info("Starting RAG Summarizer API")
    
    global preprocessor, textrank, embeddings, llm, pipelines
    
    # Initialize services
    preprocessor = PreprocessorService()
    textrank = TextRankService()
    embeddings = EmbeddingService()
    llm = LLMService()
    
    # Initialize pipelines
    pipelines = {
        PipelineMode.EXTRACTIVE: ExtractivePipeline(preprocessor, textrank),
        PipelineMode.SEMANTIC: SemanticPipeline(preprocessor, textrank, embeddings),
        PipelineMode.ABSTRACTIVE: AbstractivePipeline(preprocessor, textrank, embeddings, llm),
    }
    
    logger.info(
        "Services initialized successfully",
        services=list(['preprocessor', 'textrank', 'embeddings', 'llm', 'pipelines'])
    )
    
    yield
    
    logger.info("Shutting down RAG Summarizer API")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Latency-sensitive RAG summarizer for customer support content",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            code="INTERNAL_ERROR"
        ).dict()
    )


# ============================================
# ROUTES - All in one file for deployment
# ============================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api_prefix": settings.API_PREFIX
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint at root level"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        services={
            "preprocessor": "ok",
            "textrank": "ok",
            "embeddings": "ok" if embeddings and embeddings.model else "not_loaded",
            "llm": "ok" if llm and llm.client else "not_configured"
        }
    )


@app.post(f"{settings.API_PREFIX}/summarize", response_model=SummarizationResponse)
async def summarize_text(request: SummarizationRequest):
    """
    Summarize customer support text
    
    **Pipeline Modes:**
    - extractive: Fast TextRank-only (~200ms)
    - semantic: TextRank + DistilBERT (~350ms)
    - abstractive: Full LLM pipeline (~1200ms)
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Summarization request",
            mode=request.mode,
            text_length=len(request.text)
        )
        
        # Get appropriate pipeline
        pipeline = pipelines.get(request.mode)
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
            duration_ms=total_duration
        )
        
        return result
    
    except ValueError as e:
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


@app.get(f"{settings.API_PREFIX}/models")
async def list_models():
    """List available models and their status"""
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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )