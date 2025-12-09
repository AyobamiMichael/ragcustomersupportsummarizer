"""
DistilBERT embedding and semantic re-ranking service
FIXED: Removed FP16 optimization that causes errors on CPU
"""

import torch
import numpy as np
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer, util

from ..config import get_settings
from ..models.schemas import EmbeddingResult


class EmbeddingService:
    """Service for semantic embeddings and re-ranking using DistilBERT"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"EmbeddingService initialized - Device: {self.device}")
    
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self.model is None:
            print(f"Loading sentence transformer model: {self.settings.SENTENCE_TRANSFORMER_MODEL}")
            try:
                self.model = SentenceTransformer(
                    self.settings.SENTENCE_TRANSFORMER_MODEL,
                    cache_folder=self.settings.MODEL_CACHE_DIR,
                    device=self.device
                )
                
                # ✅ REMOVED: FP16 optimization that causes errors on CPU
                # DO NOT convert to half precision on CPU
                # Only use FP16 on GPU if available
                if self.device.type == 'cuda':
                    try:
                        self.model = self.model.half()
                        print("✅ Model converted to FP16 for GPU")
                    except Exception as e:
                        print(f"⚠️  Could not convert to FP16: {e}")
                else:
                    print("✅ Using FP32 for CPU (stable)")
                
                print(f"✅ Model loaded successfully on {self.device}")
                
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                raise
    
    def encode_sentences(self, sentences: List[str], 
                        batch_size: int = None) -> torch.Tensor:
        """
        Encode sentences into embeddings
        
        Args:
            sentences: List of sentences to encode
            batch_size: Batch size for encoding
            
        Returns:
            Tensor of embeddings
        """
        self._load_model()
        
        if batch_size is None:
            batch_size = self.settings.BATCH_SIZE
        
        try:
            embeddings = self.model.encode(
                sentences,
                batch_size=batch_size,
                convert_to_tensor=True,
                show_progress_bar=False,
                device=self.device
            )
            return embeddings
            
        except Exception as e:
            print(f"Error encoding sentences: {e}")
            raise
    
    def rerank_with_embeddings(self, query: str, candidates: List[str], 
                              top_k: int = None) -> EmbeddingResult:
        """
        Re-rank candidate sentences using semantic similarity
        
        Args:
            query: Query text (e.g., original document or specific question)
            candidates: List of candidate sentences
            top_k: Number of top sentences to return
            
        Returns:
            EmbeddingResult with re-ranked sentences
        """
        if not candidates:
            return EmbeddingResult(
                embeddings=[],
                similarity_scores=[],
                top_indices=[]
            )
        
        if top_k is None:
            top_k = self.settings.SEMANTIC_TOP_K
        
        self._load_model()
        
        try:
            # Encode query and candidates
            query_embedding = self.model.encode(
                query, 
                convert_to_tensor=True,
                device=self.device
            )
            
            candidate_embeddings = self.model.encode(
                candidates,
                batch_size=self.settings.BATCH_SIZE,
                convert_to_tensor=True,
                device=self.device
            )
            
            # Calculate cosine similarity
            similarity_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
            
            # Get top k indices
            top_results = torch.topk(
                similarity_scores, 
                k=min(top_k, len(candidates))
            )
            
            top_indices = top_results.indices.cpu().numpy().tolist()
            top_scores = top_results.values.cpu().numpy().tolist()
            
            return EmbeddingResult(
                embeddings=candidate_embeddings.cpu().numpy().tolist(),
                similarity_scores=top_scores,
                top_indices=top_indices
            )
            
        except Exception as e:
            print(f"Error in rerank_with_embeddings: {e}")
            raise
    
    def semantic_search(self, query: str, corpus: List[str], 
                       top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Semantic search in a corpus of sentences
        
        Args:
            query: Search query
            corpus: List of sentences to search
            top_k: Number of results to return
            
        Returns:
            List of (index, score) tuples
        """
        self._load_model()
        
        try:
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True)
            
            hits = util.semantic_search(
                query_embedding, 
                corpus_embeddings, 
                top_k=top_k
            )[0]
            
            return [(hit['corpus_id'], hit['score']) for hit in hits]
            
        except Exception as e:
            print(f"Error in semantic_search: {e}")
            raise
    
    def calculate_similarity_matrix(self, sentences: List[str]) -> np.ndarray:
        """
        Calculate pairwise similarity matrix for sentences
        
        Args:
            sentences: List of sentences
            
        Returns:
            Similarity matrix (n x n)
        """
        if not sentences:
            return np.array([])
        
        self._load_model()
        
        try:
            embeddings = self.model.encode(
                sentences,
                convert_to_tensor=True,
                batch_size=self.settings.BATCH_SIZE
            )
            
            similarity_matrix = util.cos_sim(embeddings, embeddings)
            
            return similarity_matrix.cpu().numpy()
            
        except Exception as e:
            print(f"Error calculating similarity matrix: {e}")
            raise
    
    def cluster_sentences(self, sentences: List[str], 
                         num_clusters: int = 3) -> List[int]:
        """
        Cluster sentences using K-means on embeddings
        
        Args:
            sentences: List of sentences
            num_clusters: Number of clusters
            
        Returns:
            List of cluster labels
        """
        from sklearn.cluster import KMeans
        
        if len(sentences) < num_clusters:
            return list(range(len(sentences)))
        
        self._load_model()
        
        try:
            embeddings = self.model.encode(sentences)
            
            kmeans = KMeans(
                n_clusters=num_clusters, 
                random_state=42,
                n_init=10
            )
            labels = kmeans.fit_predict(embeddings)
            
            return labels.tolist()
            
        except Exception as e:
            print(f"Error clustering sentences: {e}")
            raise
    
    def find_representative_sentences(self, sentences: List[str], 
                                     num_representatives: int = 3) -> List[int]:
        """
        Find representative sentences using clustering
        
        Args:
            sentences: List of sentences
            num_representatives: Number of representatives to find
            
        Returns:
            Indices of representative sentences
        """
        if len(sentences) <= num_representatives:
            return list(range(len(sentences)))
        
        try:
            labels = self.cluster_sentences(sentences, num_representatives)
            embeddings = self.model.encode(sentences)
            
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=num_representatives, random_state=42)
            kmeans.fit(embeddings)
            
            representatives = []
            for i in range(num_representatives):
                cluster_indices = [j for j, label in enumerate(labels) if label == i]
                
                if cluster_indices:
                    cluster_embeddings = embeddings[cluster_indices]
                    center = kmeans.cluster_centers_[i]
                    distances = np.linalg.norm(cluster_embeddings - center, axis=1)
                    closest_idx = cluster_indices[np.argmin(distances)]
                    representatives.append(closest_idx)
            
            return sorted(representatives)
            
        except Exception as e:
            print(f"Error finding representative sentences: {e}")
            raise