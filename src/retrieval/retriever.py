"""Hybrid retriever combining BM25, vector search, and RRF fusion."""

import re
import uuid
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import chromadb
from chromadb.config import Settings

from ..domain.schemas import Citation


@dataclass
class DocWithScore:
    """Document with relevance score."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source_type: str
    source_title: str
    source_section: Optional[str] = None


class BM25Retriever:
    """BM25 retriever for text-based search."""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_lengths = []
        self.avg_doc_length = 0.0
        self.idf = {}
        self.term_freq = []
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the index."""
        self.documents = documents
        
        # Calculate document lengths
        self.doc_lengths = [len(doc['content'].split()) for doc in documents]
        self.avg_doc_length = np.mean(self.doc_lengths) if self.doc_lengths else 0.0
        
        # Build TF-IDF matrix
        texts = [doc['content'] for doc in documents]
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=10000
        )
        
        tf_matrix = vectorizer.fit_transform(texts)
        self.term_freq = tf_matrix.toarray()
        
        # Calculate IDF values
        feature_names = vectorizer.get_feature_names_out()
        for i, term in enumerate(feature_names):
            doc_freq = np.sum(self.term_freq[:, i] > 0)
            self.idf[term] = np.log((len(documents) - doc_freq + 0.5) / (doc_freq + 0.5))
    
    def search(self, query: str, k: int = 8) -> List[Tuple[int, float]]:
        """Search documents using BM25 scoring."""
        if not self.documents:
            return []
            
        query_terms = query.lower().split()
        scores = []
        
        for doc_idx, doc in enumerate(self.documents):
            score = 0.0
            doc_length = self.doc_lengths[doc_idx]
            
            for term in query_terms:
                if term in self.idf:
                    term_idx = list(self.idf.keys()).index(term)
                    tf = self.term_freq[doc_idx, term_idx]
                    
                    # BM25 scoring
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                    score += self.idf[term] * (numerator / denominator)
            
            scores.append((doc_idx, score))
        
        # Sort by score and return top k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


class VectorRetriever:
    """Vector-based retriever using ChromaDB."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists."""
        try:
            self.collection = self.client.get_collection("policy_documents")
        except:
            self.collection = self.client.create_collection(
                name="policy_documents",
                metadata={"description": "Policy documents for IT support"}
            )
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector index."""
        if not documents:
            return
            
        # Prepare documents for ChromaDB
        ids = [doc.get('id', str(uuid.uuid4())) for doc in documents]
        texts = [doc['content'] for doc in documents]
        metadatas = [
            {
                'title': doc.get('title', ''),
                'category': doc.get('category', ''),
                'source_type': doc.get('source_type', 'policy'),
                'tags': ','.join(doc.get('tags', [])),
                **{k: v for k, v in doc.items() if k not in ['id', 'content', 'title', 'category', 'source_type', 'tags']}
            }
            for doc in documents
        ]
        
        # Add to collection
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query: str, k: int = 8, filters: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float]]:
        """Search documents using vector similarity."""
        if not self.collection:
            return []
        
        # Apply filters if provided
        where = None
        if filters:
            where = {}
            for key, value in filters.items():
                if key in ['category', 'source_type']:
                    where[key] = value
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where
        )
        
        if results['ids'] and results['distances']:
            return list(zip(results['ids'][0], results['distances'][0]))
        return []


class HybridRetriever:
    """Hybrid retriever combining BM25, vector search, and RRF fusion."""
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 bm25_weight: float = 0.4,
                 vector_weight: float = 0.6,
                 rrf_k: float = 60.0):
        self.bm25_retriever = BM25Retriever()
        self.vector_retriever = VectorRetriever(persist_directory)
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k
        self.documents = []
        self.doc_id_to_idx = {}
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to both retrievers."""
        self.documents = documents
        self.doc_id_to_idx = {doc.get('id', str(i)): i for i, doc in enumerate(documents)}
        
        # Add to both retrievers
        self.bm25_retriever.add_documents(documents)
        self.vector_retriever.add_documents(documents)
    
    def _reciprocal_rank_fusion(self, 
                               bm25_results: List[Tuple[int, float]], 
                               vector_results: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Apply Reciprocal Rank Fusion to combine results."""
        scores = {}
        
        # Process BM25 results
        for rank, (doc_idx, score) in enumerate(bm25_results):
            doc_id = self.documents[doc_idx].get('id', str(doc_idx))
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + self.bm25_weight * rrf_score
        
        # Process vector results
        for rank, (doc_id, distance) in enumerate(vector_results):
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + self.vector_weight * rrf_score
        
        # Sort by combined score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores
    
    def retrieve(self, query: str, k: int = 8, filters: Optional[Dict[str, Any]] = None) -> List[DocWithScore]:
        """Retrieve documents using hybrid search."""
        if not self.documents:
            return []
        
        # Get results from both retrievers
        bm25_results = self.bm25_retriever.search(query, k=k*2)  # Get more candidates for fusion
        vector_results = self.vector_retriever.search(query, k=k*2, filters=filters)
        
        # Apply RRF fusion
        fused_scores = self._reciprocal_rank_fusion(bm25_results, vector_results)
        
        # Convert to DocWithScore objects
        results = []
        for doc_id, score in fused_scores[:k]:
            if doc_id in self.doc_id_to_idx:
                doc_idx = self.doc_id_to_idx[doc_id]
                doc = self.documents[doc_idx]
                
                # Extract section if available
                source_section = self._extract_section(doc.get('content', ''))
                
                results.append(DocWithScore(
                    id=doc_id,
                    content=doc.get('content', ''),
                    metadata=doc,
                    score=score,
                    source_type=doc.get('source_type', 'policy'),
                    source_title=doc.get('title', ''),
                    source_section=source_section
                ))
        
        return results
    
    def _extract_section(self, content: str) -> Optional[str]:
        """Extract section information from content."""
        # Look for common section patterns
        section_patterns = [
            r'Section\s+(\d+[\.\d]*)',
            r'(\d+[\.\d]*)\s*[A-Z][^.]*',
            r'Chapter\s+(\d+)',
            r'Part\s+(\d+)'
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, content[:500])  # Check first 500 chars
            if match:
                return match.group(1)
        return None
    
    def retrieve_citations(self, query: str) -> List[Citation]:
        """Retrieve citations with canonicalized policy titles and section anchors."""
        documents = self.retrieve(query, k=8)
        citations = []
        
        for doc in documents:
            # Canonicalize policy title
            canonical_title = self._canonicalize_title(doc.source_title)
            
            # Create section anchor
            section_anchor = self._create_section_anchor(doc.source_section) if doc.source_section else None
            
            citation = Citation(
                id=str(uuid.uuid4()),
                source_type=doc.source_type,
                source_id=doc.id,
                source_title=canonical_title,
                source_url=None,  # Could be added if URLs are available
                content=doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                relevance_score=min(doc.score, 1.0),  # Ensure score is between 0 and 1
                page_number=None,
                section=section_anchor
            )
            citations.append(citation)
        
        return citations
    
    def _canonicalize_title(self, title: str) -> str:
        """Canonicalize policy title for consistent citation."""
        if not title:
            return "Unknown Policy"
        
        # Remove common prefixes and normalize
        title = title.strip()
        title = re.sub(r'^(IT\s+|Technology\s+|Information\s+)?(Policy|Procedure|Guideline|Standard)\s*[-:]\s*', '', title, flags=re.IGNORECASE)
        
        # Capitalize properly
        title = title.title()
        
        # Ensure it's not empty after cleaning
        if not title:
            return "Policy Document"
        
        return title
    
    def _create_section_anchor(self, section: str) -> str:
        """Create a section anchor for citations."""
        if not section:
            return None
        
        # Clean section identifier
        section = re.sub(r'[^\w\d\.]', '', section)
        return f"section-{section.lower()}"
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by its ID."""
        if doc_id in self.doc_id_to_idx:
            return self.documents[self.doc_id_to_idx[doc_id]]
        return None
    
    def update_document(self, doc_id: str, updated_doc: Dict[str, Any]):
        """Update a document in the index."""
        if doc_id in self.doc_id_to_idx:
            idx = self.doc_id_to_idx[doc_id]
            self.documents[idx] = updated_doc
            
            # Rebuild both indices
            self.bm25_retriever.add_documents(self.documents)
            self.vector_retriever.add_documents(self.documents)
    
    def remove_document(self, doc_id: str):
        """Remove a document from the index."""
        if doc_id in self.doc_id_to_idx:
            idx = self.doc_id_to_idx[doc_id]
            del self.documents[idx]
            
            # Rebuild indices
            self.doc_id_to_idx = {doc.get('id', str(i)): i for i, doc in enumerate(self.documents)}
            self.bm25_retriever.add_documents(self.documents)
            self.vector_retriever.add_documents(self.documents)
