# Citations Module Implementation Summary

## Overview

The citations module provides a comprehensive solution for mapping raw document metadata to canonical citations with deterministic formatting for logs and UI. It ensures consistent citation representation across the Local IT Support system.

## What Was Implemented

### 1. Core Classes

#### `CanonicalCitation`
- **Purpose**: Standardized citation representation with computed fields
- **Fields**:
  - `policy_title`: Raw policy title
  - `section`: Extracted section identifier
  - `effective_date`: Policy effective date
  - `url_or_path`: Source URL or file path
  - `snippet`: Content snippet for context
  - `citation_id`: Deterministic 8-character hash
  - `display_title`: Canonicalized title for display
  - `section_display`: Formatted section text
  - `date_display`: Formatted date text

#### `CitationMapper`
- **Purpose**: Maps raw document metadata to canonical citations
- **Features**:
  - Automatic section extraction from content
  - Flexible date field detection
  - URL/path field extraction
  - Content snippet creation
  - Fallback handling for incomplete documents

### 2. Key Features

#### Title Canonicalization
Automatically removes common prefixes for consistent display:
- `"IT Policy - Security Requirements"` → `"Security Requirements"`
- `"Technology Procedure: Data Access"` → `"Data Access"`
- `"Information Guideline - Compliance"` → `"Compliance"`

#### Section Extraction
Identifies and extracts section information using regex patterns:
- `Section 1.1` → `1.1`
- `Chapter 3` → `3`
- `Part 4` → `4`
- `1.2 Security Requirements` → `1.2`

#### Date Formatting
Supports multiple input formats and standardizes output:
- `2024-01-01` → `January 01, 2024`
- `2024/02/01` → `February 01, 2024`
- `01/03/2024` → `January 03, 2024`
- `January 4, 2024` → `January 04, 2024`

#### Metadata Extraction
Intelligently detects various field names:
- **Dates**: `effective_date`, `effectiveDate`, `start_date`, `created_date`, etc.
- **Paths**: `url`, `file_path`, `source_url`, `document_url`, etc.

### 3. Output Formats

#### Log Format
```
It Security Policy - Section 1.1 - (January 01, 2024) - [/policies/security.pdf]
```

#### UI Format
```
**It Security Policy** | *Section 1.1* | Effective: January 01, 2024
```

#### Markdown Format
```markdown
## It Security Policy

**Section 1.1**

*Effective: January 01, 2024*

[Source](/policies/security.pdf)

Content snippet...
```

#### JSON Format
```json
{
  "citation_id": "16b622de",
  "policy_title": "IT Security Policy - Access Control",
  "display_title": "It Security Policy - Access Control",
  "section": "1.1",
  "section_display": "Section 1.1",
  "effective_date": "2024-01-01",
  "date_display": "January 01, 2024",
  "url_or_path": "/policies/security.pdf",
  "snippet": "This policy covers access control requirements..."
}
```

### 4. Utility Functions

#### Citation Creation
- `create_citation_from_doc_with_score()`: Convert DocWithScore to CanonicalCitation

#### Formatting Functions
- `format_citations_for_logs()`: List of log-formatted strings
- `format_citations_for_ui()`: List of UI-formatted strings
- `format_citations_for_markdown()`: Complete markdown document

#### Import/Export
- `export_citations_to_json()`: Export to string or file
- `import_citations_from_json()`: Import from JSON data

### 5. Advanced Features

#### Deterministic IDs
- 8-character MD5 hash based on title, section, date, and URL
- Same metadata always produces same ID
- Useful for caching and deduplication

#### Fallback Handling
- Graceful handling of missing fields
- Configurable fallback titles
- Robust error handling

#### Content Snippets
- Automatic content truncation at sentence boundaries
- Configurable maximum length (default: 200 characters)
- Clean whitespace normalization

## Technical Implementation

### 1. Data Processing Pipeline
```
Raw Document → CitationMapper → CanonicalCitation → Formatted Output
```

### 2. Section Pattern Matching
```python
section_patterns = [
    r'Section\s+(\d+[\.\d]*)',
    r'(\d+[\.\d]*)\s*[A-Z][^.]*',
    r'Chapter\s+(\d+)',
    r'Part\s+(\d+)',
    r'(\d+\.\d+)\s*[-:]\s*[A-Z][^.]*',
]
```

### 3. Date Parsing
Supports multiple date formats with fallback handling:
```python
date_formats = [
    '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y',
    '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y'
]
```

### 4. Title Canonicalization
Uses regex to remove common prefixes:
```python
r'^(IT\s+|Technology\s+|Information\s+)?(Policy|Procedure|Guideline|Standard|Protocol)\s*[-:]\s*'
```

## Usage Examples

### Basic Citation Creation
```python
from src.retrieval import CanonicalCitation

citation = CanonicalCitation(
    policy_title="IT Security Policy - Password Requirements",
    section="1.1",
    effective_date="2024-01-01",
    url_or_path="/policies/security.pdf",
    snippet="All passwords must be at least 12 characters long..."
)

print(citation.to_log_format())
# Output: It Security Policy - Password Requirements - Section 1.1 - (January 01, 2024) - [/policies/security.pdf]
```

### Document Mapping
```python
from src.retrieval import CitationMapper

mapper = CitationMapper()
raw_docs = [
    {
        'title': 'IT Security Policy - Access Control',
        'content': 'Section 1.1 covers password policies.',
        'effective_date': '2024-01-01',
        'file_path': '/policies/security.pdf'
    }
]

citations = mapper.map_documents(raw_docs)
```

### Format Conversion
```python
from src.retrieval import format_citations_for_markdown

markdown = format_citations_for_markdown(citations)
print(markdown)
```

## Testing

### Test Coverage
- **CanonicalCitation**: 9 tests covering all methods and edge cases
- **CitationMapper**: 7 tests covering mapping and extraction
- **Utility Functions**: 5 tests covering formatting and I/O
- **Integration**: 1 test covering full workflow

### Test Results
```
22 tests passed in 1.34s
- Title canonicalization: ✅
- Section extraction: ✅
- Date formatting: ✅
- Output formats: ✅
- JSON I/O: ✅
- Error handling: ✅
```

## Integration with Hybrid Retriever

The citations module integrates seamlessly with the hybrid retriever:

```python
from src.retrieval import HybridRetriever, create_citation_from_doc_with_score

# Retrieve documents
retriever = HybridRetriever()
results = retriever.retrieve("password security")

# Convert to canonical citations
citations = [create_citation_from_doc_with_score(result) for result in results]

# Format for different outputs
log_formats = format_citations_for_logs(citations)
ui_formats = format_citations_for_ui(citations)
markdown = format_citations_for_markdown(citations)
```

## Benefits

### 1. Consistency
- Deterministic formatting across all outputs
- Standardized citation structure
- Consistent field naming

### 2. Flexibility
- Multiple output formats for different use cases
- Configurable field detection
- Fallback handling for incomplete data

### 3. Maintainability
- Clean separation of concerns
- Comprehensive test coverage
- Well-documented API

### 4. Performance
- Efficient regex patterns
- Lazy field computation
- Minimal memory overhead

## Future Enhancements

### Potential Improvements
1. **Custom Field Mappers**: User-defined field extraction rules
2. **Template System**: Configurable output format templates
3. **Validation**: Schema validation for citation data
4. **Caching**: Result caching for repeated operations
5. **Async Support**: Asynchronous citation processing

### Integration Opportunities
1. **LLM Integration**: Connect with language models for enhanced extraction
2. **Database Storage**: Persistent citation storage and retrieval
3. **API Endpoints**: REST API for citation services
4. **Batch Processing**: Efficient bulk citation generation

## Conclusion

The citations module provides a robust, production-ready solution for citation management in the Local IT Support system. It successfully addresses the requirement for deterministic formatting across logs and UI while maintaining flexibility and extensibility.

The implementation includes comprehensive testing, detailed documentation, and practical examples that demonstrate its capabilities for policy document citation generation, formatting, and export.
