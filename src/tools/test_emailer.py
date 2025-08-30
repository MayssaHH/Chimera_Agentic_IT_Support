"""Tests for emailer module functionality."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from .emailer import Emailer, EmailTemplate


class TestEmailTemplate:
    """Test the EmailTemplate class."""
    
    def setup_method(self):
        """Setup template for each test."""
        self.template = EmailTemplate("test_template")
    
    def test_initialization(self):
        """Test template initialization."""
        assert self.template.template_name == "test_template"
        assert "email_templates" in str(self.template.templates_dir)
    
    def test_render_html_fallback(self):
        """Test HTML rendering with fallback to default template."""
        html = self.template.render_html(
            subject="Test Subject",
            body="Test Body",
            company_name="Test Company"
        )
        
        assert "Test Subject" in html
        assert "Test Body" in html
        assert "Test Company" in html
        assert "<!DOCTYPE html>" in html
        assert "IT Support System" in html
    
    def test_render_text_fallback(self):
        """Test text rendering with fallback to default template."""
        text = self.template.render_text(
            subject="Test Subject",
            body="Test Body",
            company_name="Test Company"
        )
        
        assert "Test Subject" in text
        assert "Test Body" in text
        assert "Test Company" in text
        assert "IT Support System" in text
    
    def test_render_html_with_ticket_created(self):
        """Test HTML rendering with ticket_created template type."""
        html = self.template.render_html(
            template_type="ticket_created",
            ticket_id="IT-001",
            priority="High",
            category="hardware",
            description="Test description"
        )
        
        assert "IT-001" in html
        assert "High" in html
        assert "hardware" in html
        assert "Test description" in html
        assert "Ticket Details:" in html
    
    def test_render_text_with_ticket_updated(self):
        """Test text rendering with ticket_updated template type."""
        text = self.template.render_text(
            template_type="ticket_updated",
            ticket_id="IT-002",
            status="resolved",
            updated_by="tech_support",
            notes="Issue resolved"
        )
        
        assert "IT-002" in html
        assert "resolved" in html
        assert "tech_support" in html
        assert "Issue resolved" in html
        assert "Ticket Update:" in html
    
    def test_render_html_with_escalation(self):
        """Test HTML rendering with escalation template type."""
        html = self.template.render_html(
            template_type="escalation",
            ticket_id="IT-003",
            escalation_reason="Critical issue",
            urgency="High"
        )
        
        assert "IT-003" in html
        assert "Critical issue" in html
        assert "High" in html
        assert "Escalation Required:" in html


class TestEmailer:
    """Test the Emailer class."""
    
    def setup_method(self):
        """Setup emailer for each test."""
        # Mock the settings to avoid config dependency
        with patch('src.tools.emailer.settings') as mock_settings:
            mock_settings.smtp_host = "smtp.test.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_user = "test@test.com"
            mock_settings.smtp_password = "test_password"
            mock_settings.smtp_use_tls = True
            
            self.emailer = Emailer(dry_run=True)
    
    def test_initialization(self):
        """Test emailer initialization."""
        assert self.emailer.dry_run is True
        assert self.emailer.smtp_host == "smtp.test.com"
        assert self.emailer.smtp_port == 587
        assert self.emailer.smtp_user == "test@test.com"
        assert self.emailer.smtp_password == "test_password"
        assert self.emailer.smtp_use_tls is True
    
    def test_normalize_emails_string(self):
        """Test email normalization from string."""
        emails = self.emailer._normalize_emails("user1@test.com, user2@test.com")
        assert emails == ["user1@test.com", "user2@test.com"]
    
    def test_normalize_emails_list(self):
        """Test email normalization from list."""
        emails = self.emailer._normalize_emails(["user1@test.com", "user2@test.com"])
        assert emails == ["user1@test.com", "user2@test.com"]
    
    def test_normalize_emails_empty(self):
        """Test email normalization with empty input."""
        emails = self.emailer._normalize_emails("")
        assert emails == []
        
        emails = self.emailer._normalize_emails(None)
        assert emails == []
    
    def test_convert_text_to_html(self):
        """Test text to HTML conversion."""
        text = "Line 1\nLine 2\nLine 3"
        html = self.emailer._convert_text_to_html(text)
        
        assert "<!DOCTYPE html>" in html
        assert "<br>" in html
        assert "Line 1" in html
        assert "Line 2" in html
        assert "Line 3" in html
    
    def test_add_attachment_file_not_found(self):
        """Test adding attachment when file doesn't exist."""
        msg = Mock()
        
        # Should not raise exception, just log warning
        self.emailer._add_attachment(msg, "/nonexistent/file.txt")
        
        # Verify no attachment was added
        msg.attach.assert_not_called()
    
    def test_add_attachment_success(self):
        """Test successfully adding attachment."""
        msg = Mock()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            temp_file = f.name
        
        try:
            self.emailer._add_attachment(msg, temp_file)
            
            # Verify attachment was added
            msg.attach.assert_called_once()
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_test_connection_dry_run(self):
        """Test connection test in dry-run mode."""
        result = self.emailer.test_connection()
        assert result is True
    
    def test_send_email_dry_run(self):
        """Test sending email in dry-run mode."""
        success = self.emailer.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert success is True
    
    def test_send_email_with_template(self):
        """Test sending email with template."""
        success = self.emailer.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
            template_name="test_template",
            template_vars={
                'subject': 'Test Subject',
                'body': 'Test Body',
                'company_name': 'Test Company'
            }
        )
        
        assert success is True
    
    def test_send_email_with_attachments(self):
        """Test sending email with attachments."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test attachment content")
            temp_file = f.name
        
        try:
            success = self.emailer.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
                attachments=[temp_file]
            )
            
            assert success is True
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_send_email_multiple_recipients(self):
        """Test sending email to multiple recipients."""
        success = self.emailer.send_email(
            to=["user1@test.com", "user2@test.com"],
            subject="Test Subject",
            body="Test Body",
            cc="cc@test.com",
            bcc="bcc@test.com"
        )
        
        assert success is True
    
    def test_send_ticket_notification(self):
        """Test sending ticket notification."""
        success = self.emailer.send_ticket_notification(
            to="employee@test.com",
            ticket_id="IT-001",
            ticket_summary="Test Issue",
            status="new",
            priority="Medium",
            category="software",
            description="Test description"
        )
        
        assert success is True
    
    def test_send_system_alert(self):
        """Test sending system alert."""
        success = self.emailer.send_system_alert(
            to="admin@test.com",
            alert_type="Database",
            message="Test alert message",
            severity="high"
        )
        
        assert success is True


class TestEmailerLiveMode:
    """Test Emailer in live mode (with mocked SMTP)."""
    
    def setup_method(self):
        """Setup emailer for each test."""
        with patch('src.tools.emailer.settings') as mock_settings:
            mock_settings.smtp_host = "smtp.test.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_user = "test@test.com"
            mock_settings.smtp_password = "test_password"
            mock_settings.smtp_use_tls = True
            
            self.emailer = Emailer(dry_run=False)
    
    @patch('smtplib.SMTP')
    def test_send_email_live_success(self, mock_smtp):
        """Test successful email sending in live mode."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        success = self.emailer.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert success is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "test_password")
        mock_server.sendmail.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_live_connection_error(self, mock_smtp):
        """Test email sending with connection error."""
        # Mock SMTP connection error
        mock_smtp.side_effect = Exception("Connection failed")
        
        success = self.emailer.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert success is False
    
    @patch('smtplib.SMTP')
    def test_test_connection_live_success(self, mock_smtp):
        """Test successful connection test in live mode."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.emailer.test_connection()
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_test_connection_live_failure(self, mock_smtp):
        """Test failed connection test in live mode."""
        # Mock SMTP connection error
        mock_smtp.side_effect = Exception("Connection failed")
        
        result = self.emailer.test_connection()
        
        assert result is False


class TestEmailerEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Setup emailer for each test."""
        with patch('src.tools.emailer.settings') as mock_settings:
            mock_settings.smtp_host = "smtp.test.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_user = "test@test.com"
            mock_settings.smtp_password = "test_password"
            mock_settings.smtp_use_tls = True
            
            self.emailer = Emailer(dry_run=True)
    
    def test_send_email_empty_recipients(self):
        """Test sending email with empty recipients."""
        success = self.emailer.send_email(
            to="",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Should handle gracefully
        assert success is False
    
    def test_send_email_none_recipients(self):
        """Test sending email with None recipients."""
        success = self.emailer.send_email(
            to=None,
            subject="Test Subject",
            body="Test Body"
        )
        
        # Should handle gracefully
        assert success is False
    
    def test_send_email_invalid_email_format(self):
        """Test sending email with invalid email format."""
        success = self.emailer.send_email(
            to="invalid-email-format",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Should handle gracefully
        assert success is False
    
    def test_send_email_with_reply_to(self):
        """Test sending email with reply-to address."""
        success = self.emailer.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
            reply_to="support@test.com"
        )
        
        assert success is True


if __name__ == "__main__":
    pytest.main([__file__])
