"""
Pydantic models for request/response schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class PipelineMode(str, Enum):
    """Available pipeline modes"""
    EXTRACTIVE = "extractive"
    SEMANTIC = "semantic"
    ABSTRACTIVE = "abstractive"


class SummarizationRequest(BaseModel):
    """Request model for summarization endpoint"""
    text: str = Field(..., min_length=10, max_length=10000)
    mode: PipelineMode = Field(default=PipelineMode.EXTRACTIVE)
    top_k: Optional[int] = Field(default=3, ge=1, le=10)
    include_provenance: bool = Field(default=True)
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

class SentenceProvenance(BaseModel):
    """Provenance information for extracted sentence"""
    sentence: str
    score: float = Field(..., ge=0.0, le=1.0)
    position: int
    source_section: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineStage(BaseModel):
    """Information about a pipeline stage"""
    name: str
    duration_ms: float
    status: str = Field(default="complete")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SummarizationResponse(BaseModel):
    """Response model for summarization endpoint"""
    summary: str
    mode: PipelineMode
    sentences_extracted: List[str]
    provenance: Optional[List[SentenceProvenance]] = None
    sections_detected: List[str] = Field(default_factory=list)
    total_sentences: int
    pipeline_stages: List[PipelineStage]
    total_duration_ms: float
    cache_hit: bool = False
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict)


class PreprocessingResult(BaseModel):
    """Internal model for preprocessing results"""
    cleaned_text: str
    sections: Dict[str, str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TextRankResult(BaseModel):
    """Internal model for TextRank results"""
    ranked_sentences: List[tuple]
    graph_stats: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingResult(BaseModel):
    """Internal model for embedding results"""
    embeddings: List[List[float]]
    similarity_scores: List[float]
    top_indices: List[int]
