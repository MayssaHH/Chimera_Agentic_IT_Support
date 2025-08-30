"""Tests for Jira client functionality."""

import pytest
from unittest.mock import Mock, patch
from .jira import JiraClient


class TestJiraClient:
    """Test the JiraClient class."""
    
    def setup_method(self):
        """Setup client for each test."""
        # Mock the settings to avoid config dependency
        with patch('src.tools.jira.settings') as mock_settings:
            mock_settings.jira_base_url = "https://test.atlassian.net"
            mock_settings.jira_user = "test_user"
            mock_settings.jira_token = "test_token"
            
            self.client = JiraClient(dry_run=True)
    
    def test_initialization(self):
        """Test client initialization."""
        assert self.client.dry_run is True
        assert self.client.base_url == "https://test.atlassian.net"
        assert self.client.auth == ("test_user", "test_token")
    
    def test_workflow_states(self):
        """Test workflow state mappings."""
        states = self.client.get_workflow_states()
        
        expected_states = {
            "new": "10000",
            "in_progress": "3", 
            "resolved": "10001",
            "closed": "6"
        }
        
        assert states == expected_states
    
    def test_create_ticket_dry_run(self):
        """Test ticket creation in dry-run mode."""
        ticket = self.client.create_ticket(
            summary="Test ticket",
            description="Test description",
            employee_id="emp_001"
        )
        
        assert ticket["id"] == "DRY-RUN-001"
        assert ticket["key"] == "IT-DRY-001"
        assert ticket["summary"] == "Test ticket"
        assert ticket["status"] == "new"
    
    def test_create_ticket_with_priority_and_type(self):
        """Test ticket creation with custom priority and type."""
        ticket = self.client.create_ticket(
            summary="Critical issue",
            description="Urgent problem",
            employee_id="emp_001",
            priority="Critical",
            issue_type="Bug"
        )
        
        assert ticket["summary"] == "Critical issue"
        assert ticket["status"] == "new"
    
    def test_transition_ticket_dry_run(self):
        """Test ticket transition in dry-run mode."""
        result = self.client.transition_ticket("TEST-001", "in_progress")
        assert result is True
    
    def test_transition_ticket_invalid_status(self):
        """Test ticket transition with invalid status."""
        result = self.client.transition_ticket("TEST-001", "invalid_status")
        assert result is False
    
    def test_get_ticket_dry_run(self):
        """Test getting ticket details in dry-run mode."""
        ticket = self.client.get_ticket("TEST-001")
        
        assert ticket is not None
        assert ticket["id"] == "TEST-001"
        assert ticket["key"] == "IT-TEST-001"
        assert ticket["status"] == "new"
        assert ticket["assignee"] == "employee_001"
    
    def test_search_employee_tickets_dry_run(self):
        """Test employee ticket search in dry-run mode."""
        tickets = self.client.search_employee_tickets("emp_001")
        
        assert len(tickets) == 3  # Default dry-run returns 3 tickets
        assert all(ticket["assignee"] == "emp_001" for ticket in tickets)
        assert all(ticket["status"] == "new" for ticket in tickets)
    
    def test_search_employee_tickets_with_status_filter(self):
        """Test employee ticket search with status filter."""
        tickets = self.client.search_employee_tickets(
            "emp_001", 
            status="in_progress"
        )
        
        assert len(tickets) == 3
        assert all(ticket["assignee"] == "emp_001" for ticket in tickets)
    
    def test_search_employee_tickets_with_max_results(self):
        """Test employee ticket search with max results limit."""
        tickets = self.client.search_employee_tickets(
            "emp_001", 
            max_results=1
        )
        
        assert len(tickets) == 1
    
    def test_validate_credentials_dry_run(self):
        """Test credential validation in dry-run mode."""
        result = self.client.validate_credentials()
        assert result is True
    
    def test_get_project_info_dry_run(self):
        """Test getting project info in dry-run mode."""
        project_info = self.client.get_project_info("IT")
        
        assert project_info is not None
        assert project_info["key"] == "IT"
        assert project_info["name"] == "IT Support"
        assert project_info["projectTypeKey"] == "software"
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with JiraClient(dry_run=True) as jira:
            assert jira.dry_run is True
            # Client should be accessible within context
        
        # Client should be closed after context exit
        # Note: In dry-run mode, close() doesn't do much, but we can test the method exists
        assert hasattr(jira, 'close')
    
    def test_extract_description_empty(self):
        """Test description extraction with empty description."""
        description = self.client._extract_description({})
        assert description == ""
        
        description = self.client._extract_description(None)
        assert description == ""
    
    def test_extract_description_simple(self):
        """Test description extraction with simple text."""
        description_obj = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Simple description"
                        }
                    ]
                }
            ]
        }
        
        description = self.client._extract_description(description_obj)
        assert description == "Simple description"
    
    def test_extract_description_complex(self):
        """Test description extraction with complex nested content."""
        description_obj = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "First paragraph"
                        }
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Second paragraph"
                        }
                    ]
                }
            ]
        }
        
        description = self.client._extract_description(description_obj)
        assert "First paragraph" in description
        assert "Second paragraph" in description


class TestJiraClientLiveMode:
    """Test JiraClient in live mode (with mocked HTTP responses)."""
    
    def setup_method(self):
        """Setup client for each test."""
        with patch('src.tools.jira.settings') as mock_settings:
            mock_settings.jira_base_url = "https://test.atlassian.net"
            mock_settings.jira_user = "test_user"
            mock_settings.jira_token = "test_token"
            
            self.client = JiraClient(dry_run=False)
    
    @patch('httpx.Client.request')
    def test_create_ticket_live(self, mock_request):
        """Test ticket creation in live mode."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "12345",
            "key": "IT-123"
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        ticket = self.client.create_ticket(
            summary="Test ticket",
            description="Test description",
            employee_id="emp_001"
        )
        
        assert ticket["id"] == "12345"
        assert ticket["key"] == "IT-123"
        assert ticket["summary"] == "Test ticket"
        assert ticket["status"] == "new"
    
    @patch('httpx.Client.request')
    def test_transition_ticket_live(self, mock_request):
        """Test ticket transition in live mode."""
        # Mock transitions response
        mock_transitions_response = Mock()
        mock_transitions_response.status_code = 200
        mock_transitions_response.json.return_value = {
            "transitions": [
                {
                    "id": "transition_123",
                    "to": {"id": "3", "name": "In Progress"}
                }
            ]
        }
        mock_transitions_response.raise_for_status.return_value = None
        
        # Mock transition response
        mock_transition_response = Mock()
        mock_transition_response.status_code = 204
        mock_transition_response.raise_for_status.return_value = None
        
        mock_request.side_effect = [mock_transitions_response, mock_transition_response]
        
        result = self.client.transition_ticket("TEST-001", "in_progress")
        assert result is True
    
    @patch('httpx.Client.request')
    def test_get_ticket_live(self, mock_request):
        """Test getting ticket details in live mode."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "key": "IT-123",
            "fields": {
                "summary": "Test ticket",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Test description"
                                }
                            ]
                        }
                    ]
                },
                "status": {"id": "10000", "name": "To Do"},
                "priority": {"name": "Medium"},
                "assignee": {"accountId": "emp_001"},
                "reporter": {"accountId": "emp_001"},
                "created": "2024-01-01T00:00:00.000Z",
                "updated": "2024-01-01T00:00:00.000Z",
                "labels": ["it-support"]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        ticket = self.client.get_ticket("IT-123")
        
        assert ticket is not None
        assert ticket["key"] == "IT-123"
        assert ticket["summary"] == "Test ticket"
        assert ticket["status"] == "new"  # Mapped from status ID 10000
        assert ticket["assignee"] == "emp_001"


if __name__ == "__main__":
    pytest.main([__file__])
