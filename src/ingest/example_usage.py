"""Example usage of the ingestion pipeline."""

import os
from pathlib import Path

from pipeline import IngestionPipeline, DocumentLoader, MetadataExtractor, DocumentChunker


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Some operations will fail.")
        print("   Set it with: export OPENAI_API_KEY='your_key_here'")
        return
    
    # Initialize pipeline
    pipeline = IngestionPipeline(
        storage_path="./storage/vectorstore",
        store_type="chromadb"
    )
    
    # Process documents (assuming you have a company_docs directory)
    docs_dir = "./company_docs"
    if Path(docs_dir).exists():
        print(f"Processing documents from {docs_dir}...")
        pipeline.process_directory(docs_dir)
    else:
        print(f"Directory {docs_dir} not found. Create it and add some documents first.")


def example_component_usage():
    """Example of using individual components."""
    print("\n=== Component Usage Example ===")
    
    # Create a test document
    test_doc = Path("test_example.txt")
    test_doc.write_text("""
    Company Policy Example
    Policy ID: EX-001
    Version: 1.0
    Effective Date: 2024-01-01
    Section: General
    
    This is an example policy document.
    It demonstrates the metadata extraction capabilities.
    """)
    
    try:
        # Load document
        loader = DocumentLoader()
        doc = loader.load_document(test_doc)
        if doc:
            print(f"✅ Document loaded: {len(doc.page_content)} characters")
            
            # Extract metadata
            extractor = MetadataExtractor()
            metadata = extractor.extract_metadata(doc, test_doc)
            print(f"✅ Metadata extracted: {metadata}")
            
            # Chunk document
            chunker = DocumentChunker(max_tokens=50, overlap_tokens=10)
            chunks = chunker.chunk_document(doc)
            print(f"✅ Document chunked into {len(chunks)} pieces")
            
            for i, chunk in enumerate(chunks):
                print(f"   Chunk {i}: {len(chunk.page_content)} chars")
        
    finally:
        # Clean up
        if test_doc.exists():
            test_doc.unlink()
            print("🧹 Cleaned up test file")


def example_custom_chunking():
    """Example of custom chunking settings."""
    print("\n=== Custom Chunking Example ===")
    
    # Create a longer test document
    test_doc = Path("test_long.txt")
    test_doc.write_text("""
    This is a longer document that will be split into multiple chunks.
    Each chunk will have a maximum of 100 tokens with 20 tokens of overlap.
    This ensures that important context is maintained between chunks.
    
    The chunking process uses the tiktoken library to accurately count tokens.
    This is more precise than character-based splitting and ensures
    that the chunks respect token boundaries from the language model.
    
    Overlap between chunks helps maintain context and improves
    the quality of semantic search results when querying the vector store.
    
    The pipeline automatically adds metadata to each chunk including
    the chunk ID, total number of chunks, and token count.
    """)
    
    try:
        # Load and chunk with custom settings
        loader = DocumentLoader()
        doc = loader.load_document(test_doc)
        
        if doc:
            # Custom chunking: 100 tokens max, 20 tokens overlap
            chunker = DocumentChunker(max_tokens=100, overlap_tokens=20)
            chunks = chunker.chunk_document(doc)
            
            print(f"✅ Custom chunking: {len(chunks)} chunks created")
            print(f"   Max tokens per chunk: 100")
            print(f"   Overlap tokens: 20")
            
            for i, chunk in enumerate(chunks):
                tokens = chunk.metadata.get('chunk_tokens', 'N/A')
                print(f"   Chunk {i}: {tokens} tokens")
    
    finally:
        # Clean up
        if test_doc.exists():
            test_doc.unlink()
            print("🧹 Cleaned up test file")


def example_vector_store_options():
    """Example of different vector store options."""
    print("\n=== Vector Store Options Example ===")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Skipping vector store examples.")
        return
    
    # ChromaDB example
    print("ChromaDB (default):")
    try:
        chroma_pipeline = IngestionPipeline(
            storage_path="./storage/vectorstore/chromadb",
            store_type="chromadb"
        )
        print("   ✅ ChromaDB pipeline initialized")
    except Exception as e:
        print(f"   ❌ ChromaDB failed: {e}")
    
    # FAISS example
    print("FAISS:")
    try:
        faiss_pipeline = IngestionPipeline(
            storage_path="./storage/vectorstore/faiss",
            store_type="faiss"
        )
        print("   ✅ FAISS pipeline initialized")
    except Exception as e:
        print(f"   ❌ FAISS failed: {e}")


def main():
    """Run all examples."""
    print("🚀 Ingestion Pipeline Examples")
    print("=" * 50)
    
    example_basic_usage()
    example_component_usage()
    example_custom_chunking()
    example_vector_store_options()
    
    print("\n" + "=" * 50)
    print("✨ Examples completed!")
    print("\nTo run the full pipeline:")
    print("  python -m src.ingest.pipeline ./company_docs")
    print("\nTo run tests:")
    print("  python -m src.ingest.test_pipeline")


if __name__ == "__main__":
    main()
