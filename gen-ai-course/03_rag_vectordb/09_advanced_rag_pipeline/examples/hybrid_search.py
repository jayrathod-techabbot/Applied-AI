"""
Hybrid Search Implementation
Combines vector search with keyword search using RRF
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

try:
    from rank_bm25 import BM25Okapi
    from langchain_core.documents import Document
except ImportError:
    pass


@dataclass
class SearchResult:
    """Standardized search result"""
    content: str
    score: float
    metadata: Dict
    source: str


class HybridRetriever:
    """Hybrid search combining vector and keyword search"""
    
    def __init__(self, vector_db, top_k: int = 5, rrf_k: int = 60):
        self.vector_db = vector_db
        self.top_k = top_k
        self.rrf_k = rrf_k
        self.keyword_index = None
        self.tokenized_docs = None
    
    def build_keyword_index(self, documents: List[Document]):
        """Build BM25 keyword index"""
        self.tokenized_docs = []
        clean_docs = []
        
        for doc in documents:
            tokens = doc.page_content.lower().split()
            self.tokenized_docs.append(tokens)
            clean_docs.append(doc)
        
        self.keyword_index = BM25Okapi(self.tokenized_docs)
    
    def vector_search(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        """Perform vector similarity search"""
        k = k or self.top_k
        return self.vector_db.similarity_search_with_score(query, k=k * 2)
    
    def keyword_search(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        """Perform BM25 keyword search"""
        k = k or self.top_k
        
        if not self.keyword_index:
            return []
        
        query_tokens = query.lower().split()
        scores = self.keyword_index.get_scores(query_tokens)
        
        # Get top k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k * 2]
        
        # Return top documents with scores
        results = []
        for idx in top_indices:
            doc = Document(
                page_content=" ".join(self.tokenized_docs[idx]),
                metadata={}
            )
            results.append((doc, scores[idx]))
        
        return results
    
    def reciprocal_rank_fusion(self, 
                             result_sets: List[List[Tuple[Document, float]]], 
                             k: int = 60) -> List[Document]:
        """
        Combine multiple result sets using RRF
        RRF Score = sum(1 / (k + rank)) for each result set
        """
        doc_scores = {}
        doc_map = {}
        
        for result_set in result_sets:
            for rank, (doc, _) in enumerate(result_set):
                doc_key = doc.metadata.get('chunk_id', id(doc))
                
                if doc_key not in doc_map:
                    doc_map[doc_key] = doc
                
                rrf_score = 1 / (k + rank)
                doc_scores[doc_key] = doc_scores.get(doc_key, 0) + rrf_score
        
        # Sort by RRF score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [doc_map[key] for key, _ in sorted_docs[:self.top_k]]
    
    def retrieve(self, query: str, use_keyword: bool = True) -> List[Document]:
        """Perform hybrid retrieval"""
        # Vector search
        vector_results = self.vector_search(query)
        
        if use_keyword and self.keyword_index:
            # Keyword search
            keyword_results = self.keyword_search(query)
            
            # Combine using RRF
            return self.reciprocal_rank_fusion([vector_results, keyword_results])
        
        # Return only vector results
        return [doc for doc, _ in vector_results[:self.top_k]]


class HybridSearchWithReranking:
    """Hybrid search with cross-encoder reranking"""
    
    def __init__(self, hybrid_retriever, reranker_model=None):
        self.hybrid = hybrid_retriever
        self.reranker = reranker_model
    
    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents using cross-encoder"""
        if not self.reranker:
            return documents
        
        # Compute scores
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.reranker.predict(pairs)
        
        # Sort by score
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs]
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """Retrieve and rerank"""
        # Get more candidates than needed
        candidates = self.hybrid.retrieve(query, top_k * 2)
        
        # Rerank
        return self.rerank(query, candidates)[:top_k]


if __name__ == "__main__":
    # Example usage
    print("Hybrid Search Example")
    print("=" * 50)
    
    # Initialize (would need actual vector_db)
    # retriever = HybridRetriever(vector_db)
    # retriever.build_keyword_index(documents)
    # results = retriever.retrieve("your query here")