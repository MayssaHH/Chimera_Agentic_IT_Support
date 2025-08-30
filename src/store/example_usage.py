"""Example usage of the database module."""

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


def example_workflow():
    """Example workflow demonstrating database operations."""
    
    # Initialize database (creates tables on first run)
    print("Initializing database...")
    init_db()
    
    # Create a sample ticket
    print("\nCreating a sample ticket...")
    ticket = Ticket(
        title="Printer not working",
        description="The office printer is showing error code E-04 and won't print",
        category="hardware",
        priority="high",
        created_by="emp_001",
        tags="printer,hardware,urgent"
    )
    
    saved_ticket = save_ticket(ticket)
    print(f"Created ticket: {saved_ticket.id} - {saved_ticket.title}")
    
    # Create a decision for the ticket
    print("\nCreating a decision...")
    decision = Decision(
        ticket_id=saved_ticket.id,
        decision_text="Replace printer fuser unit",
        reasoning="Error E-04 indicates fuser unit failure based on printer manual",
        confidence_score=0.85,
        created_by="ai_system"
    )
    
    saved_decision = save_decision(decision)
    print(f"Created decision: {saved_decision.id}")
    
    # Create a plan for the ticket
    print("\nCreating a plan...")
    plan = Plan(
        ticket_id=saved_ticket.id,
        plan_title="Replace Printer Fuser Unit",
        plan_description="Replace the fuser unit to resolve printer error E-04",
        steps='["1. Power off printer", "2. Remove old fuser unit", "3. Install new fuser unit", "4. Test print"]',
        priority="high",
        estimated_duration=30,
        created_by="ai_system"
    )
    
    saved_plan = save_plan(plan)
    print(f"Created plan: {saved_plan.id}")
    
    # Update ticket status
    print("\nUpdating ticket status...")
    updated_ticket = update_ticket_status(
        saved_ticket.id,
        "in_progress",
        "Fuser unit replacement in progress"
    )
    print(f"Ticket status updated to: {updated_ticket.status}")
    
    # List tickets
    print("\nListing all tickets...")
    all_tickets = list_tickets()
    for t in all_tickets:
        print(f"- {t.id}: {t.title} ({t.status})")
    
    # Search tickets
    print("\nSearching for printer-related tickets...")
    printer_tickets = search_tickets("printer")
    for t in printer_tickets:
        print(f"- {t.id}: {t.title}")
    
    # Get ticket statistics
    print("\nGetting ticket statistics...")
    stats = get_ticket_statistics()
    print(f"Total tickets: {stats['total_tickets']}")
    print(f"Status breakdown: {stats['status_breakdown']}")
    print(f"Category breakdown: {stats['category_breakdown']}")
    
    # Get specific ticket with related data
    print(f"\nGetting detailed info for ticket {saved_ticket.id}...")
    ticket_detail = get_ticket(saved_ticket.id)
    if ticket_detail:
        print(f"Ticket: {ticket_detail.title}")
        print(f"Status: {ticket_detail.status}")
        print(f"Created: {ticket_detail.created_at}")
        print(f"Priority: {ticket_detail.priority}")


if __name__ == "__main__":
    example_workflow()
