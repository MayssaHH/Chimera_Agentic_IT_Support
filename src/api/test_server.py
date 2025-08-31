"""
Test file for the Local IT Support API server.

This file contains basic tests to verify the API endpoints work correctly.
"""

import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Import the FastAPI app
from server import app

# Create test client
client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Local IT Support API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    def test_create_request(self):
        """Test creating a new IT support request."""
        request_data = {
            "employee_id": "EMP001",
            "request_type": "software_access",
            "title": "Test Request",
            "description": "Test description",
            "priority": "medium",
            "urgency": "normal"
        }
        
        response = client.post("/request", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "ticket_id" in data
        assert data["decision"] == "pending"
        assert data["status"] == "pending"
        assert data["next_action"] == "workflow_starting"
    
    def test_create_request_invalid_data(self):
        """Test creating a request with invalid data."""
        # Missing required fields
        request_data = {
            "employee_id": "EMP001"
            # Missing title, description, etc.
        }
        
        response = client.post("/request", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_tickets_no_filters(self):
        """Test getting tickets without filters."""
        response = client.get("/tickets")
        assert response.status_code == 200
        
        data = response.json()
        assert "tickets" in data
        assert "count" in data
        assert isinstance(data["tickets"], list)
    
    def test_get_tickets_with_filters(self):
        """Test getting tickets with filters."""
        response = client.get("/tickets?employee_id=EMP001")
        assert response.status_code == 200
        
        data = response.json()
        assert "tickets" in data
        assert "count" in data
    
    def test_hil_endpoint_not_found(self):
        """Test HIL endpoint with non-existent ticket."""
        hil_data = {
            "answer": "Test answer",
            "approval": True,
            "approver_id": "MANAGER001"
        }
        
        response = client.post("/hil/non-existent-ticket", json=hil_data)
        assert response.status_code == 404
    
    def test_events_endpoint_not_found(self):
        """Test events endpoint with non-existent ticket."""
        response = client.get("/events/non-existent-ticket")
        assert response.status_code == 404


class TestAPIValidation:
    """Test cases for API validation."""
    
    def test_user_request_validation(self):
        """Test UserRequest model validation."""
        from server import UserRequest
        
        # Valid request
        valid_request = UserRequest(
            employee_id="EMP001",
            request_type="software_access",
            title="Valid Request",
            description="Valid description",
            priority="high",
            urgency="urgent"
        )
        assert valid_request.employee_id == "EMP001"
        assert valid_request.priority == "high"
        
        # Test default values
        assert valid_request.business_justification is None
        assert valid_request.desired_completion_date is None
    
    def test_hil_response_validation(self):
        """Test HILResponse model validation."""
        from server import HILResponse
        
        # Valid HIL response
        valid_response = HILResponse(
            answer="Approved",
            approval=True,
            approver_id="MANAGER001"
        )
        assert valid_response.approval is True
        assert valid_response.comments is None  # Optional field


class TestWorkflowIntegration:
    """Test cases for workflow integration."""
    
    def test_app_state_initialization(self):
        """Test AppState initialization."""
        from server import AppState
        
        app_state = AppState()
        assert hasattr(app_state, 'workflow')
        assert hasattr(app_state, 'active_tickets')
        assert hasattr(app_state, 'event_streams')
        assert len(app_state.active_tickets) == 0
    
    def test_ticket_creation(self):
        """Test ticket creation in AppState."""
        from server import AppState, UserRequest
        
        app_state = AppState()
        
        request = UserRequest(
            employee_id="EMP001",
            request_type="software_access",
            title="Test Request",
            description="Test description",
            priority="medium",
            urgency="normal"
        )
        
        ticket_id = app_state.create_ticket(request)
        assert ticket_id in app_state.active_tickets
        assert app_state.active_tickets[ticket_id]["employee_id"] == "EMP001"
        assert ticket_id in app_state.event_streams


def test_imports():
    """Test that all required modules can be imported."""
    try:
        from server import app, AppState, UserRequest, HILResponse
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import required modules: {e}")


if __name__ == "__main__":
    # Run basic tests
    print("Running API tests...")
    
    # Test imports
    try:
        test_imports()
        print("✅ Imports successful")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
    
    # Test basic functionality
    try:
        test_api = TestAPIEndpoints()
        test_api.test_health_check()
        test_api.test_root_endpoint()
        print("✅ Basic endpoint tests passed")
    except Exception as e:
        print(f"❌ Basic endpoint tests failed: {e}")
    
    print("Tests completed!")
