"""Tests for the database module."""

import pytest
from datetime import datetime
from .db import (
    Decision,
    Plan,
    Ticket,
    ToolCall,
    init_db,
    save_ticket,
    save_decision,
    save_plan,
    update_ticket_status,
    list_tickets,
    get_ticket,
    search_tickets,
    get_ticket_statistics,
)


@pytest.fixture(scope="function")
def setup_db():
    """Setup database for testing."""
    # Use in-memory SQLite for testing
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    from ..config import settings
    settings.database_url = "sqlite:///:memory:"
    
    init_db()
    yield
    # Cleanup handled by in-memory database


def test_create_ticket(setup_db):
    """Test creating and saving a ticket."""
    ticket = Ticket(
        title="Test Ticket",
        description="Test Description",
        category="software",
        priority="medium",
        created_by="test_emp"
    )
    
    saved_ticket = save_ticket(ticket)
    
    assert saved_ticket.id is not None
    assert saved_ticket.title == "Test Ticket"
    assert saved_ticket.status == "open"
    assert saved_ticket.created_at is not None


def test_create_decision(setup_db):
    """Test creating and saving a decision."""
    # First create a ticket
    ticket = Ticket(
        title="Test Ticket",
        description="Test Description",
        category="software",
        created_by="test_emp"
    )
    saved_ticket = save_ticket(ticket)
    
    # Create decision
    decision = Decision(
        ticket_id=saved_ticket.id,
        decision_text="Test Decision",
        reasoning="Test Reasoning",
        confidence_score=0.8,
        created_by="ai_system"
    )
    
    saved_decision = save_decision(decision)
    
    assert saved_decision.id is not None
    assert saved_decision.ticket_id == saved_ticket.id
    assert saved_decision.confidence_score == 0.8


def test_create_plan(setup_db):
    """Test creating and saving a plan."""
    # First create a ticket
    ticket = Ticket(
        title="Test Ticket",
        description="Test Description",
        category="software",
        created_by="test_emp"
    )
    saved_ticket = save_ticket(ticket)
    
    # Create plan
    plan = Plan(
        ticket_id=saved_ticket.id,
        plan_title="Test Plan",
        plan_description="Test Plan Description",
        steps='["Step 1", "Step 2"]',
        priority="high",
        estimated_duration=60,
        created_by="ai_system"
    )
    
    saved_plan = save_plan(plan)
    
    assert saved_plan.id is not None
    assert saved_plan.ticket_id == saved_ticket.id
    assert saved_plan.priority == "high"


def test_update_ticket_status(setup_db):
    """Test updating ticket status."""
    # Create a ticket
    ticket = Ticket(
        title="Test Ticket",
        description="Test Description",
        category="software",
        created_by="test_emp"
    )
    saved_ticket = save_ticket(ticket)
    
    # Update status
    updated_ticket = update_ticket_status(
        saved_ticket.id,
        "resolved",
        "Issue resolved"
    )
    
    assert updated_ticket.status == "resolved"
    assert updated_ticket.resolution_notes == "Issue resolved"
    assert updated_ticket.resolved_at is not None


def test_list_tickets(setup_db):
    """Test listing tickets."""
    # Create multiple tickets
    ticket1 = Ticket(
        title="Ticket 1",
        description="Description 1",
        category="hardware",
        created_by="emp_1"
    )
    ticket2 = Ticket(
        title="Ticket 2",
        description="Description 2",
        category="software",
        created_by="emp_2"
    )
    
    save_ticket(ticket1)
    save_ticket(ticket2)
    
    # List all tickets
    all_tickets = list_tickets()
    assert len(all_tickets) == 2
    
    # Filter by category
    hardware_tickets = list_tickets(category="hardware")
    assert len(hardware_tickets) == 1
    assert hardware_tickets[0].category == "hardware"


def test_search_tickets(setup_db):
    """Test searching tickets."""
    # Create tickets with searchable content
    ticket1 = Ticket(
        title="Printer Issue",
        description="Printer not working",
        category="hardware",
        created_by="emp_1"
    )
    ticket2 = Ticket(
        title="Network Problem",
        description="Cannot connect to network",
        category="network",
        created_by="emp_2"
    )
    
    save_ticket(ticket1)
    save_ticket(ticket2)
    
    # Search for printer-related tickets
    printer_tickets = search_tickets("printer")
    assert len(printer_tickets) == 1
    assert "Printer" in printer_tickets[0].title


def test_get_ticket_statistics(setup_db):
    """Test getting ticket statistics."""
    # Create tickets with different statuses and categories
    ticket1 = Ticket(
        title="Ticket 1",
        description="Description 1",
        category="hardware",
        status="open",
        created_by="emp_1"
    )
    ticket2 = Ticket(
        title="Ticket 2",
        description="Description 2",
        category="software",
        status="resolved",
        created_by="emp_2"
    )
    
    save_ticket(ticket1)
    save_ticket(ticket2)
    
    # Get statistics
    stats = get_ticket_statistics()
    
    assert stats["total_tickets"] == 2
    assert "open" in stats["status_breakdown"]
    assert "resolved" in stats["status_breakdown"]
    assert "hardware" in stats["category_breakdown"]
    assert "software" in stats["category_breakdown"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])
