"""Email client for sending transactional emails via SMTP."""

import logging
from typing import List, Optional, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from pathlib import Path
import os

from ..config import settings


logger = logging.getLogger(__name__)


class EmailTemplate:
    """Base class for email templates."""
    
    def __init__(self, template_name: str):
        """
        Initialize template.
        
        Args:
            template_name: Name of the template file
        """
        self.template_name = template_name
        self.templates_dir = Path(__file__).parent / "email_templates"
    
    def render_html(self, **kwargs) -> str:
        """Render HTML template with variables."""
        template_path = self.templates_dir / f"{self.template_name}.html"
        
        if not template_path.exists():
            # Fallback to default HTML template
            return self._get_default_html_template(**kwargs)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Simple variable substitution
            for key, value in kwargs.items():
                placeholder = f"{{{{{key}}}}}"
                template_content = template_content.replace(placeholder, str(value))
            
            return template_content
            
        except Exception as e:
            logger.error(f"Failed to render HTML template {template_name}: {e}")
            return self._get_default_html_template(**kwargs)
    
    def render_text(self, **kwargs) -> str:
        """Render plain text template with variables."""
        template_path = self.templates_dir / f"{self.template_name}.txt"
        
        if not template_path.exists():
            # Fallback to default text template
            return self._get_default_text_template(**kwargs)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Simple variable substitution
            for key, value in kwargs.items():
                placeholder = f"{{{{{key}}}}}"
                template_content = template_content.replace(placeholder, str(value))
            
            return template_content
            
        except Exception as e:
            logger.error(f"Failed to render text template {template_name}: {e}")
            return self._get_default_text_template(**kwargs)
    
    def _get_default_html_template(self, **kwargs) -> str:
        """Get default HTML template if custom template not found."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{kwargs.get('subject', 'IT Support Notification')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .content {{ background-color: #ffffff; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>IT Support System</h2>
                </div>
                <div class="content">
                    <h3>{kwargs.get('subject', 'Notification')}</h3>
                    <p>{kwargs.get('body', 'This is an automated message from the IT Support system.')}</p>
                    {self._render_html_content(kwargs)}
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply directly to this email.</p>
                    <p>IT Support System - {kwargs.get('company_name', 'Your Company')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_default_text_template(self, **kwargs) -> str:
        """Get default plain text template if custom template not found."""
        return f"""
IT Support System
=================

{kwargs.get('subject', 'Notification')}

{kwargs.get('body', 'This is an automated message from the IT Support system.')}

{self._render_text_content(kwargs)}

---
This is an automated message. Please do not reply directly to this email.
IT Support System - {kwargs.get('company_name', 'Your Company')}
        """
    
    def _render_html_content(self, kwargs: Dict[str, Any]) -> str:
        """Render additional HTML content based on template type."""
        template_type = kwargs.get('template_type', 'general')
        
        if template_type == 'ticket_created':
            return f"""
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h4>Ticket Details:</h4>
                    <p><strong>Ticket ID:</strong> {kwargs.get('ticket_id', 'N/A')}</p>
                    <p><strong>Priority:</strong> {kwargs.get('priority', 'N/A')}</p>
                    <p><strong>Category:</strong> {kwargs.get('category', 'N/A')}</p>
                    <p><strong>Description:</strong> {kwargs.get('description', 'N/A')}</p>
                </div>
            """
        elif template_type == 'ticket_updated':
            return f"""
                <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h4>Ticket Update:</h4>
                    <p><strong>Ticket ID:</strong> {kwargs.get('ticket_id', 'N/A')}</p>
                    <p><strong>New Status:</strong> {kwargs.get('status', 'N/A')}</p>
                    <p><strong>Updated By:</strong> {kwargs.get('updated_by', 'N/A')}</p>
                    <p><strong>Notes:</strong> {kwargs.get('notes', 'N/A')}</p>
                </div>
            """
        elif template_type == 'escalation':
            return f"""
                <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h4>Escalation Required:</h4>
                    <p><strong>Ticket ID:</strong> {kwargs.get('ticket_id', 'N/A')}</p>
                    <p><strong>Reason:</strong> {kwargs.get('escalation_reason', 'N/A')}</p>
                    <p><strong>Urgency:</strong> {kwargs.get('urgency', 'N/A')}</p>
                </div>
            """
        
        return ""
    
    def _render_text_content(self, kwargs: Dict[str, Any]) -> str:
        """Render additional text content based on template type."""
        template_type = kwargs.get('template_type', 'general')
        
        if template_type == 'ticket_created':
            return f"""
Ticket Details:
- Ticket ID: {kwargs.get('ticket_id', 'N/A')}
- Priority: {kwargs.get('priority', 'N/A')}
- Category: {kwargs.get('category', 'N/A')}
- Description: {kwargs.get('description', 'N/A')}
            """
        elif template_type == 'ticket_updated':
            return f"""
Ticket Update:
- Ticket ID: {kwargs.get('ticket_id', 'N/A')}
- New Status: {kwargs.get('status', 'N/A')}
- Updated By: {kwargs.get('updated_by', 'N/A')}
- Notes: {kwargs.get('notes', 'N/A')}
            """
        elif template_type == 'escalation':
            return f"""
Escalation Required:
- Ticket ID: {kwargs.get('ticket_id', 'N/A')}
- Reason: {kwargs.get('escalation_reason', 'N/A')}
- Urgency: {kwargs.get('urgency', 'N/A')}
            """
        
        return ""


class Emailer:
    """Email client for sending transactional emails."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize emailer.
        
        Args:
            dry_run: If True, simulate sending without actually sending emails
        """
        self.dry_run = dry_run
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
        
        if dry_run:
            logger.info("Emailer initialized in DRY-RUN mode")
        else:
            logger.info(f"Emailer initialized for {self.smtp_host}:{self.smtp_port}")
    
    def send_email(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        reply_to: Optional[str] = None,
        template_name: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
        cc: Optional[str | List[str]] = None,
        bcc: Optional[str | List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email with optional template rendering.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body (plain text)
            reply_to: Reply-to email address
            template_name: Name of template to use
            template_vars: Variables for template rendering
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            attachments: List of file paths to attach
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Normalize recipients
            to_emails = self._normalize_emails(to)
            cc_emails = self._normalize_emails(cc) if cc else []
            bcc_emails = self._normalize_emails(bcc) if bcc else []
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Render templates if specified
            if template_name and template_vars:
                template = EmailTemplate(template_name)
                html_body = template.render_html(**template_vars)
                text_body = template.render_text(**template_vars)
            else:
                html_body = self._convert_text_to_html(body)
                text_body = body
            
            # Add plain text part
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    self._add_attachment(msg, attachment_path)
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would send email to {to_emails}")
                logger.info(f"[DRY-RUN] Subject: {subject}")
                logger.info(f"[DRY-RUN] Body length: {len(body)} characters")
                return True
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                server.login(self.smtp_user, self.smtp_password)
                
                # Combine all recipients
                all_recipients = to_emails + cc_emails + bcc_emails
                
                # Send email
                server.sendmail(self.smtp_user, all_recipients, msg.as_string())
                
                logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _normalize_emails(self, emails: str | List[str]) -> List[str]:
        """Normalize email addresses to list format."""
        if isinstance(emails, str):
            return [email.strip() for email in emails.split(',')]
        elif isinstance(emails, list):
            return [email.strip() for email in emails]
        else:
            return []
    
    def _convert_text_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML."""
        # Convert line breaks to <br> tags
        html = text.replace('\n', '<br>')
        
        # Wrap in basic HTML structure
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """Add file attachment to email."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Attachment file not found: {file_path}")
                return
            
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            
            msg.attach(part)
            logger.info(f"Attachment added: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to add attachment {file_path}: {e}")
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection and authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.dry_run:
                return True
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                server.login(self.smtp_user, self.smtp_password)
                logger.info("SMTP connection test successful")
                return True
                
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_ticket_notification(
        self,
        to: str | List[str],
        ticket_id: str,
        ticket_summary: str,
        status: str,
        priority: str,
        category: str,
        description: str,
        template_type: str = "ticket_created"
    ) -> bool:
        """
        Send ticket notification email using predefined template.
        
        Args:
            to: Recipient email address(es)
            ticket_id: Ticket identifier
            ticket_summary: Ticket summary/title
            status: Current ticket status
            priority: Ticket priority
            category: Ticket category
            description: Ticket description
            template_type: Type of notification (ticket_created, ticket_updated, escalation)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        template_vars = {
            'template_type': template_type,
            'ticket_id': ticket_id,
            'subject': f"IT Support Ticket: {ticket_summary}",
            'body': f"Your IT support ticket has been {template_type.replace('_', ' ')}.",
            'priority': priority,
            'category': category,
            'description': description,
            'status': status,
            'company_name': 'Your Company'
        }
        
        return self.send_email(
            to=to,
            subject=template_vars['subject'],
            body=template_vars['body'],
            template_name='ticket_notification',
            template_vars=template_vars
        )
    
    def send_system_alert(
        self,
        to: str | List[str],
        alert_type: str,
        message: str,
        severity: str = "medium"
    ) -> bool:
        """
        Send system alert email.
        
        Args:
            to: Recipient email address(es)
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity (low, medium, high, critical)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"System Alert: {alert_type} - {severity.upper()}"
        
        template_vars = {
            'template_type': 'system_alert',
            'subject': subject,
            'body': message,
            'alert_type': alert_type,
            'severity': severity,
            'company_name': 'Your Company'
        }
        
        return self.send_email(
            to=to,
            subject=subject,
            body=message,
            template_name='system_alert',
            template_vars=template_vars
        )
