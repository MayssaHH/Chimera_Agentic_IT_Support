# Document Ingestion Pipeline

A robust document ingestion pipeline for processing PDF, DOCX, and TXT files with intelligent chunking, metadata extraction, and vector storage.

## Features

- **Multi-format Support**: PDF, DOCX, and TXT document processing
- **Intelligent Chunking**: Configurable token-based chunking with overlap
- **Metadata Extraction**: Automatic extraction of policy_id, version, effective_date, and section
- **Vector Storage**: Support for ChromaDB (default) and FAISS
- **CLI Interface**: Easy-to-use command-line tool
- **Configurable**: Environment variables and command-line options

## Installation

The pipeline uses the dependencies already defined in the project's `pyproject.toml`. Ensure you have the required packages:

```bash
# Install project dependencies
poetry install

# Or install specific ingestion requirements
pip install -r src/ingest/requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE_PATH=./storage/vectorstore
VECTOR_STORE_TYPE=chromadb
MAX_CHUNK_TOKENS=800
OVERLAP_TOKENS=120
LOG_LEVEL=INFO
```

### Default Settings

- **Chunking**: 800 tokens max, 120 tokens overlap
- **Vector Store**: ChromaDB (persistent storage)
- **Storage Path**: `./storage/vectorstore`
- **Embedding Model**: `text-embedding-ada-002`

## Usage

### Command Line Interface

Process documents from a directory:

```bash
# Basic usage
python -m src.ingest.pipeline ./company_docs

# With custom settings
python -m src.ingest.pipeline ./company_docs \
    --storage-path ./custom_storage \
    --store-type faiss \
    --max-tokens 1000 \
    --overlap-tokens 150
```

### Command Line Options

- `input_dir`: Directory containing documents to process
- `--storage-path`: Path for vector store storage (default: `./storage/vectorstore`)
- `--store-type`: Vector store type: `chromadb` or `faiss` (default: `chromadb`)
- `--max-tokens`: Maximum tokens per chunk (default: 800)
- `--overlap-tokens`: Overlap tokens between chunks (default: 120)

### Programmatic Usage

```python
from src.ingest.pipeline import IngestionPipeline

# Initialize pipeline
pipeline = IngestionPipeline(
    storage_path="./storage/vectorstore",
    store_type="chromadb"
)

# Process documents
pipeline.process_directory("./company_docs")
```

## Document Processing

### Supported Formats

- **PDF**: Uses PyPDFLoader for text extraction
- **DOCX**: Uses UnstructuredWordDocumentLoader for rich text processing
- **TXT**: Uses TextLoader for plain text files

### Metadata Extraction

The pipeline automatically extracts the following metadata:

- **policy_id**: Extracted from filename or content using regex patterns
- **version**: Version numbers (e.g., v1.0, 2.1)
- **effective_date**: Dates in various formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
- **section**: Document sections (overview, security, procedures, etc.)
- **source**: Full file path
- **filename**: Original filename
- **file_type**: File extension
- **file_size**: File size in bytes

### Chunking Strategy

- **Token-based**: Uses tiktoken for accurate token counting
- **Overlap**: Configurable overlap to maintain context between chunks
- **Smart Splitting**: Recursive character splitting with natural separators
- **Metadata Preservation**: Each chunk retains source document metadata

## Vector Storage

### ChromaDB (Default)

- **Persistent Storage**: Automatically saves to disk
- **Collection Management**: Creates `company_documents` collection
- **Cosine Similarity**: Optimized for semantic search
- **Metadata Indexing**: Full metadata support

### FAISS

- **High Performance**: Fast similarity search
- **Memory Efficient**: Optimized for large-scale operations
- **Local Storage**: Saves to disk for persistence
- **Merge Support**: Can combine with existing stores

## Directory Structure

```
src/ingest/
├── __init__.py          # Package initialization
├── pipeline.py          # Main pipeline implementation
├── config.py            # Configuration management
├── requirements.txt     # Dependencies
├── test_pipeline.py     # Test suite
└── README.md           # This file
```

## Testing

Run the test suite to verify functionality:

```bash
# Run all tests
python -m src.ingest.test_pipeline

# Test specific components
python -c "
from src.ingest.pipeline import DocumentLoader, MetadataExtractor
print('Components imported successfully')
"
```

## Example Workflow

1. **Prepare Documents**: Place PDF, DOCX, or TXT files in a directory
2. **Set Environment**: Configure OpenAI API key and optional settings
3. **Run Pipeline**: Execute the ingestion command
4. **Verify Results**: Check the vector store storage directory
5. **Query Documents**: Use the vector store for semantic search

## Troubleshooting

### Common Issues

- **Missing API Key**: Ensure `OPENAI_API_KEY` is set in environment
- **Permission Errors**: Check write permissions for storage directory
- **Document Loading Failures**: Verify file formats and file integrity
- **Memory Issues**: Reduce chunk size for large documents

### Logging

The pipeline provides detailed logging. Set `LOG_LEVEL=DEBUG` for verbose output:

```bash
export LOG_LEVEL=DEBUG
python -m src.ingest.pipeline ./company_docs
```

## Performance Considerations

- **Chunk Size**: Smaller chunks (400-600 tokens) for precise retrieval
- **Overlap**: 15-20% overlap maintains context between chunks
- **Batch Processing**: Process documents in batches for large collections
- **Storage**: ChromaDB for development, FAISS for production scale

## Contributing

When extending the pipeline:

1. Add new document loaders to `DocumentLoader` class
2. Extend metadata patterns in `MetadataExtractor`
3. Implement new vector store backends in `VectorStore` class
4. Update tests and documentation

## License

This pipeline is part of the Local IT Support system and follows the same licensing terms.
