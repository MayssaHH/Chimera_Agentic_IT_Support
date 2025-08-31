"""
Retrieve Node for IT Support Workflow

This node handles document retrieval, citation generation, deduplication,
and relevance scoring for IT support requests.
"""

import hashlib
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

from ..state import (
    ITGraphState, RetrievedDocument, Citation, RetrievedDocumentModel, CitationModel
)


@dataclass
class DocumentSection:
    """Represents a section within a document"""
    section_id: str
    title: str
    content: str
    start_pos: int
    end_pos: int
    level: int  # Heading level (1 = main, 2 = sub, etc.)


@dataclass
class RelevanceScore:
    """Relevance scoring for document sections"""
    section_id: str
    score: float
    factors: Dict[str, float]
    matched_terms: List[str]


class DocumentRetriever:
    """Handles document retrieval and processing"""
    
    def __init__(self, knowledge_base_client=None):
        self.kb_client = knowledge_base_client
        self.cache = {}
        
    def retrieve_documents(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Retrieve documents from knowledge base"""
        # Placeholder for actual KB integration
        # In real implementation, this would call the KB client
        if self.kb_client:
            return self.kb_client.search(query, max_results=max_results)
        
        # Mock implementation for development
        return self._mock_retrieval(query, max_results)
    
    def _mock_retrieval(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Mock document retrieval for development/testing"""
        # This would be replaced with actual KB search
        mock_docs = [
            {
                "doc_id": "IT_ACCESS_POLICY_001",
                "title": "IT Access Control Policy",
                "content": "This policy defines access control procedures for all IT systems...",
                "source": "IT_Policies",
                "document_type": "policy",
                "version": "2.1",
                "last_updated": "2024-01-15",
                "metadata": {"category": "security", "department": "IT"}
            },
            {
                "doc_id": "SOFTWARE_INSTALL_002", 
                "title": "Software Installation Guidelines",
                "content": "Guidelines for installing software on company devices...",
                "source": "IT_Procedures",
                "document_type": "procedure",
                "version": "1.3",
                "last_updated": "2024-01-10",
                "metadata": {"category": "operations", "department": "IT"}
            }
        ]
        return mock_docs[:max_results]


class DocumentProcessor:
    """Processes retrieved documents for sections and relevance"""
    
    def __init__(self):
        self.section_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^[A-Z][A-Z\s]+\n[-=]+\s*$',  # Underlined headers
            r'^\d+\.\s+(.+)$',  # Numbered sections
        ]
    
    def extract_sections(self, content: str, title: str) -> List[DocumentSection]:
        """Extract logical sections from document content"""
        sections = []
        
        # Add document title as main section
        sections.append(DocumentSection(
            section_id=f"main_{hashlib.md5(title.encode()).hexdigest()[:8]}",
            title=title,
            content=content,
            start_pos=0,
            end_pos=len(content),
            level=0
        ))
        
        # Extract markdown-style headers
        lines = content.split('\n')
        current_section = None
        
        for i, line in enumerate(lines):
            # Check for markdown headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                level = len(header_match.group(1))
                section_title = header_match.group(2).strip()
                
                # Close previous section if exists
                if current_section:
                    current_section.end_pos = i
                    sections.append(current_section)
                
                # Start new section
                section_id = f"section_{hashlib.md5(section_title.encode()).hexdigest()[:8]}"
                current_section = DocumentSection(
                    section_id=section_id,
                    title=section_title,
                    content="",
                    start_pos=i + 1,
                    end_pos=len(lines),
                    level=level
                )
        
        # Close last section
        if current_section:
            current_section.end_pos = len(lines)
            sections.append(current_section)
        
        # Extract content for each section
        for section in sections:
            if section.start_pos < len(lines):
                section.content = '\n'.join(lines[section.start_pos:section.end_pos]).strip()
        
        return sections
    
    def calculate_relevance(self, section: DocumentSection, query: str, 
                           request_context: Dict[str, Any]) -> RelevanceScore:
        """Calculate relevance score for a document section"""
        query_terms = set(query.lower().split())
        content_terms = set(section.content.lower().split())
        
        # Basic term matching
        matched_terms = query_terms.intersection(content_terms)
        term_match_score = len(matched_terms) / len(query_terms) if query_terms else 0
        
        # Context relevance
        context_score = self._calculate_context_relevance(section, request_context)
        
        # Section level relevance (main sections get higher scores)
        level_score = 1.0 / (section.level + 1) if section.level > 0 else 1.0
        
        # Content length relevance (prefer substantial content)
        length_score = min(len(section.content) / 1000, 1.0)  # Normalize to 0-1
        
        # Calculate weighted score
        factors = {
            "term_match": term_match_score * 0.4,
            "context": context_score * 0.3,
            "level": level_score * 0.2,
            "length": length_score * 0.1
        }
        
        total_score = sum(factors.values())
        
        return RelevanceScore(
            section_id=section.section_id,
            score=total_score,
            factors=factors,
            matched_terms=list(matched_terms)
        )

    def _calculate_context_relevance(self, section: DocumentSection, 
                                   request_context: Dict[str, Any]) -> float:
        """Calculate context-based relevance score"""
        context_score = 0.0
        
        # Check if section content matches request category
        if 'category' in request_context:
            category = request_context['category'].lower()
            if category in section.content.lower():
                context_score += 0.3
        
        # Check if section content matches department
        if 'department' in request_context:
            dept = request_context['department'].lower()
            if dept in section.content.lower():
                context_score += 0.2
        
        # Check if section content matches priority level
        if 'priority' in request_context:
            priority = request_context['priority'].lower()
            if priority in section.content.lower():
                context_score += 0.2
        
        # Check for policy-related terms
        policy_terms = ['policy', 'procedure', 'guideline', 'rule', 'requirement']
        policy_matches = sum(1 for term in policy_terms if term in section.content.lower())
        context_score += (policy_matches / len(policy_terms)) * 0.3
        
        return min(context_score, 1.0)


class DeduplicationEngine:
    """Handles document and content deduplication"""
    
    def __init__(self):
        self.content_hashes = set()
        self.similarity_threshold = 0.8
    
    def deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents based on content similarity"""
        unique_docs = []
        
        for doc in documents:
            content_hash = self._generate_content_hash(doc['content'])
            
            if content_hash not in self.content_hashes:
                self.content_hashes.add(content_hash)
                unique_docs.append(doc)
        
        return unique_docs
    
    def deduplicate_sections(self, sections: List[DocumentSection]) -> List[DocumentSection]:
        """Remove duplicate sections based on content similarity"""
        unique_sections = []
        
        for section in sections:
            if not self._is_duplicate_section(section, unique_sections):
                unique_sections.append(section)
        
        return unique_sections
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        # Normalize content for better deduplication
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _is_duplicate_section(self, section: DocumentSection, 
                            existing_sections: List[DocumentSection]) -> bool:
        """Check if section is duplicate of existing sections"""
        for existing in existing_sections:
            similarity = self._calculate_similarity(section.content, existing.content)
            if similarity > self.similarity_threshold:
                return True
        return False
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate content similarity using Jaccard similarity"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class CitationGenerator:
    """Generates citations from relevant document sections"""
    
    def __init__(self):
        self.citation_counter = 0
    
    def generate_citations(self, sections: List[DocumentSection], 
                          relevance_scores: List[RelevanceScore]) -> List[Citation]:
        """Generate citations from relevant document sections"""
        citations = []
        
        # Sort sections by relevance score
        scored_sections = [(section, score) for section, score in zip(sections, relevance_scores)]
        scored_sections.sort(key=lambda x: x[1].score, reverse=True)
        
        # Generate citations for top relevant sections
        for section, score in scored_sections[:5]:  # Top 5 most relevant
            if score.score > 0.3:  # Minimum relevance threshold
                citation = self._create_citation(section, score)
                citations.append(citation)
        
        return citations
    
    def _create_citation(self, section: DocumentSection, 
                        score: RelevanceScore) -> Citation:
        """Create a citation from a document section"""
        self.citation_counter += 1
        
        # Extract source document info from section
        source_parts = section.section_id.split('_')
        source = source_parts[0] if source_parts else "unknown"
        
        # Create relevance explanation
        relevance_factors = []
        if score.factors['term_match'] > 0.5:
            relevance_factors.append("high term match")
        if score.factors['context'] > 0.5:
            relevance_factors.append("contextually relevant")
        if score.factors['level'] > 0.5:
            relevance_factors.append("main section content")
        
        relevance = f"Relevant due to: {', '.join(relevance_factors)}"
        
        return Citation(
            source=source,
            text=section.content[:200] + "..." if len(section.content) > 200 else section.content,
            relevance=relevance,
            document_id=section.section_id,
            page_number=None,
            section=section.title if section.title != "main" else None
        )


def retrieve_node(state: ITGraphState) -> ITGraphState:
    """
    Retrieve node: fills retrieved_docs and citations based on user request
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with retrieved documents and citations
    """
    try:
        # Extract request information
        user_request = state.get('user_request', {})
        query = f"{user_request.get('title', '')} {user_request.get('description', '')}"
        
        # Initialize components
        retriever = DocumentRetriever()
        processor = DocumentProcessor()
        deduplicator = DeduplicationEngine()
        citation_gen = CitationGenerator()
        
        # Retrieve documents
        raw_documents = retriever.retrieve_documents(query, max_results=15)
        
        # Deduplicate documents
        unique_documents = deduplicator.deduplicate_documents(raw_documents)
        
        # Process documents and extract sections
        all_sections = []
        for doc in unique_documents:
            sections = processor.extract_sections(doc['content'], doc['title'])
            all_sections.extend(sections)
        
        # Deduplicate sections
        unique_sections = deduplicator.deduplicate_sections(all_sections)
        
        # Calculate relevance scores
        relevance_scores = []
        for section in unique_sections:
            score = processor.calculate_relevance(section, query, user_request)
            relevance_scores.append(score)
        
        # Generate citations
        citations = citation_gen.generate_citations(unique_sections, relevance_scores)
        
        # Convert to RetrievedDocument format
        retrieved_docs = []
        for doc in unique_documents:
            retrieved_doc = RetrievedDocument(
                doc_id=doc['doc_id'],
                title=doc['title'],
                content=doc['content'],
                source=doc['source'],
                relevance_score=max(score.score for score in relevance_scores 
                                  if score.section_id.startswith(doc['doc_id'])),
                retrieval_date=datetime.now(),
                document_type=doc['document_type'],
                version=doc['version'],
                last_updated=datetime.fromisoformat(doc['last_updated']) if isinstance(doc['last_updated'], str) else doc['last_updated'],
                metadata=doc.get('metadata', {})
            )
            retrieved_docs.append(retrieved_doc)
        
        # Update state
        state['retrieved_docs'] = retrieved_docs
        state['citations'] = citations
        
        # Add retrieval metadata to state
        if 'metadata' not in state:
            state['metadata'] = {}
        state['metadata']['retrieval'] = {
            'query': query,
            'documents_retrieved': len(retrieved_docs),
            'sections_processed': len(unique_sections),
            'citations_generated': len(citations),
            'retrieval_timestamp': datetime.now().isoformat(),
            'deduplication_applied': True
        }
        
        return state
        
    except Exception as e:
        # Handle errors gracefully
        error_record = {
            'error_id': f"retrieval_error_{datetime.now().timestamp()}",
            'timestamp': datetime.now(),
            'error_type': 'retrieval_error',
            'message': f"Error in retrieve node: {str(e)}",
            'stack_trace': None,
            'context': {'node': 'retrieve', 'state_keys': list(state.keys())},
            'severity': 'medium',
            'resolved': False,
            'resolution_notes': None
        }
        
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(error_record)
        
        # Return state with empty retrieval results
        state['retrieved_docs'] = []
        state['citations'] = []
        
        return state


# Convenience functions for testing and direct usage
def create_retrieved_document_model(doc_data: Dict[str, Any]) -> RetrievedDocumentModel:
    """Create a RetrievedDocumentModel from dictionary data"""
    return RetrievedDocumentModel(**doc_data)


def create_citation_model(citation_data: Dict[str, Any]) -> CitationModel:
    """Create a CitationModel from dictionary data"""
    return CitationModel(**citation_data)


def test_retrieve_node():
    """Test function for the retrieve node"""
    # Create test state
    test_state = {
        'user_request': {
            'title': 'Database Access Request',
            'description': 'Need access to customer database for analytics',
            'category': 'access_control',
            'department': 'data_science'
        },
        'retrieved_docs': [],
        'citations': []
    }
    
    # Run retrieve node
    result_state = retrieve_node(test_state)
    
    print(f"Retrieved {len(result_state['retrieved_docs'])} documents")
    print(f"Generated {len(result_state['citations'])} citations")
    
    return result_state


if __name__ == "__main__":
    # Run test if executed directly
    test_retrieve_node()
