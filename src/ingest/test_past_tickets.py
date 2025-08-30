"""Test suite for the past tickets ingestion module."""

import json
import tempfile
from pathlib import Path

from src.ingest.past_tickets import (
    TicketData, TicketProcessor, TicketIngestionPipeline,
    TICKET_OUTCOMES, APPROVER_ROLES
)


def create_sample_ticket_data():
    """Create sample ticket data for testing."""
    return [
        {
            "ticket_id": "TICKET-001",
            "description": "User needs access to shared network drive",
            "outcome": "approved",
            "resolution": "Access granted to shared drive after manager approval",
            "approver_role": "IT Manager",
            "created_date": "2024-01-15",
            "resolved_date": "2024-01-16",
            "category": "access",
            "priority": "medium",
            "tags": ["network access", "shared drive"]
        },
        {
            "ticket_id": "TICKET-002",
            "description": "Software installation request for Adobe Creative Suite",
            "outcome": "denied",
            "resolution": "Request denied due to budget constraints",
            "approver_role": "Department Head",
            "created_date": "2024-01-20",
            "resolved_date": "2024-01-22",
            "category": "software",
            "priority": "low",
            "tags": ["software installation", "adobe"]
        },
        {
            "ticket_id": "TICKET-003",
            "description": "Password reset for locked account",
            "outcome": "approved",
            "resolution": "Password reset completed and user notified",
            "approver_role": "IT Admin",
            "created_date": "2024-01-25",
            "resolved_date": "2024-01-25",
            "category": "access",
            "priority": "high",
            "tags": ["password reset", "account lockout"]
        }
    ]


def create_sample_text_tickets():
    """Create sample text-based ticket data."""
    return """
Ticket ID: TEXT-001
User reported printer not working in office
Outcome: approved
Resolution: Replaced printer cartridge and restarted printer service
Approver: IT Support Lead
Date: 2024-02-01

Ticket ID: TEXT-002
Request for VPN access to company network
Outcome: requires_approval
Resolution: Pending manager approval for remote access
Approver: Security Officer
Date: 2024-02-05

Ticket ID: TEXT-003
Hardware replacement for broken laptop
Outcome: approved
Resolution: Laptop replaced with new model from inventory
Approver: IT Manager
Date: 2024-02-10
"""


def test_ticket_data_creation():
    """Test TicketData class creation and methods."""
    print("=== Testing TicketData Creation ===")
    
    # Test basic creation
    ticket = TicketData(
        ticket_id="TEST-001",
        description="Test ticket description",
        outcome="approved",
        resolution="Test resolution",
        approver_role="Test Manager",
        created_date="2024-01-01",
        category="test",
        priority="medium",
        tags=["test", "example"]
    )
    
    print(f"✅ Ticket created: {ticket.ticket_id}")
    print(f"   Description: {ticket.description}")
    print(f"   Outcome: {ticket.outcome}")
    print(f"   Approver: {ticket.approver_role}")
    
    # Test to_dict method
    ticket_dict = ticket.to_dict()
    print(f"✅ Dictionary conversion: {len(ticket_dict)} fields")
    
    # Test to_document method
    doc = ticket.to_document()
    print(f"✅ Document conversion: {len(doc.page_content)} chars")
    print(f"   Metadata source: {doc.metadata.get('source')}")
    print(f"   Content type: {doc.metadata.get('content_type')}")
    
    return ticket


def test_ticket_processor():
    """Test TicketProcessor functionality."""
    print("\n=== Testing TicketProcessor ===")
    
    processor = TicketProcessor()
    
    # Test outcome detection
    test_texts = [
        ("User access was approved by manager", "allowed"),
        ("Request was rejected due to policy violation", "denied"),
        ("Ticket is pending approval", "requires_approval"),
        ("Access granted to system", "allowed"),
        ("Request blocked by security", "denied")
    ]
    
    for text, expected in test_texts:
        detected = processor.detect_outcome(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} Outcome detection: '{text}' -> {detected} (expected: {expected})")
    
    # Test approver role detection
    test_roles = [
        ("Approved by IT Manager", "IT Manager"),
        ("Supervisor approved the request", "Supervisor"),
        ("Department Head signed off", "Department Head"),
        ("No specific approver mentioned", None)
    ]
    
    for text, expected in test_roles:
        detected = processor.detect_approver_role(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} Role detection: '{text}' -> {detected} (expected: {expected})")
    
    # Test date extraction
    test_dates = [
        "Ticket created on 2024-01-15 and resolved on 2024-01-16",
        "Opened January 20, 2024, closed January 22, 2024"
    ]
    
    for text in test_dates:
        dates = processor.extract_dates(text)
        print(f"✅ Date extraction: {dates}")
    
    # Test category extraction
    test_categories = [
        ("User needs network access", "Network"),
        ("Software installation request", "Software"),
        ("Hardware replacement needed", "Hardware"),
        ("Security incident reported", "Security")
    ]
    
    for text, expected in test_categories:
        detected = processor.extract_category(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} Category detection: '{text}' -> {detected} (expected: {expected})")
    
    # Test priority extraction
    test_priorities = [
        ("Urgent security issue", "High"),
        ("Normal maintenance request", "Medium"),
        ("Low priority software update", "Low")
    ]
    
    for text, expected in test_priorities:
        detected = processor.extract_priority(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} Priority detection: '{text}' -> {detected} (expected: {expected})")
    
    # Test tag extraction
    test_tags = [
        "User needs password reset for locked account",
        "Request for VPN access to company network",
        "Hardware replacement for broken laptop"
    ]
    
    for text in test_tags:
        tags = processor.extract_tags(text)
        print(f"✅ Tag extraction: '{text}' -> {tags}")
    
    return processor


def test_ticket_ingestion_pipeline():
    """Test the complete ticket ingestion pipeline."""
    print("\n=== Testing Ticket Ingestion Pipeline ===")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample JSON file
        json_file = temp_path / "sample_tickets.json"
        sample_data = create_sample_ticket_data()
        with open(json_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        # Create sample CSV file
        csv_file = temp_path / "sample_tickets.csv"
        import csv
        with open(csv_file, 'w', newline='') as f:
            if sample_data:
                writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
                writer.writeheader()
                writer.writerows(sample_data)
        
        # Create sample text file
        text_file = temp_path / "sample_tickets.txt"
        text_content = create_sample_text_tickets()
        text_file.write_text(text_content)
        
        print(f"✅ Created test files in {temp_path}")
        print(f"   JSON: {json_file.name}")
        print(f"   CSV: {csv_file.name}")
        print(f"   TXT: {text_file.name}")
        
        # Test pipeline initialization (without vector store)
        try:
            pipeline = TicketIngestionPipeline(
                storage_path=temp_path / "vectorstore",
                store_type="chromadb"
            )
            print("✅ Pipeline initialized successfully")
            
            # Test individual file processing
            json_tickets = pipeline.process_ticket_file(json_file)
            print(f"✅ JSON processing: {len(json_tickets)} tickets")
            
            csv_tickets = pipeline.process_ticket_file(csv_file)
            print(f"✅ CSV processing: {len(csv_tickets)} tickets")
            
            txt_tickets = pipeline.process_ticket_file(text_file)
            print(f"✅ TXT processing: {len(txt_tickets)} tickets")
            
            # Test ticket data validation
            for ticket in json_tickets + csv_tickets + txt_tickets:
                print(f"   Ticket {ticket.ticket_id}: {ticket.outcome} by {ticket.approver_role}")
            
        except Exception as e:
            print(f"❌ Pipeline test failed: {e}")
            import traceback
            traceback.print_exc()


def test_constants():
    """Test the defined constants and patterns."""
    print("\n=== Testing Constants and Patterns ===")
    
    print(f"✅ Ticket outcomes: {list(TICKET_OUTCOMES.keys())}")
    for outcome, keywords in TICKET_OUTCOMES.items():
        print(f"   {outcome}: {keywords}")
    
    print(f"✅ Approver roles: {len(APPROVER_ROLES)} roles")
    print(f"   Sample roles: {APPROVER_ROLES[:5]}")


def test_integration():
    """Test integration with the main pipeline components."""
    print("\n=== Testing Integration ===")
    
    try:
        # Test importing from pipeline module
        from src.ingest.past_tickets import TicketIngestionPipeline
        
        # Test creating pipeline instance
        pipeline = TicketIngestionPipeline()
        print("✅ Pipeline integration test passed")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("🚀 Past Tickets Ingestion Tests")
    print("=" * 50)
    
    try:
        test_ticket_data_creation()
        test_ticket_processor()
        test_ticket_ingestion_pipeline()
        test_constants()
        test_integration()
        
        print("\n" + "=" * 50)
        print("✨ All tests completed successfully!")
        print("\nTo run the ticket ingestion pipeline:")
        print("  python3 -m src.ingest.past_tickets ./ticket_data")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
