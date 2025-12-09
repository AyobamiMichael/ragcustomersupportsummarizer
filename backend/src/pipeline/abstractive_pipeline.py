"""
Abstractive pipeline with full LLM generation
"""


import time
from typing import List
from ..models.schemas import (
    SummarizationResponse,
    PipelineMode,
    PipelineStage,
    SentenceProvenance
)
from ..services.preprocessor import PreprocessorService
from ..services.textrank_service import TextRankService
from ..services.embedding_service import EmbeddingService
from ..services.llm_service import LLMService

class AbstractivePipeline:
    """
    Abstractive summarization pipeline with LLM
    
    Pipeline stages:
    1. Preprocessing
    2. TextRank
    3. DistilBERT re-ranking (optional)
    4. LLM abstractive generation
    
    Target latency: <1500ms p95
    """

    def __init__(self, preprocessor: PreprocessorService,
                 textrank: TextRankService,
                 embeddings: EmbeddingService,
                 llm: LLMService):
        self.preprocessor = preprocessor
        self.textrank = textrank
        self.embeddings = embeddings
        self.llm = llm
    
    async def process(self, text: str, top_k: int = 3,
                     include_provenance: bool = True) -> SummarizationResponse:
        """Process text through abstractive pipeline"""
        stages = []
        overall_start = time.time()
        
        # Stage 1: Preprocessing
        stage_start = time.time()
        preprocess_result = self.preprocessor.preprocess(text)
        cleaned_text = preprocess_result.cleaned_text
        sections = preprocess_result.sections
        stages.append(PipelineStage(
            name="Preprocessing",
            duration_ms=(time.time() - stage_start) * 1000
        ))

        # Stage 2: Sentence extraction
        stage_start = time.time()
        sentences = self.preprocessor.extract_sentences(cleaned_text)
        if not sentences:
            return self._create_empty_response(stages, overall_start)
        stages.append(PipelineStage(
            name="Sentence Extraction",
            duration_ms=(time.time() - stage_start) * 1000
        ))

        # Stage 3: TextRank for candidates
        stage_start = time.time()
        textrank_result = self.textrank.rank_sentences(sentences, top_k * 2)
        candidates = [sent for sent, _, _ in textrank_result.ranked_sentences[:top_k * 2]]
        stages.append(PipelineStage(
            name="TextRank",
            duration_ms=(time.time() - stage_start) * 1000
        ))

        # Stage 4: Semantic re-ranking (light)
        stage_start = time.time()
        query = cleaned_text[:500]
        embedding_result = self.embeddings.rerank_with_embeddings(
            query, candidates, top_k
        )
        top_sentences = [candidates[idx] for idx in embedding_result.top_indices]
        stages.append(PipelineStage(
            name="Semantic Re-ranking",
            duration_ms=(time.time() - stage_start) * 1000
        ))

        # Stage 5: LLM abstractive generation
        stage_start = time.time()
        context = f"Original sections: {', '.join(sections.keys())}"
        abstractive_summary = await self.llm.generate_summary(
            top_sentences,
            context=context,
            style="concise"
        )
        stages.append(PipelineStage(
            name="LLM Generation",
            duration_ms=(time.time() - stage_start) * 1000
        ))

         # Build provenance
        provenance = None
        if include_provenance:
            provenance = [
                SentenceProvenance(
                    sentence=candidates[idx],
                    score=score,
                    position=idx,
                    source_section=self._find_section(candidates[idx], sections)
                )
                for idx, score in zip(
                    embedding_result.top_indices,
                    embedding_result.similarity_scores
                )
            ]
        
        total_duration = (time.time() - overall_start) * 1000
        
        return SummarizationResponse(
            summary=abstractive_summary,
            mode=PipelineMode.ABSTRACTIVE,
            sentences_extracted=top_sentences,
            provenance=provenance,
            sections_detected=list(sections.keys()),
            total_sentences=len(sentences),
            pipeline_stages=stages,
            total_duration_ms=total_duration,
            cache_hit=False
        )
    def _find_section(self, sentence: str, sections: dict) -> str:
        """Find which section a sentence belongs to"""
        for section_name, section_content in sections.items():
            if sentence in section_content:
                return section_name
        return "unknown"
    
    def _create_empty_response(self, stages, start_time):
        """Create response for empty input"""
        return SummarizationResponse(
            summary="No content to summarize",
            mode=PipelineMode.ABSTRACTIVE,
            sentences_extracted=[],
            sections_detected=[],
            total_sentences=0,
            pipeline_stages=stages,
            total_duration_ms=(time.time() - start_time) * 1000
        )
    