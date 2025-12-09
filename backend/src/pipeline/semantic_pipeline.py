"""
Semantic pipeline with TextRank + DistilBERT re-ranking
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


class SemanticPipeline:
    """
    Semantic summarization pipeline with re-ranking
    
    Pipeline stages:
    1. Preprocessing
    2. TextRank (get candidates)
    3. DistilBERT re-ranking
    4. Top-k selection
    
    Target latency: <500ms p95
    """

    def __init__(
         self, preprocessor: PreprocessorService,
          textrank: TextRankService,
          embeddings: EmbeddingService
     ):
        self.preprocessor = preprocessor
        self.textrank = textrank
        self.embeddings = embeddings

    async def process(self, text: str, top_k: int = 3, include_provenance: bool = True)-> SummarizationResponse:
        """Process text through semantic pipeline"""
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
            duration_ms=(time.time() - stage_start) * 1000,
            metadata={"total_sentences": len(sentences)}
        ))

        # Stage 3: TextRank (get top candidates)
        stage_start = time.time()
        candidate_k = min(top_k * 3, len(sentences))  # Get 3x candidates
        textrank_result = self.textrank.rank_sentences(sentences, candidate_k)
        candidates = [sent for sent, _, _ in textrank_result.ranked_sentences]
        stages.append(PipelineStage(
            name="TextRank",
            duration_ms=(time.time() - stage_start) * 1000,
            metadata={"candidates": len(candidates)}
        ))

         # Stage 4: DistilBERT re-ranking
        stage_start = time.time()
        # Use full text as query for relevance
        query = cleaned_text[:500]  # Limit query length
        embedding_result = self.embeddings.rerank_with_embeddings(
            query, candidates, top_k
        )

         # Get top sentences
        final_sentences = [
            candidates[idx] for idx in embedding_result.top_indices
        ]
        stages.append(PipelineStage(
            name="DistilBERT Re-ranking",
            duration_ms=(time.time() - stage_start) * 1000,
            metadata={"selected": len(final_sentences)}
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
        summary_text = ' '.join(final_sentences)

        return SummarizationResponse(
            summary=summary_text,
            mode=PipelineMode.SEMANTIC,
            sentences_extracted=final_sentences,
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
            mode=PipelineMode.SEMANTIC,
            sentences_extracted=[],
            sections_detected=[],
            total_sentences=0,
            pipeline_stages=stages,
            total_duration_ms=(time.time() - start_time) * 1000
        )

