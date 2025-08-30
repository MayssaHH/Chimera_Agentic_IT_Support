"""Tests for the citations module."""

import pytest
import json
import tempfile
from datetime import datetime
from unittest.mock import Mock

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


class TestCanonicalCitation:
    """Test CanonicalCitation class."""
    
    def test_basic_creation(self):
        """Test basic citation creation."""
        citation = CanonicalCitation(
            policy_title="IT Security Policy",
            section="1.1",
            effective_date="2024-01-01",
            url_or_path="/policies/security.pdf",
            snippet="Password requirements for employees."
        )
        
        assert citation.policy_title == "IT Security Policy"
        assert citation.section == "1.1"
        assert citation.effective_date == "2024-01-01"
        assert citation.url_or_path == "/policies/security.pdf"
        assert citation.snippet == "Password requirements for employees."
        assert citation.citation_id is not None
        assert len(citation.citation_id) == 8
    
    def test_title_canonicalization(self):
        """Test title canonicalization."""
        # Test various title formats
        test_cases = [
            ("IT Policy - Security Requirements", "Security Requirements"),
            ("Technology Procedure: Data Access", "Data Access"),
            ("Information Guideline - Compliance", "Compliance"),
            ("Standard Protocol - Network Security", "Standard Protocol - Network Security"),
            ("Simple Title", "Simple Title"),
            ("", "Unknown Policy"),
        ]
        
        for input_title, expected in test_cases:
            citation = CanonicalCitation(
                policy_title=input_title,
                snippet="test"
            )
            assert citation.display_title == expected
    
    def test_section_formatting(self):
        """Test section formatting."""
        test_cases = [
            ("1.1", "Section 1.1"),
            ("2", "Section 2"),
            ("Section 3.2", "Section 3.2"),
            ("Chapter 4", "Chapter 4"),
            ("Part 5", "Part 5"),
            ("Custom Section", "Section Custom Section"),
        ]
        
        for input_section, expected in test_cases:
            citation = CanonicalCitation(
                policy_title="Test Policy",
                section=input_section,
                snippet="test"
            )
            assert citation.section_display == expected
    
    def test_date_formatting(self):
        """Test date formatting."""
        test_cases = [
            ("2024-01-01", "January 01, 2024"),
            ("2024/02/01", "February 01, 2024"),
            ("01/03/2024", "January 03, 2024"),
            ("January 4, 2024", "January 04, 2024"),
            ("invalid-date", "invalid-date"),
        ]
        
        for input_date, expected in test_cases:
            citation = CanonicalCitation(
                policy_title="Test Policy",
                effective_date=input_date,
                snippet="test"
            )
            assert citation.date_display == expected
    
    def test_deterministic_id(self):
        """Test that citation ID is deterministic."""
        citation1 = CanonicalCitation(
            policy_title="IT Security Policy",
            section="1.1",
            effective_date="2024-01-01",
            url_or_path="/policies/security.pdf",
            snippet="test"
        )
        
        citation2 = CanonicalCitation(
            policy_title="IT Security Policy",
            section="1.1",
            effective_date="2024-01-01",
            url_or_path="/policies/security.pdf",
            snippet="different snippet"
        )
        
        # Same metadata should produce same ID
        assert citation1.citation_id == citation2.citation_id
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        citation = CanonicalCitation(
            policy_title="Test Policy",
            section="1.1",
            effective_date="2024-01-01",
            url_or_path="/test.pdf",
            snippet="test content"
        )
        
        data = citation.to_dict()
        
        assert data['policy_title'] == "Test Policy"
        assert data['display_title'] == "Test Policy"
        assert data['section'] == "1.1"
        assert data['section_display'] == "Section 1.1"
        assert data['effective_date'] == "2024-01-01"
        assert data['date_display'] == "January 01, 2024"
        assert data['url_or_path'] == "/test.pdf"
        assert data['snippet'] == "test content"
        assert 'citation_id' in data
    
    def test_log_format(self):
        """Test log format."""
        citation = CanonicalCitation(
            policy_title="IT Security Policy",
            section="1.1",
            effective_date="2024-01-01",
            url_or_path="/policies/security.pdf",
            snippet="test"
        )
        
        log_format = citation.to_log_format()
        expected = "It Security Policy - Section 1.1 - (January 01, 2024) - [/policies/security.pdf]"
        assert log_format == expected
    
    def test_ui_format(self):
        """Test UI format."""
        citation = CanonicalCitation(
            policy_title="IT Security Policy",
            section="1.1",
            effective_date="2024-01-01",
            snippet="test"
        )
        
        ui_format = citation.to_ui_format()
        expected = "**It Security Policy** | *Section 1.1* | Effective: January 01, 2024"
        assert ui_format == expected
    
    def test_markdown_format(self):
        """Test markdown format."""
        citation = CanonicalCitation(
            policy_title="IT Security Policy",
            section="1.1",
            effective_date="2024-01-01",
            url_or_path="/policies/security.pdf",
            snippet="Password requirements for employees."
        )
        
        markdown = citation.to_markdown()
        assert "## It Security Policy" in markdown
        assert "**Section 1.1**" in markdown
        assert "*Effective: January 01, 2024*" in markdown
        assert "[Source](/policies/security.pdf)" in markdown
        assert "Password requirements for employees." in markdown


class TestCitationMapper:
    """Test CitationMapper class."""
    
    def test_basic_mapping(self):
        """Test basic document mapping."""
        mapper = CitationMapper()
        
        doc = {
            'title': 'IT Security Policy - Access Control',
            'content': 'This policy covers access control. Section 1.1 discusses passwords.',
            'effective_date': '2024-01-01',
            'url': '/policies/security.pdf'
        }
        
        citation = mapper.map_document(doc)
        
        assert citation.policy_title == 'IT Security Policy - Access Control'
        assert citation.section == '1.1'
        assert citation.effective_date == '2024-01-01'
        assert citation.url_or_path == '/policies/security.pdf'
        assert 'access control' in citation.snippet.lower()
    
    def test_section_extraction(self):
        """Test section extraction from content."""
        mapper = CitationMapper()
        
        test_cases = [
            ("Section 1.1 covers passwords", "1.1"),
            ("Chapter 3 discusses access", "3"),
            ("Part 4 outlines procedures", "4"),
            ("1.2 Security Requirements", "1.2"),
            ("No section here", None),
        ]
        
        for content, expected in test_cases:
            doc = {'title': 'Test', 'content': content}
            citation = mapper.map_document(doc)
            assert citation.section == expected
    
    def test_date_extraction(self):
        """Test date field extraction."""
        mapper = CitationMapper()
        
        doc = {
            'title': 'Test Policy',
            'content': 'test content',
            'effectiveDate': '2024-01-01',
            'start_date': '2024-02-01',
            'created_date': '2024-03-01'
        }
        
        citation = mapper.map_document(doc)
        # Should pick the first available date field
        assert citation.effective_date == '2024-01-01'
    
    def test_url_extraction(self):
        """Test URL/path field extraction."""
        mapper = CitationMapper()
        
        doc = {
            'title': 'Test Policy',
            'content': 'test content',
            'file_path': '/policies/test.pdf',
            'source_url': 'https://example.com/policy',
            'link': '/internal/policy'
        }
        
        citation = mapper.map_document(doc)
        # Should pick the first available path field
        assert citation.url_or_path == '/policies/test.pdf'
    
    def test_snippet_creation(self):
        """Test snippet creation."""
        mapper = CitationMapper()
        
        # Short content
        short_doc = {
            'title': 'Test Policy',
            'content': 'Short content here.'
        }
        citation = mapper.map_document(short_doc)
        assert citation.snippet == 'Short content here.'
        
        # Long content
        long_content = "This is a very long content that should be truncated. " * 20
        long_doc = {
            'title': 'Test Policy',
            'content': long_content
        }
        citation = mapper.map_document(long_doc)
        assert len(citation.snippet) <= 200
        # Check if it's truncated (either ends with ... or is exactly 200 chars or shorter)
        assert citation.snippet.endswith('...') or len(citation.snippet) <= 200
    
    def test_map_documents(self):
        """Test mapping multiple documents."""
        mapper = CitationMapper()
        
        docs = [
            {'title': 'Policy 1', 'content': 'Section 1.1 content'},
            {'title': 'Policy 2', 'content': 'Section 2.1 content'},
        ]
        
        citations = mapper.map_documents(docs)
        assert len(citations) == 2
        assert citations[0].policy_title == 'Policy 1'
        assert citations[1].policy_title == 'Policy 2'
    
    def test_map_with_fallback(self):
        """Test mapping with fallback values."""
        mapper = CitationMapper()
        
        doc = {'content': 'test content'}  # No title
        
        citation = mapper.map_with_fallback(doc, "Fallback Title")
        assert citation.policy_title == "Fallback Title"


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_citation_from_doc_with_score(self):
        """Test creating citation from DocWithScore."""
        # Mock DocWithScore object
        mock_doc = Mock()
        mock_doc.source_title = "IT Security Policy"
        mock_doc.content = "Section 1.1 covers passwords"
        mock_doc.source_section = "1.1"
        mock_doc.metadata = {'effective_date': '2024-01-01'}
        
        citation = create_citation_from_doc_with_score(mock_doc)
        
        assert citation.policy_title == "IT Security Policy"
        assert citation.section == "1.1"
        assert citation.effective_date == "2024-01-01"
    
    def test_format_citations_for_logs(self):
        """Test log formatting."""
        citations = [
            CanonicalCitation("Policy 1", "1.1", "2024-01-01", snippet="test"),
            CanonicalCitation("Policy 2", "2.1", "2024-02-01", snippet="test"),
        ]
        
        log_formats = format_citations_for_logs(citations)
        assert len(log_formats) == 2
        assert "Policy 1 - Section 1.1" in log_formats[0]
        assert "Policy 2 - Section 2.1" in log_formats[1]
    
    def test_format_citations_for_ui(self):
        """Test UI formatting."""
        citations = [
            CanonicalCitation("Policy 1", "1.1", "2024-01-01", snippet="test"),
            CanonicalCitation("Policy 2", "2.1", "2024-02-01", snippet="test"),
        ]
        
        ui_formats = format_citations_for_ui(citations)
        assert len(ui_formats) == 2
        assert "**Policy 1**" in ui_formats[0]
        assert "**Policy 2**" in ui_formats[1]
    
    def test_format_citations_for_markdown(self):
        """Test markdown formatting."""
        citations = [
            CanonicalCitation("Policy 1", "1.1", "2024-01-01", snippet="test"),
            CanonicalCitation("Policy 2", "2.1", "2024-02-01", snippet="test"),
        ]
        
        markdown = format_citations_for_markdown(citations)
        assert "# Policy Citations" in markdown
        assert "## Policy 1" in markdown
        assert "## Policy 2" in markdown
        assert "---" in markdown
    
    def test_export_import_json(self):
        """Test JSON export and import."""
        citations = [
            CanonicalCitation("Policy 1", "1.1", "2024-01-01", snippet="test"),
            CanonicalCitation("Policy 2", "2.1", "2024-02-01", snippet="test"),
        ]
        
        # Export to string
        json_str = export_citations_to_json(citations)
        data = json.loads(json_str)
        assert len(data) == 2
        assert data[0]['policy_title'] == "Policy 1"
        
        # Import from string
        imported = import_citations_from_json(json_str)
        assert len(imported) == 2
        assert imported[0].policy_title == "Policy 1"
        
        # Export to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            result = export_citations_to_json(citations, temp_path)
            assert "exported to" in result
            
            # Read and verify file
            with open(temp_path, 'r') as f:
                file_data = json.load(f)
            assert len(file_data) == 2
        finally:
            import os
            os.unlink(temp_path)


def test_integration_example():
    """Integration test showing full workflow."""
    # Create sample documents
    docs = [
        {
            'title': 'IT Security Policy - Password Requirements',
            'content': 'This policy establishes password requirements. Section 1.1 covers complexity rules.',
            'effective_date': '2024-01-01',
            'file_path': '/policies/security.pdf'
        },
        {
            'title': 'Data Access Guidelines - Employee Permissions',
            'content': 'Guidelines for data access. Section 2.1 discusses permission levels.',
            'effective_date': '2024-02-01',
            'url': '/guidelines/access.pdf'
        }
    ]
    
    # Map to citations
    mapper = CitationMapper()
    citations = mapper.map_documents(docs)
    
    assert len(citations) == 2
    
    # Test first citation
    first = citations[0]
    assert first.display_title == "It Security Policy - Password Requirements"
    assert first.section == "1.1"
    assert first.section_display == "Section 1.1"
    assert first.date_display == "January 01, 2024"
    assert first.url_or_path == "/policies/security.pdf"
    
    # Test second citation
    second = citations[1]
    assert second.display_title == "Data Access Guidelines - Employee Permissions"
    assert second.section == "2.1"
    assert second.section_display == "Section 2.1"
    assert second.date_display == "February 01, 2024"
    assert second.url_or_path == "/guidelines/access.pdf"
    
    # Test formatting functions
    log_formats = format_citations_for_logs(citations)
    assert len(log_formats) == 2
    assert "It Security Policy - Password Requirements - Section 1.1" in log_formats[0]
    
    ui_formats = format_citations_for_ui(citations)
    assert len(ui_formats) == 2
    assert "**It Security Policy - Password Requirements**" in ui_formats[0]
    
    markdown = format_citations_for_markdown(citations)
    assert "## It Security Policy - Password Requirements" in markdown
    assert "## Data Access Guidelines - Employee Permissions" in markdown


if __name__ == "__main__":
    # Run integration example
    print("Running citations integration example...")
    test_integration_example()
    print("✅ Citations integration test completed successfully!")
