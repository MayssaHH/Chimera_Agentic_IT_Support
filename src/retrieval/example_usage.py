#!/usr/bin/env python3
"""Example usage of the hybrid retriever."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

from .retriever import HybridRetriever


def load_sample_policies():
    """Load sample policy documents."""
    return [
        {
            'id': 'security_policy_001',
            'title': 'IT Security Policy - Access Control',
            'content': '''
            This policy establishes security requirements for all employees and contractors.
            
            Section 1.1 - Password Requirements
            All passwords must be at least 12 characters long and contain uppercase, lowercase, 
            numbers, and special characters. Passwords must be changed every 90 days.
            
            Section 1.2 - Access Control
            Employees may only access systems and data necessary for their job functions.
            Access requests must be approved by department managers and reviewed quarterly.
            
            Section 1.3 - Data Classification
            Company data is classified into three levels: Public, Internal, and Confidential.
            Each level has specific handling and access requirements.
            ''',
            'category': 'security',
            'source_type': 'policy',
            'tags': ['security', 'access', 'passwords', 'data_classification'],
            'version': '2.1',
            'effective_date': '2024-01-01'
        },
        {
            'id': 'data_access_001',
            'title': 'Data Access Guidelines - Employee Permissions',
            'content': '''
            These guidelines outline the process for requesting and managing data access.
            
            Section 2.1 - Request Process
            Data access requests must be submitted through the IT Service Portal.
            Requests should include business justification and manager approval.
            
            Section 2.2 - Access Levels
            Basic access: Read-only access to internal documents
            Standard access: Read-write access to department data
            Elevated access: Administrative access to systems (requires additional approval)
            
            Section 2.3 - Review Process
            All access permissions are reviewed quarterly by department managers.
            Inactive accounts are automatically disabled after 30 days of inactivity.
            ''',
            'category': 'access',
            'source_type': 'guideline',
            'tags': ['data', 'access', 'permissions', 'review'],
            'version': '1.3',
            'effective_date': '2024-02-01'
        },
        {
            'id': 'software_001',
            'title': 'Software Installation Procedure - Standard Applications',
            'content': '''
            This procedure covers the installation of standard software applications.
            
            Chapter 3 - Approval Process
            Software installation requests must be approved by IT Security team.
            Only approved software from the company software catalog may be installed.
            
            Part 4 - Installation Steps
            1. Submit software request through IT portal
            2. Wait for security approval (typically 2-3 business days)
            3. Download from approved software repository
            4. Install following provided instructions
            5. Verify installation and report any issues
            
            Part 5 - Compliance
            All installed software must comply with company security standards.
            Regular audits are conducted to ensure compliance.
            ''',
            'category': 'software',
            'source_type': 'procedure',
            'tags': ['software', 'installation', 'approval', 'compliance'],
            'version': '1.0',
            'effective_date': '2024-03-01'
        }
    ]


def main():
    """Main example function."""
    print("🚀 Hybrid Retriever Example")
    print("=" * 50)
    
    # Load sample policies
    policies = load_sample_policies()
    print(f"Loaded {len(policies)} policy documents")
    
    # Initialize retriever (with mocked ChromaDB for demo)
    with patch('chromadb.PersistentClient'):
        retriever = HybridRetriever()
        retriever.add_documents(policies)
        
        # Mock vector search results
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['security_policy_001', 'data_access_001', 'software_001']],
            'distances': [[0.1, 0.3, 0.5]]
        }
        retriever.vector_retriever.collection = mock_collection
        
        print("\n📋 Example Queries:")
        print("-" * 30)
        
        # Example 1: Security-related query
        print("\n1. Query: 'password security requirements'")
        results = retriever.retrieve("password security requirements", k=3)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.source_title} (Score: {result.score:.3f})")
            print(f"      Section: {result.source_section}")
            print(f"      Content: {result.content[:100]}...")
        
        # Example 2: Access-related query
        print("\n2. Query: 'employee data access permissions'")
        results = retriever.retrieve("employee data access permissions", k=3)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.source_title} (Score: {result.score:.3f})")
            print(f"      Section: {result.source_section}")
            print(f"      Content: {result.content[:100]}...")
        
        # Example 3: Software-related query
        print("\n3. Query: 'software installation approval process'")
        results = retriever.retrieve("software installation approval process", k=3)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.source_title} (Score: {result.score:.3f})")
            print(f"      Section: {result.source_section}")
            print(f"      Content: {result.content[:100]}...")
        
        # Example 4: Generate citations
        print("\n4. Citations for 'security access control'")
        citations = retriever.retrieve_citations("security access control")
        for i, citation in enumerate(citations, 1):
            print(f"   {i}. {citation.source_title}")
            print(f"      Section: {citation.section}")
            print(f"      Relevance: {citation.relevance_score:.3f}")
            print(f"      Content: {citation.content[:80]}...")
        
        # Example 5: Filtered search
        print("\n5. Filtered search: Security policies only")
        filters = {'category': 'security', 'source_type': 'policy'}
        results = retriever.retrieve("access control", k=3, filters=filters)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.source_title} (Score: {result.score:.3f})")
            print(f"      Category: {result.metadata['category']}")
            print(f"      Type: {result.metadata['source_type']}")
        
        print("\n✅ Example completed successfully!")
        print("\n💡 Key Features Demonstrated:")
        print("   • Hybrid search combining BM25 and vector search")
        print("   • Automatic section extraction and title canonicalization")
        print("   • Citation generation with relevance scores")
        print("   • Metadata filtering capabilities")
        print("   • RRF fusion for optimal result ranking")


if __name__ == "__main__":
    main()
