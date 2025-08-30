"""Example usage of the emailer module for sending transactional emails."""

import logging
from .emailer import Emailer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_email():
    """Example of sending a basic email."""
    
    print("=== Basic Email Example ===")
    
    # Initialize emailer in dry-run mode for local development
    emailer = Emailer(dry_run=True)
    
    # Test connection (always returns True in dry-run mode)
    if emailer.test_connection():
        print("✓ SMTP connection test successful")
    else:
        print("✗ SMTP connection test failed")
        return
    
    # Send a simple email
    success = emailer.send_email(
        to="user@example.com",
        subject="Welcome to IT Support System",
        body="Thank you for using our IT support system. We're here to help!",
        reply_to="support@company.com"
    )
    
    if success:
        print("✓ Basic email sent successfully")
    else:
        print("✗ Failed to send basic email")


def example_ticket_notification():
    """Example of sending ticket notification emails."""
    
    print("\n=== Ticket Notification Example ===")
    
    emailer = Emailer(dry_run=True)
    
    # Send ticket created notification
    success = emailer.send_ticket_notification(
        to="employee@company.com",
        ticket_id="IT-001",
        ticket_summary="Printer not working in Marketing",
        status="new",
        priority="High",
        category="hardware",
        description="The HP LaserJet printer in Marketing department is showing 'Paper Jam' error and won't print. Multiple users affected.",
        template_type="ticket_created"
    )
    
    if success:
        print("✓ Ticket created notification sent")
    else:
        print("✗ Failed to send ticket notification")
    
    # Send ticket updated notification
    success = emailer.send_ticket_notification(
        to="employee@company.com",
        ticket_id="IT-001",
        ticket_summary="Printer not working in Marketing",
        status="in_progress",
        priority="High",
        category="hardware",
        description="The HP LaserJet printer in Marketing department is showing 'Paper Jam' error and won't print. Multiple users affected.",
        template_type="ticket_updated"
    )
    
    if success:
        print("✓ Ticket updated notification sent")
    else:
        print("✗ Failed to send ticket update notification")


def example_custom_template():
    """Example of using custom templates."""
    
    print("\n=== Custom Template Example ===")
    
    emailer = Emailer(dry_run=True)
    
    # Send email with custom template
    template_vars = {
        'template_type': 'escalation',
        'ticket_id': 'IT-002',
        'subject': 'Ticket Escalation Required',
        'body': 'Your ticket has been escalated due to high priority.',
        'escalation_reason': 'Critical system issue affecting multiple users',
        'urgency': 'High',
        'company_name': 'TechCorp Inc.'
    }
    
    success = emailer.send_email(
        to="manager@company.com",
        subject="Ticket Escalation Required",
        body="Your ticket has been escalated due to high priority.",
        template_name='ticket_notification',
        template_vars=template_vars,
        cc="supervisor@company.com"
    )
    
    if success:
        print("✓ Custom template email sent")
    else:
        print("✗ Failed to send custom template email")


def example_system_alert():
    """Example of sending system alert emails."""
    
    print("\n=== System Alert Example ===")
    
    emailer = Emailer(dry_run=True)
    
    # Send system alert
    success = emailer.send_system_alert(
        to=["admin@company.com", "tech@company.com"],
        alert_type="Database Connection",
        message="Database connection pool is running low. Current usage: 85%. Please investigate.",
        severity="high"
    )
    
    if success:
        print("✓ System alert sent")
    else:
        print("✗ Failed to send system alert")


def example_email_with_attachments():
    """Example of sending emails with attachments."""
    
    print("\n=== Email with Attachments Example ===")
    
    emailer = Emailer(dry_run=True)
    
    # Create a sample file for demonstration
    sample_file_path = "/tmp/sample_report.txt"
    try:
        with open(sample_file_path, 'w') as f:
            f.write("Sample IT Support Report\n")
            f.write("Generated on: 2024-01-01\n")
            f.write("Status: All systems operational\n")
    except Exception as e:
        print(f"Could not create sample file: {e}")
        return
    
    # Send email with attachment
    success = emailer.send_email(
        to="manager@company.com",
        subject="Monthly IT Support Report",
        body="Please find attached the monthly IT support report.",
        attachments=[sample_file_path]
    )
    
    if success:
        print("✓ Email with attachment sent")
    else:
        print("✗ Failed to send email with attachment")
    
    # Clean up sample file
    try:
        import os
        os.remove(sample_file_path)
    except:
        pass


def example_bulk_emails():
    """Example of sending emails to multiple recipients."""
    
    print("\n=== Bulk Email Example ===")
    
    emailer = Emailer(dry_run=True)
    
    # Multiple recipients
    recipients = [
        "user1@company.com",
        "user2@company.com", 
        "user3@company.com"
    ]
    
    # Send to multiple recipients
    success = emailer.send_email(
        to=recipients,
        subject="System Maintenance Notice",
        body="Scheduled maintenance will occur this weekend. Please plan accordingly.",
        cc="admin@company.com",
        bcc="audit@company.com"
    )
    
    if success:
        print(f"✓ Bulk email sent to {len(recipients)} recipients")
    else:
        print("✗ Failed to send bulk email")


def example_error_handling():
    """Example of error handling in email sending."""
    
    print("\n=== Error Handling Example ===")
    
    emailer = Emailer(dry_run=True)
    
    # Test with invalid email addresses
    print("Testing with invalid email addresses...")
    
    success = emailer.send_email(
        to="invalid-email",
        subject="Test Email",
        body="This should fail gracefully."
    )
    
    if success:
        print("✓ Email sent (unexpected)")
    else:
        print("✗ Email failed as expected")
    
    # Test with empty recipients
    print("\nTesting with empty recipients...")
    
    success = emailer.send_email(
        to="",
        subject="Test Email",
        body="This should also fail gracefully."
    )
    
    if success:
        print("✓ Email sent (unexpected)")
    else:
        print("✗ Email failed as expected")


def main():
    """Run all examples."""
    print("Emailer Module Examples")
    print("=" * 50)
    
    try:
        example_basic_email()
        example_ticket_notification()
        example_custom_template()
        example_system_alert()
        example_email_with_attachments()
        example_bulk_emails()
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Example failed with error: {e}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    main()
