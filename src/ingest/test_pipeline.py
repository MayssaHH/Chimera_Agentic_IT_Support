"""Test script for the ingestion pipeline."""

import os
import tempfile
from pathlib import Path

from src.ingest.pipeline import IngestionPipeline, DocumentLoader, MetadataExtractor, DocumentChunker


def create_test_documents():
    """Create test documents for testing."""
    test_dir = Path("test_docs")
    test_dir.mkdir(exist_ok=True)
    
    # Create test text file
    text_file = test_dir / "policy_001_v1.0_overview.txt"
    text_file.write_text("""
    Company Policy Overview
    Policy ID: POL-001
    Version: 1.0
    Effective Date: 2024-01-01
    Section: Overview
    
    This is a test policy document for the IT support system.
    It contains important information about company policies and procedures.
    All employees must follow these guidelines to ensure compliance.
    
    The policy covers various aspects including:
    - Security protocols
    - Data handling procedures
    - User access management
    - Incident response procedures
    
    This document will be processed by the ingestion pipeline
    to extract metadata and create vector embeddings.
    """)
    
    # Create test document with different metadata
    doc2 = test_dir / "security_policy_002_v2.1_security.txt"
    doc2.write_text("""
    Security Policy Document
    Policy ID: SEC-002
    Version: 2.1
    Effective Date: 2024-03-15
    Section: Security
    
    This document outlines the security requirements for all IT systems.
    It includes password policies, access controls, and data protection measures.
    
    Key security principles:
    1. Defense in depth
    2. Principle of least privilege
    3. Regular security audits
    4. Incident response planning
    
    All security incidents must be reported immediately to the IT security team.
    """)
    
    print(f"Created test documents in {test_dir}")
    return test_dir


def test_document_loader():
    """Test document loading functionality."""
    print("\n=== Testing Document Loader ===")
    
    test_dir = create_test_documents()
    loader = DocumentLoader()
    
    for doc_path in test_dir.glob("*.txt"):
        print(f"Loading: {doc_path.name}")
        doc = loader.load_document(doc_path)
        if doc:
            print(f"  - Content length: {len(doc.page_content)} characters")
            print(f"  - Metadata: {doc.metadata}")
        else:
            print(f"  - Failed to load document")


def test_metadata_extraction():
    """Test metadata extraction functionality."""
    print("\n=== Testing Metadata Extraction ===")
    
    test_dir = Path("test_docs")
    loader = DocumentLoader()
    extractor = MetadataExtractor()
    
    for doc_path in test_dir.glob("*.txt"):
        print(f"Processing: {doc_path.name}")
        doc = loader.load_document(doc_path)
        if doc:
            metadata = extractor.extract_metadata(doc, doc_path)
            print(f"  - Extracted metadata: {metadata}")


def test_chunking():
    """Test document chunking functionality."""
    print("\n=== Testing Document Chunking ===")
    
    test_dir = Path("test_docs")
    loader = DocumentLoader()
    chunker = DocumentChunker(max_tokens=100, overlap_tokens=20)
    
    for doc_path in test_dir.glob("*.txt"):
        print(f"Chunking: {doc_path.name}")
        doc = loader.load_document(doc_path)
        if doc:
            chunks = chunker.chunk_document(doc)
            print(f"  - Created {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                print(f"    Chunk {i}: {len(chunk.page_content)} chars, "
                      f"{chunk.metadata.get('chunk_tokens', 'N/A')} tokens")


def test_pipeline_integration():
    """Test the complete pipeline integration."""
    print("\n=== Testing Pipeline Integration ===")
    
    # Create a temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "vectorstore"
        
        try:
            # Initialize pipeline (without OpenAI API key for testing)
            pipeline = IngestionPipeline(
                storage_path=str(storage_path),
                store_type="chromadb"
            )
            
            print("Pipeline initialized successfully")
            print(f"Storage path: {storage_path}")
            print(f"Store type: {pipeline.vector_store.store_type}")
            
        except Exception as e:
            print(f"Pipeline initialization failed (expected without API key): {e}")


def cleanup_test_files():
    """Clean up test files."""
    import shutil
    
    test_dir = Path("test_docs")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("\nCleaned up test files")


def main():
    """Run all tests."""
    print("Running ingestion pipeline tests...")
    
    try:
        test_document_loader()
        test_metadata_extraction()
        test_chunking()
        test_pipeline_integration()
        
        print("\n=== All tests completed ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup_test_files()


if __name__ == "__main__":
    main()
