"""Example usage of the HIL queue for human-in-the-loop questions."""

import logging
from datetime import datetime, timedelta
from .hil_queue import (
    HILQueue,
    create_hil_question,
    answer_hil_question,
    get_pending_hil_questions,
    get_hil_updates_for_ticket,
    check_hil_answer_status,
    get_hil_queue_summary
)
from ..store.rationale_policy import create_structured_rationale

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_create_hil_question():
    """Example of creating a HIL question."""
    
    print("=== Creating HIL Question Example ===")
    
    # Create AI rationale for the question
    ai_rationale = create_structured_rationale(
        rules=[
            "Hardware replacement policy",
            "Budget approval requirements",
            "User impact assessment"
        ],
        evidence=[
            "Laptop is 5 years old and out of warranty",
            "Multiple hardware failures reported",
            "User productivity significantly impacted"
        ],
        decision="Recommend laptop replacement",
        confidence=0.75,
        missing_info=[
            "Budget approval from department manager",
            "User's preference for replacement vs. repair",
            "Timeline for replacement"
        ]
    )
    
    # Create HIL question
    question_id = create_hil_question(
        ticket_id="IT-001",
        question_text="Should we replace the user's laptop or attempt repair?",
        context="User's laptop has multiple hardware issues and is out of warranty. Replacement cost is $800, repair estimate is $300 with no guarantee of success.",
        ai_rationale=ai_rationale,
        priority="high",
        assigned_to="manager_001",
        expires_in_hours=24
    )
    
    print(f"✓ Created HIL question: {question_id}")
    print(f"  - Ticket: IT-001")
    print(f"  - Priority: High")
    print(f"  - Assigned to: manager_001")
    print(f"  - Expires in: 24 hours")


def example_answer_hil_question():
    """Example of answering a HIL question."""
    
    print("\n=== Answering HIL Question Example ===")
    
    # Answer the HIL question
    success = answer_hil_question(
        ticket_id="IT-001",
        answer="Approve laptop replacement",
        approver="manager_001",
        justification="Based on the age of the laptop, multiple hardware failures, and impact on user productivity, replacement is the most cost-effective solution. Budget has been approved by department head."
    )
    
    if success:
        print("✓ HIL question answered successfully")
        print(f"  - Answer: Approve laptop replacement")
        print(f"  - Approver: manager_001")
        print(f"  - Justification: Budget approved, replacement most cost-effective")
    else:
        print("✗ Failed to answer HIL question")


def example_polling_for_updates():
    """Example of polling for HIL updates."""
    
    print("\n=== Polling for Updates Example ===")
    
    # Check for pending questions
    pending_questions = get_pending_hil_questions(
        assigned_to="manager_001",
        priority="high",
        limit=10
    )
    
    print(f"✓ Found {len(pending_questions)} pending HIL questions")
    for question in pending_questions:
        print(f"  - {question['id']}: {question['question_text'][:50]}...")
    
    # Check for updates on a specific ticket
    ticket_updates = get_hil_updates_for_ticket("IT-001")
    
    print(f"\n✓ Found {len(ticket_updates)} HIL updates for ticket IT-001")
    for update in ticket_updates:
        print(f"  - Status: {update['status']}")
        if update.get('answer'):
            print(f"    Answer: {update['answer']}")
    
    # Check if a specific question has been answered
    answer_status = check_hil_answer_status("IT-001")
    
    if answer_status:
        print(f"\n✓ HIL question answered for ticket IT-001:")
        print(f"  - Answer: {answer_status['answer']}")
        print(f"  - Approver: {answer_status['approver']}")
        print(f"  - Answered at: {answer_status['answered_at']}")
    else:
        print(f"\n✗ No HIL answer found for ticket IT-001")


def example_queue_management():
    """Example of queue management operations."""
    
    print("\n=== Queue Management Example ===")
    
    # Get queue summary
    queue_stats = get_hil_queue_summary()
    
    print("✓ HIL Queue Statistics:")
    print(f"  - Total questions: {queue_stats['total_questions']}")
    print(f"  - Pending: {queue_stats['pending']}")
    print(f"  - Answered: {queue_stats['answered']}")
    print(f"  - Approved: {queue_stats['approved']}")
    print(f"  - Rejected: {queue_stats['rejected']}")
    print(f"  - Expired: {queue_stats['expired']}")
    
    print("\n  Priority breakdown:")
    for priority, count in queue_stats['by_priority'].items():
        print(f"    - {priority.capitalize()}: {count}")


def example_workflow_lifecycle():
    """Example of complete HIL workflow lifecycle."""
    
    print("\n=== HIL Workflow Lifecycle Example ===")
    
    # Step 1: Create HIL question
    print("Step 1: Creating HIL question...")
    
    ai_rationale = create_structured_rationale(
        rules=["Access control policy", "Security requirements"],
        evidence=["User needs admin access for development work", "Manager approval provided"],
        decision="Grant admin access with restrictions",
        confidence=0.8,
        missing_info=["Specific admin privileges needed", "Duration of access"]
    )
    
    question_id = create_hil_question(
        ticket_id="IT-002",
        question_text="Should we grant admin access to user for development work?",
        context="User is a senior developer who needs admin access to install development tools and configure local environment.",
        ai_rationale=ai_rationale,
        priority="medium",
        assigned_to="security_manager",
        expires_in_hours=48
    )
    
    print(f"  ✓ Created question: {question_id}")
    
    # Step 2: Human reviews and answers
    print("\nStep 2: Human review and answer...")
    
    success = answer_hil_question(
        ticket_id="IT-002",
        answer="Approve with restrictions",
        approver="security_manager",
        justification="Approved for development work only. Access will be limited to development tools installation and local environment configuration. Regular access reviews will be conducted."
    )
    
    print(f"  ✓ Question answered: {'Success' if success else 'Failed'}")
    
    # Step 3: Check status
    print("\nStep 3: Checking answer status...")
    
    answer_status = check_hil_answer_status("IT-002")
    if answer_status:
        print(f"  ✓ Answer recorded:")
        print(f"    - Status: {answer_status['status']}")
        print(f"    - Answer: {answer_status['answer']}")
        print(f"    - Approver: {answer_status['approver']}")
    else:
        print("  ✗ No answer found")
    
    # Step 4: Get final updates
    print("\nStep 4: Getting final updates...")
    
    final_updates = get_hil_updates_for_ticket("IT-002")
    print(f"  ✓ Final status: {len(final_updates)} updates")
    for update in final_updates:
        print(f"    - {update['status']}: {update.get('question_text', 'N/A')[:40]}...")


def example_bulk_operations():
    """Example of bulk HIL operations."""
    
    print("\n=== Bulk Operations Example ===")
    
    # Create multiple HIL questions
    questions_data = [
        {
            "ticket_id": "IT-003",
            "question_text": "Should we upgrade the office printer fleet?",
            "context": "Current printers are 3 years old. Upgrade cost is $5,000, maintenance cost is $1,200/year.",
            "priority": "medium",
            "assigned_to": "facilities_manager"
        },
        {
            "ticket_id": "IT-004", 
            "question_text": "Do we need additional network security measures?",
            "context": "Recent security audit identified potential vulnerabilities. Additional measures cost $2,500.",
            "priority": "high",
            "assigned_to": "security_manager"
        },
        {
            "ticket_id": "IT-005",
            "question_text": "Should we implement remote work VPN solution?",
            "context": "20% of staff now work remotely. VPN solution cost is $3,000/year.",
            "priority": "medium",
            "assigned_to": "it_manager"
        }
    ]
    
    print("Creating multiple HIL questions...")
    
    for q_data in questions_data:
        ai_rationale = create_structured_rationale(
            rules=["Budget policy", "Business impact assessment"],
            evidence=["Cost analysis provided", "User requirements documented"],
            decision="Requires human decision",
            confidence=0.6,
            missing_info=["ROI calculation", "User adoption estimates"]
        )
        
        question_id = create_hil_question(
            ticket_id=q_data["ticket_id"],
            question_text=q_data["question_text"],
            context=q_data["context"],
            ai_rationale=ai_rationale,
            priority=q_data["priority"],
            assigned_to=q_data["assigned_to"],
            expires_in_hours=72
        )
        
        print(f"  ✓ Created: {question_id} for {q_data['ticket_id']}")
    
    # Get all pending questions
    print("\nRetrieving all pending questions...")
    
    all_pending = get_pending_hil_questions(limit=100)
    print(f"✓ Total pending questions: {len(all_pending)}")
    
    # Group by priority
    by_priority = {}
    for question in all_pending:
        priority = question['priority']
        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append(question)
    
    for priority, questions in by_priority.items():
        print(f"  - {priority.capitalize()}: {len(questions)} questions")


def example_error_handling():
    """Example of error handling in HIL operations."""
    
    print("\n=== Error Handling Example ===")
    
    # Try to answer non-existent question
    print("Testing error handling with non-existent ticket...")
    
    success = answer_hil_question(
        ticket_id="NONEXISTENT-001",
        answer="Test answer",
        approver="test_user",
        justification="Test justification"
    )
    
    if not success:
        print("  ✓ Properly handled non-existent ticket")
    else:
        print("  ✗ Unexpectedly succeeded with non-existent ticket")
    
    # Try to get updates for non-existent ticket
    print("\nTesting updates for non-existent ticket...")
    
    updates = get_hil_updates_for_ticket("NONEXISTENT-001")
    if len(updates) == 0:
        print("  ✓ Properly handled non-existent ticket updates")
    else:
        print("  ✗ Unexpectedly got updates for non-existent ticket")
    
    # Test with invalid priority
    print("\nTesting with invalid priority...")
    
    try:
        from .hil_queue import HILPriority
        invalid_priority = HILPriority("invalid")
        print("  ✗ Unexpectedly created invalid priority")
    except ValueError:
        print("  ✓ Properly handled invalid priority")


def main():
    """Run all examples."""
    print("HIL Queue Examples")
    print("=" * 50)
    
    try:
        example_create_hil_question()
        example_answer_hil_question()
        example_polling_for_updates()
        example_queue_management()
        example_workflow_lifecycle()
        example_bulk_operations()
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Example failed with error: {e}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    main()
