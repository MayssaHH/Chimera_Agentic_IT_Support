"""Document ingestion pipeline with chunking and vector storage."""

import argparse
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default embedding model
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"


class DocumentLoader:
    """Handles loading of different document types."""
    
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    
    @staticmethod
    def load_document(file_path: Path) -> Optional[Document]:
        """Load a document based on its file extension."""
        try:
            if file_path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file_path))
                docs = loader.load()
                return docs[0] if docs else None
            elif file_path.suffix.lower() == ".docx":
                loader = UnstructuredWordDocumentLoader(str(file_path))
                docs = loader.load()
                return docs[0] if docs else None
            elif file_path.suffix.lower() == ".txt":
                loader = TextLoader(str(file_path))
                docs = loader.load()
                return docs[0] if docs else None
            else:
                logger.warning(f"Unsupported file type: {file_path.suffix}")
                return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None


class MetadataExtractor:
    """Extracts metadata from documents."""
    
    @staticmethod
    def extract_metadata(doc: Document, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from document content and filename."""
        metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "file_type": file_path.suffix.lower(),
            "file_size": file_path.stat().st_size,
        }
        
        # Try to extract policy_id from filename or content
        policy_id = MetadataExtractor._extract_policy_id(file_path.name, doc.page_content)
        if policy_id:
            metadata["policy_id"] = policy_id
        
        # Try to extract version from filename or content
        version = MetadataExtractor._extract_version(file_path.name, doc.page_content)
        if version:
            metadata["version"] = version
        
        # Try to extract effective_date from filename or content
        effective_date = MetadataExtractor._extract_effective_date(file_path.name, doc.page_content)
        if effective_date:
            metadata["effective_date"] = effective_date
        
        # Try to extract section from filename or content
        section = MetadataExtractor._extract_section(file_path.name, doc.page_content)
        if section:
            metadata["section"] = section
        
        return metadata
    
    @staticmethod
    def _extract_policy_id(filename: str, content: str) -> Optional[str]:
        """Extract policy ID from filename or content."""
        # Common patterns for policy IDs
        patterns = [
            r"policy[_-]?(\d+)",
            r"(\d{3,})",
            r"POL[_-]?(\d+)",
            r"(\w{2,3}-\d{3,})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Search in content
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_version(filename: str, content: str) -> Optional[str]:
        """Extract version from filename or content."""
        patterns = [
            r"v(\d+\.\d+)",
            r"version[_-]?(\d+\.\d+)",
            r"ver[_-]?(\d+\.\d+)",
            r"(\d+\.\d+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Search in content
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_effective_date(filename: str, content: str) -> Optional[str]:
        """Extract effective date from filename or content."""
        patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}-\d{2}-\d{4})",
            r"(\d{2}/\d{2}/\d{4})",
            r"effective[_-]?(\d{4})",
            r"(\d{4})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Search in content
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_section(filename: str, content: str) -> Optional[str]:
        """Extract section from filename or content."""
        # Common section names
        sections = [
            "overview", "introduction", "scope", "definitions", "policy", "procedures",
            "compliance", "enforcement", "exceptions", "references", "appendix",
            "general", "specific", "technical", "administrative", "security"
        ]
        
        # Check filename
        for section in sections:
            if section.lower() in filename.lower():
                return section.title()
        
        # Check content (first few lines)
        first_lines = content[:500].lower()
        for section in sections:
            if section.lower() in first_lines:
                return section.title()
        
        return None


class DocumentChunker:
    """Handles document chunking with token counting."""
    
    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 120):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Convert tokens to characters (approximate)
        # Average English word is ~5 characters, average token is ~4 characters
        self.max_chars = int(max_tokens * 4)
        self.overlap_chars = int(overlap_tokens * 4)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chars,
            chunk_overlap=self.overlap_chars,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_document(self, doc: Document) -> List[Document]:
        """Chunk a document into smaller pieces."""
        try:
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = i
                chunk.metadata["total_chunks"] = len(chunks)
                chunk.metadata["chunk_tokens"] = len(self.tokenizer.encode(chunk.page_content))
            
            logger.info(f"Split document into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            return [doc]


class VectorStore:
    """Manages vector store operations."""
    
    def __init__(self, storage_path: str = "./storage/vectorstore", store_type: str = "chromadb"):
        self.storage_path = Path(storage_path)
        self.store_type = store_type.lower()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=DEFAULT_EMBEDDING_MODEL,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize vector store
        self.vector_store = self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the appropriate vector store."""
        if self.store_type == "chromadb":
            return self._init_chromadb()
        elif self.store_type == "faiss":
            return self._init_faiss()
        else:
            logger.warning(f"Unknown store type: {self.store_type}, using ChromaDB")
            return self._init_chromadb()
    
    def _init_chromadb(self):
        """Initialize ChromaDB vector store."""
        try:
            # Create ChromaDB client
            chroma_client = chromadb.PersistentClient(
                path=str(self.storage_path / "chromadb"),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            collection = chroma_client.get_or_create_collection(
                name="company_documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            return Chroma(
                client=chroma_client,
                collection_name="company_documents",
                embedding_function=self.embeddings
            )
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def _init_faiss(self):
        """Initialize FAISS vector store."""
        try:
            faiss_path = self.storage_path / "faiss"
            faiss_path.mkdir(exist_ok=True)
            
            return FAISS.from_texts(
                texts=[""],
                embedding=self.embeddings,
                metadatas=[{}]
            )
            
        except Exception as e:
            logger.error(f"Error initializing FAISS: {e}")
            raise
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        try:
            if self.store_type == "chromadb":
                self.vector_store.add_documents(documents)
            elif self.store_type == "faiss":
                # For FAISS, we need to merge with existing store
                if hasattr(self.vector_store, 'docstore') and self.vector_store.docstore:
                    # Merge with existing documents
                    self.vector_store.merge_from(self.vector_store)
                
                # Add new documents
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]
                self.vector_store.add_texts(texts, metadatas)
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def save(self) -> None:
        """Save the vector store."""
        try:
            if self.store_type == "faiss":
                faiss_path = self.storage_path / "faiss"
                self.vector_store.save_local(str(faiss_path))
                logger.info("FAISS vector store saved")
            # ChromaDB saves automatically
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise


class IngestionPipeline:
    """Main ingestion pipeline orchestrator."""
    
    def __init__(self, storage_path: str = "./storage/vectorstore", store_type: str = "chromadb"):
        self.loader = DocumentLoader()
        self.metadata_extractor = MetadataExtractor()
        self.chunker = DocumentChunker()
        self.vector_store = VectorStore(storage_path, store_type)
    
    def process_directory(self, input_dir: str) -> None:
        """Process all documents in a directory."""
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        if not input_path.is_dir():
            raise ValueError(f"Input path is not a directory: {input_dir}")
        
        # Find all supported documents
        documents = []
        for ext in DocumentLoader.SUPPORTED_EXTENSIONS:
            documents.extend(input_path.glob(f"**/*{ext}"))
        
        if not documents:
            logger.warning(f"No supported documents found in {input_dir}")
            return
        
        logger.info(f"Found {len(documents)} documents to process")
        
        # Process each document
        all_chunks = []
        for doc_path in documents:
            logger.info(f"Processing: {doc_path}")
            
            # Load document
            doc = self.loader.load_document(doc_path)
            if not doc:
                continue
            
            # Extract metadata
            metadata = self.metadata_extractor.extract_metadata(doc, doc_path)
            doc.metadata.update(metadata)
            
            # Chunk document
            chunks = self.chunker.chunk_document(doc)
            
            # Add source metadata to chunks
            for chunk in chunks:
                chunk.metadata.update(metadata)
            
            all_chunks.extend(chunks)
        
        # Add to vector store
        if all_chunks:
            self.vector_store.add_documents(all_chunks)
            self.vector_store.save()
            logger.info(f"Successfully processed {len(all_chunks)} chunks from {len(documents)} documents")
        else:
            logger.warning("No chunks were created from the documents")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Document ingestion pipeline")
    parser.add_argument(
        "input_dir",
        help="Directory containing documents to ingest"
    )
    parser.add_argument(
        "--storage-path",
        default="./storage/vectorstore",
        help="Path for vector store storage (default: ./storage/vectorstore)"
    )
    parser.add_argument(
        "--store-type",
        choices=["chromadb", "faiss"],
        default="chromadb",
        help="Vector store type (default: chromadb)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=800,
        help="Maximum tokens per chunk (default: 800)"
    )
    parser.add_argument(
        "--overlap-tokens",
        type=int,
        default=120,
        help="Overlap tokens between chunks (default: 120)"
    )
    
    args = parser.parse_args()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        return 1
    
    try:
        # Initialize pipeline
        pipeline = IngestionPipeline(
            storage_path=args.storage_path,
            store_type=args.store_type
        )
        
        # Update chunker settings if provided
        if args.max_tokens != 800 or args.overlap_tokens != 120:
            pipeline.chunker = DocumentChunker(
                max_tokens=args.max_tokens,
                overlap_tokens=args.overlap_tokens
            )
        
        # Process documents
        pipeline.process_directory(args.input_dir)
        
        logger.info("Ingestion pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
