# Hybrid Retriever

A hybrid retrieval system that combines BM25 text search, vector similarity search, and Reciprocal Rank Fusion (RRF) to provide robust document retrieval capabilities.

## Features

- **BM25 Retriever**: Traditional text-based search using BM25 scoring algorithm
- **Vector Retriever**: Semantic search using ChromaDB and vector embeddings
- **Hybrid Fusion**: Combines both approaches using Reciprocal Rank Fusion (RRF)
- **Citation Generation**: Automatically generates citations with canonicalized titles and section anchors
- **Filtering Support**: Apply metadata filters during retrieval
- **Document Management**: Add, update, and remove documents from the index

## Architecture

The hybrid retriever consists of three main components:

1. **BM25Retriever**: Implements BM25 scoring for keyword-based search
2. **VectorRetriever**: Uses ChromaDB for vector similarity search
3. **HybridRetriever**: Orchestrates both retrievers and applies RRF fusion

## Installation

The retriever requires the following dependencies (already included in the project):

```bash
pip install scikit-learn chromadb numpy
```

## Usage

### Basic Setup

```python
from src.retrieval import HybridRetriever

# Initialize the retriever
retriever = HybridRetriever(
    persist_directory="./chroma_db",
    bm25_weight=0.4,      # Weight for BM25 results
    vector_weight=0.6,     # Weight for vector results
    rrf_k=60.0            # RRF parameter
)
```

### Adding Documents

```python
documents = [
    {
        'id': 'policy1',
        'title': 'IT Security Policy',
        'content': 'This policy outlines security requirements...',
        'category': 'security',
        'source_type': 'policy',
        'tags': ['security', 'passwords']
    },
    # ... more documents
]

retriever.add_documents(documents)
```

### Retrieving Documents

```python
# Basic retrieval
results = retriever.retrieve("password security", k=8)

# With filters
filters = {'category': 'security', 'source_type': 'policy'}
results = retriever.retrieve("password security", k=8, filters=filters)

# Access results
for result in results:
    print(f"Title: {result.source_title}")
    print(f"Score: {result.score}")
    print(f"Content: {result.content[:200]}...")
    print(f"Section: {result.source_section}")
    print("---")
```

### Generating Citations

```python
citations = retriever.retrieve_citations("password security")

for citation in citations:
    print(f"Source: {citation.source_title}")
    print(f"Section: {citation.section}")
    print(f"Relevance: {citation.relevance_score}")
    print(f"Content: {citation.content}")
    print("---")
```

## Configuration

### BM25 Parameters

- `k1`: Controls term frequency scaling (default: 1.2)
- `b`: Controls document length normalization (default: 0.75)

### Vector Search Parameters

- `persist_directory`: Directory for ChromaDB persistence
- Collection name: "policy_documents" (configurable)

### Hybrid Fusion Parameters

- `bm25_weight`: Weight for BM25 results in fusion (default: 0.4)
- `vector_weight`: Weight for vector results in fusion (default: 0.6)
- `rrf_k`: RRF parameter for rank fusion (default: 60.0)

## Document Format

Documents should have the following structure:

```python
{
    'id': 'unique_identifier',
    'title': 'Document Title',
    'content': 'Full document content...',
    'category': 'document_category',
    'source_type': 'policy|guideline|procedure|standard',
    'tags': ['tag1', 'tag2'],
    # ... additional metadata
}
```

## Section Extraction

The retriever automatically extracts section information from document content using regex patterns:

- `Section 1.1` → `1.1`
- `Chapter 3` → `3`
- `Part 4` → `4`

## Title Canonicalization

Policy titles are automatically canonicalized for consistent citations:

- `"IT Policy - Security Requirements"` → `"Security Requirements"`
- `"Technology Procedure: Data Access"` → `"Data Access"`

## Performance Considerations

- **BM25**: Fast for keyword search, good for exact matches
- **Vector Search**: Better for semantic similarity, requires more computational resources
- **Fusion**: Combines strengths of both approaches
- **Indexing**: Both indices are rebuilt when documents are added/updated

## Testing

Run the test suite to verify functionality:

```bash
pytest src/retrieval/test_retriever.py -v
```

## Example Workflow

```python
# 1. Initialize retriever
retriever = HybridRetriever()

# 2. Load policy documents
policies = load_policy_documents()
retriever.add_documents(policies)

# 3. Search for relevant policies
query = "employee access to sensitive data"
results = retriever.retrieve(query, k=5, filters={'category': 'security'})

# 4. Generate citations for response
citations = retriever.retrieve_citations(query)

# 5. Use results in decision-making
for result in results:
    if result.score > 0.7:
        print(f"High relevance: {result.source_title}")
        print(f"Section: {result.source_section}")
```

## Troubleshooting

### Common Issues

1. **ChromaDB Connection**: Ensure the persist directory is writable
2. **Memory Usage**: Large document collections may require significant memory
3. **Performance**: Vector search performance depends on document size and collection size

### Best Practices

1. **Document Preprocessing**: Clean and normalize document content before indexing
2. **Metadata**: Use consistent metadata structure for better filtering
3. **Batch Operations**: Add documents in batches for better performance
4. **Regular Updates**: Rebuild indices periodically for optimal performance

## API Reference

### HybridRetriever

- `retrieve(query, k=8, filters=None)` → `List[DocWithScore]`
- `retrieve_citations(query)` → `List[Citation]`
- `add_documents(documents)` → `None`
- `update_document(doc_id, updated_doc)` → `None`
- `remove_document(doc_id)` → `None`
- `get_document_by_id(doc_id)` → `Optional[Dict]`

### DocWithScore

- `id`: Document identifier
- `content`: Document content
- `metadata`: Full document metadata
- `score`: Relevance score
- `source_type`: Type of source document
- `source_title`: Document title
- `source_section`: Extracted section identifier
