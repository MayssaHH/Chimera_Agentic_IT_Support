"""Citation mapping and formatting utilities."""

import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json

from ..domain.schemas import Citation


@dataclass
class CanonicalCitation:
    """Canonical citation with standardized formatting."""
    
    policy_title: str
    section: Optional[str] = None
    effective_date: Optional[str] = None
    url_or_path: Optional[str] = None
    snippet: str = ""
    
    # Computed fields for consistent formatting
    citation_id: str = field(init=False)
    display_title: str = field(init=False)
    section_display: str = field(init=False)
    date_display: str = field(init=False)
    
    def __post_init__(self):
        """Compute derived fields after initialization."""
        # Generate deterministic citation ID
        content = f"{self.policy_title}:{self.section}:{self.effective_date}:{self.url_or_path}"
        self.citation_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Format display title (remove common prefixes)
        self.display_title = self._canonicalize_title(self.policy_title)
        
        # Format section display
        self.section_display = self._format_section(self.section) if self.section else ""
        
        # Format date display
        self.date_display = self._format_date(self.effective_date) if self.effective_date else ""
    
    def _canonicalize_title(self, title: str) -> str:
        """Canonicalize policy title for consistent display."""
        if not title:
            return "Unknown Policy"
        
        # Remove common prefixes and normalize
        title = title.strip()
        title = re.sub(
            r'^(IT\s+|Technology\s+|Information\s+)?(Policy|Procedure|Guideline|Standard|Protocol)\s*[-:]\s*', 
            '', 
            title, 
            flags=re.IGNORECASE
        )
        
        # Capitalize properly
        title = title.title()
        
        # Ensure it's not empty after cleaning
        if not title:
            return "Policy Document"
        
        return title
    
    def _format_section(self, section: str) -> str:
        """Format section for display."""
        if not section:
            return ""
        
        # Clean and format section
        section = section.strip()
        
        # Handle different section formats
        if re.match(r'^\d+\.\d+', section):
            return f"Section {section}"
        elif re.match(r'^\d+$', section):
            return f"Section {section}"
        elif section.lower().startswith('section'):
            return section.title()
        elif section.lower().startswith('chapter'):
            return section.title()
        elif section.lower().startswith('part'):
            return section.title()
        else:
            return f"Section {section}"
    
    def _format_date(self, date_str: str) -> str:
        """Format date for display."""
        if not date_str:
            return ""
        
        try:
            # Try to parse various date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%B %d, %Y',
                '%b %d, %Y'
            ]
            
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%B %d, %Y')
                except ValueError:
                    continue
            
            # If no format matches, return as-is
            return date_str
            
        except Exception:
            return date_str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'citation_id': self.citation_id,
            'policy_title': self.policy_title,
            'display_title': self.display_title,
            'section': self.section,
            'section_display': self.section_display,
            'effective_date': self.effective_date,
            'date_display': self.date_display,
            'url_or_path': self.url_or_path,
            'snippet': self.snippet
        }
    
    def to_log_format(self) -> str:
        """Format for logging purposes."""
        parts = [self.display_title]
        
        if self.section_display:
            parts.append(self.section_display)
        
        if self.date_display:
            parts.append(f"({self.date_display})")
        
        if self.url_or_path:
            parts.append(f"[{self.url_or_path}]")
        
        return " - ".join(parts)
    
    def to_ui_format(self) -> str:
        """Format for UI display."""
        parts = [f"**{self.display_title}**"]
        
        if self.section_display:
            parts.append(f"*{self.section_display}*")
        
        if self.date_display:
            parts.append(f"Effective: {self.date_display}")
        
        return " | ".join(parts)
    
    def to_markdown(self) -> str:
        """Format as markdown."""
        parts = [f"## {self.display_title}"]
        
        if self.section_display:
            parts.append(f"**{self.section_display}**")
        
        if self.date_display:
            parts.append(f"*Effective: {self.date_display}*")
        
        if self.url_or_path:
            parts.append(f"[Source]({self.url_or_path})")
        
        if self.snippet:
            parts.append(f"\n{self.snippet}")
        
        return "\n\n".join(parts)
    
    def __str__(self) -> str:
        """String representation for general use."""
        return self.to_log_format()
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"CanonicalCitation(id={self.citation_id}, title='{self.display_title}', section='{self.section_display}')"


class CitationMapper:
    """Maps raw document metadata to canonical citations."""
    
    def __init__(self):
        self.title_patterns = [
            r'^(IT\s+|Technology\s+|Information\s+)?(Policy|Procedure|Guideline|Standard|Protocol)\s*[-:]\s*(.+)$',
            r'^(.+?)\s*[-:]\s*(Policy|Procedure|Guideline|Standard|Protocol)',
            r'^(.+?)\s+(Policy|Procedure|Guideline|Standard|Protocol)',
        ]
        
        self.section_patterns = [
            r'Section\s+(\d+[\.\d]*)',
            r'(\d+[\.\d]*)\s*[A-Z][^.]*',
            r'Chapter\s+(\d+)',
            r'Part\s+(\d+)',
            r'(\d+\.\d+)\s*[-:]\s*[A-Z][^.]*',
        ]
    
    def map_document(self, doc: Dict[str, Any]) -> CanonicalCitation:
        """Map a raw document to a canonical citation."""
        # Extract basic fields
        policy_title = doc.get('title', '')
        content = doc.get('content', '')
        
        # Extract section from content
        section = self._extract_section(content)
        
        # Extract effective date
        effective_date = self._extract_effective_date(doc)
        
        # Extract URL or path
        url_or_path = self._extract_url_or_path(doc)
        
        # Create snippet from content
        snippet = self._create_snippet(content)
        
        return CanonicalCitation(
            policy_title=policy_title,
            section=section,
            effective_date=effective_date,
            url_or_path=url_or_path,
            snippet=snippet
        )
    
    def _extract_section(self, content: str) -> Optional[str]:
        """Extract section information from content."""
        if not content:
            return None
        
        # Check first 1000 characters for section patterns
        search_content = content[:1000]
        
        for pattern in self.section_patterns:
            match = re.search(pattern, search_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_effective_date(self, doc: Dict[str, Any]) -> Optional[str]:
        """Extract effective date from document metadata."""
        # Try different date field names
        date_fields = [
            'effective_date',
            'effectiveDate',
            'date_effective',
            'dateEffective',
            'start_date',
            'startDate',
            'created_date',
            'createdDate',
            'date_created',
            'dateCreated'
        ]
        
        for field in date_fields:
            if field in doc and doc[field]:
                return str(doc[field])
        
        return None
    
    def _extract_url_or_path(self, doc: Dict[str, Any]) -> Optional[str]:
        """Extract URL or file path from document metadata."""
        # Try different URL/path field names
        path_fields = [
            'url',
            'file_path',
            'filePath',
            'path',
            'source_url',
            'sourceUrl',
            'document_url',
            'documentUrl',
            'link',
            'href'
        ]
        
        for field in path_fields:
            if field in doc and doc[field]:
                return str(doc[field])
        
        return None
    
    def _create_snippet(self, content: str, max_length: int = 200) -> str:
        """Create a snippet from document content."""
        if not content:
            return ""
        
        # Clean content
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Truncate if too long
        if len(content) <= max_length:
            return content
        
        # Try to break at sentence boundary
        truncated = content[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.7:  # If period is in last 30%
            return truncated[:last_period + 1]
        else:
            return truncated + "..."
    
    def map_documents(self, documents: List[Dict[str, Any]]) -> List[CanonicalCitation]:
        """Map multiple documents to canonical citations."""
        return [self.map_document(doc) for doc in documents]
    
    def map_with_fallback(self, doc: Dict[str, Any], fallback_title: str = "Unknown Document") -> CanonicalCitation:
        """Map document with fallback values for missing fields."""
        # Ensure we have at least a title
        if not doc.get('title'):
            doc = doc.copy()
            doc['title'] = fallback_title
        
        return self.map_document(doc)


def create_citation_from_doc_with_score(doc_with_score: Any) -> CanonicalCitation:
    """Create a canonical citation from a DocWithScore object."""
    # Extract metadata from DocWithScore
    metadata = getattr(doc_with_score, 'metadata', {})
    if not metadata:
        metadata = {}
    
    # Use DocWithScore fields if available
    title = getattr(doc_with_score, 'source_title', None) or metadata.get('title', 'Unknown Document')
    content = getattr(doc_with_score, 'content', None) or metadata.get('content', '')
    section = getattr(doc_with_score, 'source_section', None)
    
    # Create metadata dict for mapping
    doc_dict = {
        'title': title,
        'content': content,
        'section': section,
        **metadata
    }
    
    mapper = CitationMapper()
    return mapper.map_document(doc_dict)


def format_citations_for_logs(citations: List[CanonicalCitation]) -> List[str]:
    """Format citations for logging purposes."""
    return [citation.to_log_format() for citation in citations]


def format_citations_for_ui(citations: List[CanonicalCitation]) -> List[str]:
    """Format citations for UI display."""
    return [citation.to_ui_format() for citation in citations]


def format_citations_for_markdown(citations: List[CanonicalCitation]) -> str:
    """Format citations as markdown document."""
    if not citations:
        return "# No Citations Found"
    
    header = "# Policy Citations\n\n"
    citation_sections = [citation.to_markdown() for citation in citations]
    
    return header + "\n\n---\n\n".join(citation_sections)


def export_citations_to_json(citations: List[CanonicalCitation], filepath: Optional[str] = None) -> str:
    """Export citations to JSON format."""
    citation_data = [citation.to_dict() for citation in citations]
    
    if filepath:
        with open(filepath, 'w') as f:
            json.dump(citation_data, f, indent=2)
        return f"Citations exported to {filepath}"
    else:
        return json.dumps(citation_data, indent=2)


def import_citations_from_json(json_data: str) -> List[CanonicalCitation]:
    """Import citations from JSON format."""
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
    
    citations = []
    for item in data:
        citation = CanonicalCitation(
            policy_title=item.get('policy_title', ''),
            section=item.get('section'),
            effective_date=item.get('effective_date'),
            url_or_path=item.get('url_or_path'),
            snippet=item.get('snippet', '')
        )
        citations.append(citation)
    
    return citations
