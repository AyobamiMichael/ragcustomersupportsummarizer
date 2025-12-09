"""
TextRank extractive summarization service
"""

import numpy as np
import networkx as nx
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import get_settings
from ..models.schemas import TextRankResult


class TextRankService:
    """Service for TextRank-based extractive summarization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def rank_sentences(self, sentences: List[str], top_k: int = None) -> TextRankResult:

        """
        Rank sentences using TextRank algorithm
        
        Args:
            sentences: List of sentences to rank
            top_k: Number of top sentences to return
            
        Returns:
            TextRankResult with ranked sentences and metadata
        """
        if not sentences:
            return TextRankResult(ranked_sentences=[], graph_stats={})
        
        if top_k is None:
            top_k = self.settings.TEXTRANK_TOP_K
        
        # Build similarity matrix
        similarity_matrix = self._build_similarity_matrix(sentences)
        
        # Build graph
        graph = nx.from_numpy_array(similarity_matrix)

        # Calculate PageRank scores
        try:
            scores = nx.pagerank(
                graph,
                alpha=self.settings.TEXTRANK_DAMPING,
                max_iter=100,
                tol=1e-6
            )
        except:
            scores = {i: 1.0 / len(sentences) for i in range(len(sentences))}
        
        # Rank sentences by score
        ranked = sorted(
            [(sentences[i], scores[i], i) for i in range(len(sentences))],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top k
        top_sentences = ranked[:min(top_k, len(ranked))]
        
        # Calculate graph statistics
        graph_stats = self._calculate_graph_stats(graph, similarity_matrix)
        
        return TextRankResult(
            ranked_sentences=top_sentences,
            graph_stats=graph_stats
        )
    
    def _build_similarity_matrix(self, sentences: List[str]) -> np.ndarray:
        """Build sentence similarity matrix using TF-IDF"""
        if len(sentences) == 1:
            return np.array([[1.0]])
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(sentences)
            similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
            np.fill_diagonal(similarity_matrix, 0)
            return similarity_matrix
        except Exception as e:
            n = len(sentences)
            matrix = np.ones((n, n)) * 0.1
            np.fill_diagonal(matrix, 0)
            return matrix
    
    def _calculate_graph_stats(self, graph: nx.Graph, 
                               similarity_matrix: np.ndarray) -> Dict:
        """Calculate graph statistics for metadata"""
        stats = {}
        
        try:
            stats['num_nodes'] = graph.number_of_nodes()
            stats['num_edges'] = graph.number_of_edges()
            stats['density'] = nx.density(graph)
            stats['avg_similarity'] = float(np.mean(similarity_matrix[similarity_matrix > 0]))
            stats['max_similarity'] = float(np.max(similarity_matrix))
        except:
            stats['error'] = 'Failed to calculate stats'
        
        return stats
    
    def extract_diverse_sentences(self, ranked_sentences: List[Tuple], 
                                  diversity_threshold: float = 0.7) -> List[str]:
        """Extract diverse sentences by avoiding redundancy"""
        if not ranked_sentences:
            return []
        
        selected = [ranked_sentences[0][0]]
        
        for sent, score, idx in ranked_sentences[1:]:
            is_diverse = True
            
            try:
                combined = selected + [sent]
                if len(combined) > 1:
                    tfidf = self.vectorizer.fit_transform(combined)
                    similarities = cosine_similarity(tfidf[-1:], tfidf[:-1])[0]
                    
                    if np.max(similarities) > diversity_threshold:
                        is_diverse = False
            except:
                pass
            
            if is_diverse:
                selected.append(sent)
        
        return selected
    
    def rank_with_mmr(self, sentences: List[str], query: str = None, 
                     lambda_param: float = 0.7, top_k: int = 5) -> List[str]:
         """Maximal Marginal Relevance ranking for diversity"""

         if not sentences:
             return []
         
         if len(sentences) <= top_k:
            return sentences
        
         if query is None:
             query = sentences[0]
         
         try:

            all_texts = [query] + sentences
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            query_vec = tfidf_matrix[0:1]
            sent_vecs = tfidf_matrix[1:]

            relevance = cosine_similarity(query_vec, sent_vecs)[0]
            
            selected_indices = []
            remaining_indices = list(range(len(sentences)))
            
            first_idx = np.argmax(relevance)
            selected_indices.append(first_idx)
            remaining_indices.remove(first_idx)

             
            while len(selected_indices) < top_k and remaining_indices:
                mmr_scores = []
                
                for idx in remaining_indices:
                    rel_score = relevance[idx]
                    
                    selected_vecs = sent_vecs[selected_indices]
                    current_vec = sent_vecs[idx:idx+1]
                    similarities = cosine_similarity(current_vec, selected_vecs)[0]
                    max_sim = np.max(similarities) if len(similarities) > 0 else 0
                    
                    mmr = lambda_param * rel_score - (1 - lambda_param) * max_sim
                    mmr_scores.append((idx, mmr))
                
                best_idx = max(mmr_scores, key=lambda x: x[1])[0]
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)
            
            selected_indices.sort()
            return [sentences[i] for i in selected_indices]
        
         except Exception as e:
            return sentences[:top_k]
            