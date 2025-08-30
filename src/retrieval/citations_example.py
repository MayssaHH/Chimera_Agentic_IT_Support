#!/usr/bin/env python3
"""Example usage of the citations module."""

from .citations import (
    CanonicalCitation,
    CitationMapper,
    format_citations_for_logs,
    format_citations_for_ui,
    format_citations_for_markdown,
    export_citations_to_json
)


def main():
    """Main example function."""
    print("📚 Citations Module Example")
    print("=" * 50)
    
    # Example 1: Direct citation creation
    print("\n1. Direct Citation Creation:")
    print("-" * 30)
    
    citation = CanonicalCitation(
        policy_title="IT Security Policy - Password Requirements",
        section="1.1",
        effective_date="2024-01-01",
        url_or_path="/policies/security.pdf",
        snippet="All passwords must be at least 12 characters long and contain uppercase, lowercase, numbers, and special characters."
    )
    
    print(f"Citation ID: {citation.citation_id}")
    print(f"Display Title: {citation.display_title}")
    print(f"Section: {citation.section_display}")
    print(f"Date: {citation.date_display}")
    print(f"URL: {citation.url_or_path}")
    print(f"Snippet: {citation.snippet}")
    
    # Example 2: Citation mapping from raw documents
    print("\n2. Citation Mapping from Raw Documents:")
    print("-" * 40)
    
    raw_docs = [
        {
            'title': 'IT Security Policy - Access Control',
            'content': 'This policy covers access control requirements. Section 1.1 discusses password policies. Section 1.2 covers access levels.',
            'effective_date': '2024-01-01',
            'file_path': '/policies/security.pdf',
            'category': 'security'
        },
        {
            'title': 'Data Access Guidelines - Employee Permissions',
            'content': 'Guidelines for managing employee data access. Section 2.1 covers request process. Section 2.2 discusses approval workflow.',
            'effectiveDate': '2024-02-01',
            'url': '/guidelines/access.pdf',
            'department': 'IT'
        },
        {
            'title': 'Software Installation Procedure - Standard Applications',
            'content': 'Procedure for installing approved software. Chapter 3 covers the approval process. Part 4 outlines installation steps.',
            'start_date': '2024-03-01',
            'source_url': '/procedures/software.pdf',
            'priority': 'medium'
        }
    ]
    
    mapper = CitationMapper()
    citations = mapper.map_documents(raw_docs)
    
    print(f"Mapped {len(citations)} documents to citations:")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. {citation.to_log_format()}")
    
    # Example 3: Different formatting options
    print("\n3. Different Formatting Options:")
    print("-" * 35)
    
    print("\nLog Format:")
    log_formats = format_citations_for_logs(citations)
    for fmt in log_formats:
        print(f"  • {fmt}")
    
    print("\nUI Format:")
    ui_formats = format_citations_for_ui(citations)
    for fmt in ui_formats:
        print(f"  • {fmt}")
    
    print("\nMarkdown Format:")
    markdown = format_citations_for_markdown(citations)
    print(markdown)
    
    # Example 4: JSON export
    print("\n4. JSON Export:")
    print("-" * 15)
    
    json_output = export_citations_to_json(citations)
    print("JSON representation (first 200 chars):")
    print(json_output[:200] + "...")
    
    # Example 5: Citation with fallback
    print("\n5. Citation with Fallback:")
    print("-" * 25)
    
    incomplete_doc = {
        'content': 'This document has no title but contains important information.',
        'effective_date': '2024-04-01'
    }
    
    fallback_citation = mapper.map_with_fallback(incomplete_doc, "Unknown Policy Document")
    print(f"Fallback citation: {fallback_citation.to_log_format()}")
    
    # Example 6: Section extraction patterns
    print("\n6. Section Extraction Patterns:")
    print("-" * 35)
    
    section_test_docs = [
        {'title': 'Test Doc 1', 'content': 'Section 1.1 covers basic requirements'},
        {'title': 'Test Doc 2', 'content': 'Chapter 3 discusses advanced topics'},
        {'title': 'Test Doc 3', 'content': 'Part 4 outlines implementation steps'},
        {'title': 'Test Doc 4', 'content': '1.2 Security considerations'},
        {'title': 'Test Doc 5', 'content': 'No section information here'}
    ]
    
    section_citations = mapper.map_documents(section_test_docs)
    print("Section extraction results:")
    for citation in section_citations:
        section_info = f"Section: {citation.section_display}" if citation.section else "No section"
        print(f"  • {citation.display_title} - {section_info}")
    
    # Example 7: Date formatting
    print("\n7. Date Formatting:")
    print("-" * 20)
    
    date_test_docs = [
        {'title': 'Policy A', 'content': 'test', 'effective_date': '2024-01-01'},
        {'title': 'Policy B', 'content': 'test', 'effective_date': '2024/02/01'},
        {'title': 'Policy C', 'content': 'test', 'effective_date': '01/03/2024'},
        {'title': 'Policy D', 'content': 'test', 'effective_date': 'January 4, 2024'},
        {'title': 'Policy E', 'content': 'test', 'effective_date': 'invalid-date'}
    ]
    
    date_citations = mapper.map_documents(date_test_docs)
    print("Date formatting results:")
    for citation in date_citations:
        print(f"  • {citation.display_title}: {citation.date_display}")
    
    print("\n✅ Citations example completed successfully!")
    print("\n💡 Key Features Demonstrated:")
    print("   • Automatic title canonicalization")
    print("   • Section extraction from content")
    print("   • Date parsing and formatting")
    print("   • URL/path extraction")
    print("   • Multiple output formats (log, UI, markdown)")
    print("   • JSON export/import")
    print("   • Fallback handling for incomplete documents")


if __name__ == "__main__":
    main()
