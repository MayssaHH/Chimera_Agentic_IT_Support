"""Test file for the hybrid retriever."""

import pytest
from unittest.mock import Mock, patch
import tempfile
import shutil
from pathlib import Path

from .retriever import HybridRetriever, BM25Retriever, VectorRetriever, DocWithScore


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            'id': 'doc1',
            'title': 'IT Security Policy',
            'content': 'This policy outlines security requirements for all employees. Section 1.1 covers password requirements. Section 1.2 covers access controls.',
            'category': 'security',
            'source_type': 'policy',
            'tags': ['security', 'passwords', 'access']
        },
        {
            'id': 'doc2',
            'title': 'Data Access Guidelines',
            'content': 'Guidelines for accessing company data. Section 2.1 discusses data classification. Section 2.2 covers access permissions.',
            'category': 'access',
            'source_type': 'guideline',
            'tags': ['data', 'access', 'permissions']
        },
        {
            'id': 'doc3',
            'title': 'Software Installation Procedure',
            'content': 'Procedure for installing software on company devices. Chapter 3 covers approval process. Part 4 discusses installation steps.',
            'category': 'software',
            'source_type': 'procedure',
            'tags': ['software', 'installation', 'approval']
        }
    ]


@pytest.fixture
def temp_dir():
    """Temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestBM25Retriever:
    """Test BM25 retriever functionality."""
    
    def test_add_documents(self, sample_documents):
        """Test adding documents to BM25 retriever."""
        retriever = BM25Retriever()
        retriever.add_documents(sample_documents)
        
        assert len(retriever.documents) == 3
        assert len(retriever.doc_lengths) == 3
        assert retriever.avg_doc_length > 0
        assert len(retriever.idf) > 0
    
    def test_search(self, sample_documents):
        """Test BM25 search functionality."""
        retriever = BM25Retriever()
        retriever.add_documents(sample_documents)
        
        results = retriever.search("password security", k=2)
        assert len(results) == 2
        assert all(isinstance(result, tuple) for result in results)
        assert all(len(result) == 2 for result in results)
        
        # First result should be the security policy
        first_doc_idx = results[0][0]
        assert sample_documents[first_doc_idx]['title'] == 'IT Security Policy'


class TestVectorRetriever:
    """Test vector retriever functionality."""
    
    @patch('chromadb.PersistentClient')
    def test_initialization(self, mock_client, temp_dir):
        """Test vector retriever initialization."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        retriever = VectorRetriever(temp_dir)
        assert retriever.client is not None
    
    @patch('chromadb.PersistentClient')
    def test_add_documents(self, mock_client, temp_dir, sample_documents):
        """Test adding documents to vector retriever."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        retriever = VectorRetriever(temp_dir)
        retriever.add_documents(sample_documents)
        
        # Verify collection.add was called
        mock_collection.add.assert_called_once()
        call_args = mock_collection.add.call_args
        assert len(call_args[1]['documents']) == 3
        assert len(call_args[1]['ids']) == 3


class TestHybridRetriever:
    """Test hybrid retriever functionality."""
    
    @patch('chromadb.PersistentClient')
    def test_initialization(self, mock_client, temp_dir):
        """Test hybrid retriever initialization."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        retriever = HybridRetriever(temp_dir)
        assert retriever.bm25_retriever is not None
        assert retriever.vector_retriever is not None
        assert retriever.bm25_weight == 0.4
        assert retriever.vector_weight == 0.6
    
    @patch('chromadb.PersistentClient')
    def test_add_documents(self, mock_client, temp_dir, sample_documents):
        """Test adding documents to hybrid retriever."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        retriever = HybridRetriever(temp_dir)
        retriever.add_documents(sample_documents)
        
        assert len(retriever.documents) == 3
        assert len(retriever.doc_id_to_idx) == 3
        assert 'doc1' in retriever.doc_id_to_idx
    
    @patch('chromadb.PersistentClient')
    def test_retrieve(self, mock_client, temp_dir, sample_documents):
        """Test document retrieval."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        retriever = HybridRetriever(temp_dir)
        retriever.add_documents(sample_documents)
        
        # Mock vector search results
        mock_collection.query.return_value = {
            'ids': [['doc1', 'doc2']],
            'distances': [[0.1, 0.3]]
        }
        
        results = retriever.retrieve("password security", k=2)
        assert len(results) == 2
        assert all(isinstance(result, DocWithScore) for result in results)
        assert results[0].source_title == 'IT Security Policy'
    
    @patch('chromadb.PersistentClient')
    def test_retrieve_citations(self, mock_client, temp_dir, sample_documents):
        """Test citation retrieval."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        retriever = HybridRetriever(temp_dir)
        retriever.add_documents(sample_documents)
        
        # Mock vector search results - return all 3 documents
        mock_collection.query.return_value = {
            'ids': [['doc1', 'doc2', 'doc3']],
            'distances': [[0.1, 0.3, 0.5]]
        }
        
        citations = retriever.retrieve_citations("password security")
        assert len(citations) == 3
        assert all(citation.source_type in ['policy', 'guideline', 'procedure'] for citation in citations)
        assert citations[0].source_title == 'It Security Policy'
    
    def test_canonicalize_title(self, temp_dir):
        """Test title canonicalization."""
        retriever = HybridRetriever(temp_dir)
        
        # Test various title formats
        assert retriever._canonicalize_title("IT Policy - Security Requirements") == "Security Requirements"
        assert retriever._canonicalize_title("Technology Procedure: Data Access") == "Data Access"
        assert retriever._canonicalize_title("Information Guideline - Compliance") == "Compliance"
        assert retriever._canonicalize_title("") == "Unknown Policy"
    
    def test_extract_section(self, temp_dir):
        """Test section extraction."""
        retriever = HybridRetriever(temp_dir)
        
        content1 = "Section 1.1 covers password requirements."
        content2 = "Chapter 3 discusses the approval process."
        content3 = "Part 4 outlines installation steps."
        content4 = "No section information here."
        
        assert retriever._extract_section(content1) == "1.1"
        assert retriever._extract_section(content2) == "3"
        assert retriever._extract_section(content3) == "4"
        assert retriever._extract_section(content4) is None
    
    def test_create_section_anchor(self, temp_dir):
        """Test section anchor creation."""
        retriever = HybridRetriever(temp_dir)
        
        assert retriever._create_section_anchor("1.1") == "section-1.1"
        assert retriever._create_section_anchor("3") == "section-3"
        assert retriever._create_section_anchor("") is None


def test_integration_example(temp_dir, sample_documents):
    """Integration test showing full workflow."""
    with patch('chromadb.PersistentClient'):
        # Initialize retriever
        retriever = HybridRetriever(temp_dir)
        
        # Add documents
        retriever.add_documents(sample_documents)
        
        # Mock vector search
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['doc1', 'doc2', 'doc3']],
            'distances': [[0.1, 0.3, 0.5]]
        }
        retriever.vector_retriever.collection = mock_collection
        
        # Test retrieval
        results = retriever.retrieve("security access", k=3)
        assert len(results) == 3
        
        # Test citations
        citations = retriever.retrieve_citations("security access")
        assert len(citations) == 3
        
        # Test document management
        doc = retriever.get_document_by_id('doc1')
        assert doc is not None
        assert doc['title'] == 'IT Security Policy'


if __name__ == "__main__":
    # Example usage
    print("Running hybrid retriever example...")
    
    # Create sample documents
    sample_docs = [
        {
            'id': 'policy1',
            'title': 'IT Security Policy',
            'content': 'This policy outlines security requirements for all employees. Section 1.1 covers password requirements.',
            'category': 'security',
            'source_type': 'policy',
            'tags': ['security', 'passwords']
        }
    ]
    
    # Initialize retriever (with mocked ChromaDB for demo)
    with patch('chromadb.PersistentClient'):
        retriever = HybridRetriever()
        retriever.add_documents(sample_docs)
        
        # Mock vector search results
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['policy1']],
            'distances': [[0.1]]
        }
        retriever.vector_retriever.collection = mock_collection
        
        # Test retrieval
        results = retriever.retrieve("password security")
        print(f"Retrieved {len(results)} documents")
        
        # Test citations
        citations = retriever.retrieve_citations("password security")
        print(f"Generated {len(citations)} citations")
        
        for citation in citations:
            print(f"- {citation.source_title}: {citation.content[:100]}...")
    
    print("Example completed successfully!")
