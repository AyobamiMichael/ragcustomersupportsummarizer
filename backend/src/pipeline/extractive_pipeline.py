"""
Fast extractive pipeline using TextRank only
"""
import time
from typing import List

from ..models.schemas import(
    SummarizationResponse,
    PipelineMode,
    PipelineStage,
    SentenceProvenance
)

from ..services.preprocessor import PreprocessorService
from ..services.textrank_service import TextRankService


class ExtractivePipeline:
    """
    Fast extractive summarization pipeline
    
    Pipeline stages:
    1. Preprocessing & cleaning
    2. Sentence extraction
    3. TextRank ranking
    4. Top-k selection
    
    Target latency: <300ms p95
    """

    def __init__(self, preprocessor: PreprocessorService, textrank: TextRankService):
        self.preprocessor = preprocessor
        self.textrank = textrank 
    
    async def process(self, text: str, top_k: int = 3, 
                     include_provenance: bool = True) -> SummarizationResponse:
        """
        Process text through extractive pipeline
        
        Args:
            text: Input text to summarize
            top_k: Number of sentences to extract
            include_provenance: Include sentence provenance
            
        Returns:
            SummarizationResponse with summary and metadata
        """
        stages = []
        overall_start = time.time()

        # Stage 1: Preprocessing
        stage_start = time.time()
        preprocess_result = self.preprocessor.preprocess(text)
        cleaned_text = preprocess_result.cleaned_text
        sections = preprocess_result.sections
        stages.append(PipelineStage(
            name="Preprocessing",
            duration_ms=(time.time() - stage_start) * 1000,
            metadata={"sections_found": len(sections)}
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

        # Stage 3: Apply heuristic scoring
        stage_start = time.time()
        scored_sentences = []
        for idx, sent in enumerate(sentences):
            score = self.preprocessor.score_sentence_heuristic(
                sent, idx, len(sentences)
            )
            scored_sentences.append((sent, score, idx))
        stages.append(PipelineStage(
            name="Heuristic Scoring",
            duration_ms=(time.time() - stage_start) * 1000
        ))
    
          # Stage 4: TextRank ranking
        stage_start = time.time()
        textrank_result = self.textrank.rank_sentences(sentences, top_k * 2)
        stages.append(PipelineStage(
            name="TextRank",
            duration_ms=(time.time() - stage_start) * 1000,
            metadata=textrank_result.graph_stats
        ))

         # Stage 5: Combine scores and select top-k
        stage_start = time.time()
        combined_scores = self._combine_scores(
            scored_sentences,
            textrank_result.ranked_sentences
        )
        
        # Select top k diverse sentences
        final_sentences = self._select_diverse_sentences(
            combined_scores, top_k
        )
        
        stages.append(PipelineStage(
            name="Final Selection",
            duration_ms=(time.time() - stage_start) * 1000,
            metadata={"selected": len(final_sentences)}
        ))
         
         # Build response
        total_duration = (time.time() - overall_start) * 1000
        
        # Create provenance if requested
        provenance = None
        if include_provenance:
            provenance = [
                SentenceProvenance(
                    sentence=sent,
                    score=score,
                    position=idx,
                    source_section=self._find_section(sent, sections)
                )
                for sent, score, idx in combined_scores[:min(10, len(combined_scores))]
            ]
        
        # Generate summary text
        summary_text = ' '.join(final_sentences)
        
        return SummarizationResponse(
            summary=summary_text,
            mode=PipelineMode.EXTRACTIVE,
            sentences_extracted=final_sentences,
            provenance=provenance,
            sections_detected=list(sections.keys()),
            total_sentences=len(sentences),
            pipeline_stages=stages,
            total_duration_ms=total_duration,
            cache_hit=False
        )
    

    def _combine_scores(self, heuristic_scores: List[tuple], 
                       textrank_scores: List[tuple]) -> List[tuple]:
        """
        Combine heuristic and TextRank scores
        
        Args:
            heuristic_scores: List of (sentence, score, idx)
            textrank_scores: List of (sentence, score, idx)
            
        Returns:
            Combined sorted list
        """
        # Create score lookup
        textrank_map = {sent: score for sent, score, _ in textrank_scores}
        
        combined = []
        for sent, h_score, idx in heuristic_scores:
            t_score = textrank_map.get(sent, 0.0)
            
            # Weighted combination (60% TextRank, 40% Heuristic)
            combined_score = 0.6 * t_score + 0.4 * (h_score / 10.0)
            combined.append((sent, combined_score, idx))
        
        # Sort by combined score
        combined.sort(key=lambda x: x[1], reverse=True)
        
        return combined
    

    def _select_diverse_sentences(self, scored_sentences: List[tuple], 
                                  top_k: int) -> List[str]:
        """
        Select diverse sentences avoiding redundancy
        
        Args:
            scored_sentences: Scored sentences
            top_k: Number to select
            
        Returns:
            List of selected sentences in document order
        """
        if len(scored_sentences) <= top_k:
            # Return in document order
            sentences_with_pos = [(s, idx) for s, _, idx in scored_sentences]
            sentences_with_pos.sort(key=lambda x: x[1])
            return [s for s, _ in sentences_with_pos]
        
        selected = []
        selected_indices = set()
        
        for sent, score, idx in scored_sentences:
            if len(selected) >= top_k:
                break
            
            # Check if diverse enough (simple word overlap check)
            is_diverse = True
            for prev_sent in selected:
                overlap = self._word_overlap(sent, prev_sent)
                if overlap > 0.5:  # More than 50% word overlap
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append(sent)
                selected_indices.add(idx)
        
        # Sort by original document order
        sentences_with_pos = [
            (sent, scored_sentences[i][2]) 
            for i, sent in enumerate(selected)
        ]
        sentences_with_pos.sort(key=lambda x: x[1])
        
        return [s for s, _ in sentences_with_pos]
    
    def _word_overlap(self, sent1: str, sent2: str) -> float:
        """Calculate word overlap ratio between sentences"""
        words1 = set(sent1.lower().split())
        words2 = set(sent2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    

    def _find_section(self, sentence: str, sections: dict) -> str:
        """Find which section a sentence belongs to"""
        for section_name, section_content in sections.items():
            if sentence in section_content:
                return section_name
        return "unknown"
    

    def _create_empty_response(self, stages: List[PipelineStage], 
                              start_time: float) -> SummarizationResponse:
        """Create response for empty input"""
        return SummarizationResponse(
            summary="No content to summarize",
            mode=PipelineMode.EXTRACTIVE,
            sentences_extracted=[],
            provenance=[],
            sections_detected=[],
            total_sentences=0,
            pipeline_stages=stages,
            total_duration_ms=(time.time() - start_time) * 1000,
            cache_hit=False
        )