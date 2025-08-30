"""Example usage of Jira client for ticket management."""

import logging
from .jira import JiraClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_ticket_lifecycle():
    """Example of complete ticket lifecycle management."""
    
    print("=== Jira Ticket Lifecycle Example ===")
    
    # Initialize client in dry-run mode for local development
    with JiraClient(dry_run=True) as jira:
        
        # Validate credentials (always returns True in dry-run mode)
        if jira.validate_credentials():
            print("✓ Jira credentials validated")
        else:
            print("✗ Jira credentials invalid")
            return
        
        # Get project info
        project_info = jira.get_project_info("IT")
        print(f"✓ Project: {project_info['name']} ({project_info['key']})")
        
        # Create a new ticket
        print("\n--- Creating Ticket ---")
        ticket = jira.create_ticket(
            summary="Printer not working in Marketing department",
            description="Users report that the HP LaserJet printer in Marketing is showing 'Paper Jam' error. Multiple users affected.",
            employee_id="emp_marketing_001",
            priority="High",
            issue_type="Task"
        )
        
        print(f"✓ Created ticket: {ticket['key']} - {ticket['summary']}")
        print(f"  Status: {ticket['status']}")
        
        # Get ticket details
        print("\n--- Getting Ticket Details ---")
        ticket_details = jira.get_ticket(ticket['id'])
        if ticket_details:
            print(f"✓ Ticket details retrieved:")
            print(f"  Key: {ticket_details['key']}")
            print(f"  Summary: {ticket_details['summary']}")
            print(f"  Status: {ticket_details['status']}")
            print(f"  Priority: {ticket_details['priority']}")
            print(f"  Assignee: {ticket_details['assignee']}")
        
        # Transition ticket through workflow states
        print("\n--- Workflow Transitions ---")
        
        # Start working on the ticket
        if jira.transition_ticket(ticket['id'], "in_progress"):
            print("✓ Ticket transitioned to 'in_progress'")
        else:
            print("✗ Failed to transition to 'in_progress'")
        
        # Mark as resolved
        if jira.transition_ticket(ticket['id'], "resolved"):
            print("✓ Ticket transitioned to 'resolved'")
        else:
            print("✗ Failed to transition to 'resolved'")
        
        # Close the ticket
        if jira.transition_ticket(ticket['id'], "closed"):
            print("✓ Ticket transitioned to 'closed'")
        else:
            print("✗ Failed to transition to 'closed'")
        
        # Get updated ticket details
        print("\n--- Final Ticket Status ---")
        final_ticket = jira.get_ticket(ticket['id'])
        if final_ticket:
            print(f"✓ Final status: {final_ticket['status']}")


def example_employee_ticket_search():
    """Example of searching for employee tickets."""
    
    print("\n=== Employee Ticket Search Example ===")
    
    with JiraClient(dry_run=True) as jira:
        employee_id = "emp_marketing_001"
        
        # Search for all tickets for the employee
        print(f"Searching for tickets for employee: {employee_id}")
        all_tickets = jira.search_employee_tickets(employee_id)
        
        print(f"✓ Found {len(all_tickets)} tickets:")
        for ticket in all_tickets:
            print(f"  - {ticket['key']}: {ticket['summary']} ({ticket['status']})")
        
        # Search for specific status
        print(f"\nSearching for 'in_progress' tickets for employee: {employee_id}")
        in_progress_tickets = jira.search_employee_tickets(
            employee_id, 
            status="in_progress"
        )
        
        print(f"✓ Found {len(in_progress_tickets)} in-progress tickets:")
        for ticket in in_progress_tickets:
            print(f"  - {ticket['key']}: {ticket['summary']}")


def example_workflow_states():
    """Example of workflow state management."""
    
    print("\n=== Workflow States Example ===")
    
    with JiraClient(dry_run=True) as jira:
        # Get available workflow states
        workflow_states = jira.get_workflow_states()
        
        print("✓ Available workflow states:")
        for state, transition_id in workflow_states.items():
            print(f"  - {state} (transition ID: {transition_id})")
        
        # Show the workflow progression
        print("\n✓ Workflow progression:")
        progression = ["new", "in_progress", "resolved", "closed"]
        for i, state in enumerate(progression):
            arrow = " → " if i < len(progression) - 1 else ""
            print(f"  {state}{arrow}", end="")
        print()


def example_error_handling():
    """Example of error handling and retry logic."""
    
    print("\n=== Error Handling Example ===")
    
    with JiraClient(dry_run=True) as jira:
        # Try to get a non-existent ticket
        print("Testing error handling with non-existent ticket...")
        non_existent_ticket = jira.get_ticket("INVALID-999")
        
        if non_existent_ticket is None:
            print("✓ Properly handled non-existent ticket")
        else:
            print("✗ Unexpectedly got data for non-existent ticket")
        
        # Try invalid status transition
        print("\nTesting invalid status transition...")
        invalid_transition = jira.transition_ticket("TEST-001", "invalid_status")
        
        if not invalid_transition:
            print("✓ Properly handled invalid status transition")
        else:
            print("✗ Unexpectedly succeeded with invalid status")


def main():
    """Run all examples."""
    print("Jira Client Examples")
    print("=" * 50)
    
    try:
        example_ticket_lifecycle()
        example_employee_ticket_search()
        example_workflow_states()
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Example failed with error: {e}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    main()
