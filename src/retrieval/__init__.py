"""Retrieval module for Local IT Support system."""

from .retriever import HybridRetriever
from .citations import (
    CanonicalCitation,
    CitationMapper,
    create_citation_from_doc_with_score,
    format_citations_for_logs,
    format_citations_for_ui,
    format_citations_for_markdown,
    export_citations_to_json,
    import_citations_from_json
)

__all__ = [
    "HybridRetriever",
    "CanonicalCitation",
    "CitationMapper",
    "create_citation_from_doc_with_score",
    "format_citations_for_logs",
    "format_citations_for_ui",
    "format_citations_for_markdown",
    "export_citations_to_json",
    "import_citations_from_json"
]
