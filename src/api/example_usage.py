"""
Example usage of the Local IT Support API

This file demonstrates how to interact with the API endpoints
for creating requests, handling HIL interactions, and streaming events.
"""

import asyncio
import json
import requests
from typing import Dict, Any


class ITSupportAPIClient:
    """Client for interacting with the IT Support API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new IT support request."""
        url = f"{self.base_url}/request"
        response = self.session.post(url, json=request_data)
        response.raise_for_status()
        return response.json()
    
    def submit_hil_response(self, ticket_id: str, hil_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit human-in-the-loop response."""
        url = f"{self.base_url}/hil/{ticket_id}"
        response = self.session.post(url, json=hil_data)
        response.raise_for_status()
        return response.json()
    
    def get_tickets(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get tickets with optional filters."""
        url = f"{self.base_url}/tickets"
        params = filters or {}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_health(self) -> Dict[str, Any]:
        """Check API health."""
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


async def stream_events(ticket_id: str, base_url: str = "http://localhost:8000"):
    """Stream events for a specific ticket using Server-Sent Events."""
    import aiohttp
    
    url = f"{base_url}/events/{ticket_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Failed to connect to event stream: {response.status}")
                return
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    try:
                        event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                        print(f"Event: {json.dumps(event_data, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {line}")


def example_workflow():
    """Example of a complete workflow using the API."""
    client = ITSupportAPIClient()
    
    # 1. Create a new IT support request
    print("=== Creating IT Support Request ===")
    request_data = {
        "employee_id": "EMP001",
        "request_type": "software_access",
        "title": "Request for Admin Access to Database",
        "description": "Need admin access to the customer database for data analysis tasks",
        "priority": "high",
        "urgency": "urgent",
        "business_justification": "Required for quarterly business review and customer insights analysis",
        "desired_completion_date": "2024-01-15T00:00:00Z"
    }
    
    try:
        response = client.create_request(request_data)
        print(f"Request created successfully!")
        print(f"Ticket ID: {response['ticket_id']}")
        print(f"Status: {response['status']}")
        print(f"Next Action: {response['next_action']}")
        
        ticket_id = response['ticket_id']
        
        # 2. Get tickets for the employee
        print("\n=== Retrieving Employee Tickets ===")
        tickets = client.get_tickets({"employee_id": "EMP001"})
        print(f"Found {tickets['count']} tickets for employee EMP001")
        for ticket in tickets['tickets']:
            print(f"- {ticket['title']} (Status: {ticket['status']})")
        
        # 3. Simulate human approval (if needed)
        print("\n=== Simulating Human Approval ===")
        hil_data = {
            "answer": "Approved with conditions",
            "approval": True,
            "comments": "Access granted for 30 days with audit logging enabled",
            "approver_id": "MANAGER001"
        }
        
        hil_response = client.submit_hil_response(ticket_id, hil_data)
        print(f"HIL response submitted successfully!")
        print(f"Updated Status: {hil_response['status']}")
        print(f"Decision: {hil_response['decision']}")
        
        # 4. Check final status
        print("\n=== Final Status Check ===")
        final_tickets = client.get_tickets({"employee_id": "EMP001"})
        for ticket in final_tickets['tickets']:
            if ticket['ticket_id'] == ticket_id:
                print(f"Final status for ticket {ticket_id}: {ticket['status']}")
                break
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def example_event_streaming():
    """Example of streaming events for a ticket."""
    print("=== Event Streaming Example ===")
    
    # This would typically be called with a real ticket ID
    # For demonstration, we'll show the structure
    ticket_id = "example-ticket-123"
    
    print(f"Starting event stream for ticket: {ticket_id}")
    print("Note: This requires the server to be running and the ticket to exist")
    print("To test this, create a ticket first and use its ID")
    
    # Uncomment the line below to actually stream events
    # await stream_events(ticket_id)


def main():
    """Main function to run examples."""
    print("Local IT Support API - Example Usage")
    print("=" * 50)
    
    # Check if server is running
    client = ITSupportAPIClient()
    try:
        health = client.get_health()
        print(f"✅ Server is running: {health['status']}")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the server first:")
        print("   cd src/api && python server.py")
        return
    
    print("\n" + "=" * 50)
    
    # Run workflow example
    example_workflow()
    
    print("\n" + "=" * 50)
    
    # Show event streaming example
    asyncio.run(example_event_streaming())
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()
