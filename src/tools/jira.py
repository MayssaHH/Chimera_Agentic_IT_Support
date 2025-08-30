"""Jira client for ticket management and workflow transitions."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import settings


logger = logging.getLogger(__name__)


class JiraClient:
    """Jira client for managing IT support tickets."""
    
    # Workflow state mapping
    WORKFLOW_STATES = {
        "new": "10000",  # To Do
        "in_progress": "3",  # In Progress
        "resolved": "10001",  # Done
        "closed": "6",  # Closed
    }
    
    # Reverse mapping for status lookups
    STATUS_MAPPING = {
        "10000": "new",
        "3": "in_progress", 
        "10001": "resolved",
        "6": "closed",
    }
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize Jira client.
        
        Args:
            dry_run: If True, simulate operations without making actual API calls
        """
        self.dry_run = dry_run
        self.base_url = settings.jira_base_url.rstrip('/')
        self.auth = (settings.jira_user, settings.jira_token)
        
        # HTTP client with timeout
        self.client = httpx.Client(
            timeout=30.0,
            auth=self.auth,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
        
        if dry_run:
            logger.info("Jira client initialized in DRY-RUN mode")
        else:
            logger.info(f"Jira client initialized for {self.base_url}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Jira API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            data: Request payload
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            httpx.HTTPStatusError: For HTTP errors
            httpx.RequestError: For network/connection errors
        """
        url = f"{self.base_url}/rest/api/3{endpoint}"
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] {method} {url}")
            if data:
                logger.info(f"[DRY-RUN] Request data: {data}")
            return {"dry_run": True, "url": url, "method": method}
        
        try:
            response = self.client.request(
                method=method,
                url=url,
                json=data,
                params=params
            )
            response.raise_for_status()
            
            if response.status_code == 204:  # No content
                return {"success": True}
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Jira API error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Jira request error: {e}")
            raise
    
    def create_ticket(
        self, 
        summary: str, 
        description: str, 
        employee_id: str,
        priority: str = "Medium",
        issue_type: str = "Task"
    ) -> Dict[str, Any]:
        """
        Create a new Jira ticket.
        
        Args:
            summary: Ticket summary/title
            description: Detailed description
            employee_id: Employee ID for assignment
            priority: Ticket priority (Low, Medium, High, Critical)
            issue_type: Type of issue (Task, Bug, Story, etc.)
            
        Returns:
            Created ticket data
        """
        ticket_data = {
            "fields": {
                "project": {"key": "IT"},  # Default project key
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
                "assignee": {"accountId": employee_id},
                "reporter": {"accountId": employee_id},
                "labels": ["it-support", "auto-generated"]
            }
        }
        
        logger.info(f"Creating ticket: {summary}")
        response = self._make_request("POST", "/issue", data=ticket_data)
        
        if self.dry_run:
            return {
                "id": "DRY-RUN-001",
                "key": "IT-DRY-001",
                "summary": summary,
                "status": "new"
            }
        
        return {
            "id": response["id"],
            "key": response["key"],
            "summary": summary,
            "status": "new"
        }
    
    def transition_ticket(self, ticket_id: str, status: str) -> bool:
        """
        Transition ticket to a new workflow state.
        
        Args:
            ticket_id: Jira ticket ID or key
            status: Target status (new, in_progress, resolved, closed)
            
        Returns:
            True if transition successful, False otherwise
        """
        if status not in self.WORKFLOW_STATES:
            logger.error(f"Invalid status: {status}. Valid states: {list(self.WORKFLOW_STATES.keys())}")
            return False
        
        transition_id = self.WORKFLOW_STATES[status]
        
        # Get available transitions for the ticket
        transitions_response = self._make_request("GET", f"/issue/{ticket_id}/transitions")
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Transitioning {ticket_id} to {status}")
            return True
        
        available_transitions = transitions_response.get("transitions", [])
        target_transition = None
        
        for transition in available_transitions:
            if transition["to"]["id"] == transition_id:
                target_transition = transition
                break
        
        if not target_transition:
            logger.error(f"Transition to {status} not available for ticket {ticket_id}")
            logger.debug(f"Available transitions: {[t['to']['name'] for t in available_transitions]}")
            return False
        
        # Perform the transition
        transition_data = {
            "transition": {"id": target_transition["id"]}
        }
        
        try:
            self._make_request("POST", f"/issue/{ticket_id}/transitions", data=transition_data)
            logger.info(f"Successfully transitioned ticket {ticket_id} to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to transition ticket {ticket_id} to {status}: {e}")
            return False
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get ticket details by ID or key.
        
        Args:
            ticket_id: Jira ticket ID or key
            
        Returns:
            Ticket data or None if not found
        """
        try:
            response = self._make_request("GET", f"/issue/{ticket_id}")
            
            if self.dry_run:
                return {
                    "id": ticket_id,
                    "key": f"IT-{ticket_id}",
                    "summary": "Sample ticket",
                    "status": "new",
                    "assignee": "employee_001"
                }
            
            fields = response.get("fields", {})
            
            # Map Jira status to our workflow states
            status_id = fields.get("status", {}).get("id")
            mapped_status = self.STATUS_MAPPING.get(status_id, "unknown")
            
            return {
                "id": response["id"],
                "key": response["key"],
                "summary": fields.get("summary", ""),
                "description": self._extract_description(fields.get("description", {})),
                "status": mapped_status,
                "priority": fields.get("priority", {}).get("name", "Medium"),
                "assignee": fields.get("assignee", {}).get("accountId"),
                "reporter": fields.get("reporter", {}).get("accountId"),
                "created": fields.get("created"),
                "updated": fields.get("updated"),
                "labels": fields.get("labels", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticket {ticket_id}: {e}")
            return None
    
    def search_employee_tickets(
        self, 
        employee_id: str, 
        status: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for tickets assigned to or created by an employee.
        
        Args:
            employee_id: Employee ID to search for
            status: Optional status filter
            max_results: Maximum number of results to return
            
        Returns:
            List of matching tickets
        """
        # Build JQL query
        jql_parts = [
            f'(assignee = "{employee_id}" OR reporter = "{employee_id}")'
        ]
        
        if status and status in self.WORKFLOW_STATES:
            status_id = self.WORKFLOW_STATES[status]
            jql_parts.append(f'status = "{status_id}"')
        
        jql = " AND ".join(jql_parts) + " ORDER BY updated DESC"
        
        search_data = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ["summary", "status", "priority", "assignee", "reporter", "created", "updated"]
        }
        
        try:
            response = self._make_request("POST", "/search", data=search_data)
            
            if self.dry_run:
                return [
                    {
                        "id": f"DRY-{i}",
                        "key": f"IT-DRY-{i:03d}",
                        "summary": f"Sample ticket {i}",
                        "status": "new",
                        "assignee": employee_id
                    }
                    for i in range(1, min(4, max_results + 1))
                ]
            
            tickets = []
            for issue in response.get("issues", []):
                fields = issue.get("fields", {})
                status_id = fields.get("status", {}).get("id")
                mapped_status = self.STATUS_MAPPING.get(status_id, "unknown")
                
                tickets.append({
                    "id": issue["id"],
                    "key": issue["key"],
                    "summary": fields.get("summary", ""),
                    "status": mapped_status,
                    "priority": fields.get("priority", {}).get("name", "Medium"),
                    "assignee": fields.get("assignee", {}).get("accountId"),
                    "reporter": fields.get("reporter", {}).get("accountId"),
                    "created": fields.get("created"),
                    "updated": fields.get("updated")
                })
            
            logger.info(f"Found {len(tickets)} tickets for employee {employee_id}")
            return tickets
            
        except Exception as e:
            logger.error(f"Failed to search tickets for employee {employee_id}: {e}")
            return []
    
    def _extract_description(self, description_obj: Dict) -> str:
        """Extract plain text from Jira description object."""
        if not description_obj or "content" not in description_obj:
            return ""
        
        text_parts = []
        
        def extract_text(content_list):
            for item in content_list:
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif "content" in item:
                    extract_text(item["content"])
        
        extract_text(description_obj["content"])
        return " ".join(text_parts)
    
    def get_workflow_states(self) -> Dict[str, str]:
        """Get available workflow states and their mappings."""
        return self.WORKFLOW_STATES.copy()
    
    def validate_credentials(self) -> bool:
        """
        Validate Jira credentials by making a test API call.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            if self.dry_run:
                return True
            
            # Try to get current user info
            response = self._make_request("GET", "/myself")
            return "accountId" in response
            
        except Exception as e:
            logger.error(f"Failed to validate Jira credentials: {e}")
            return False
    
    def get_project_info(self, project_key: str = "IT") -> Optional[Dict[str, Any]]:
        """
        Get project information.
        
        Args:
            project_key: Jira project key
            
        Returns:
            Project information or None if not found
        """
        try:
            response = self._make_request("GET", f"/project/{project_key}")
            
            if self.dry_run:
                return {
                    "key": project_key,
                    "name": "IT Support",
                    "projectTypeKey": "software"
                }
            
            return {
                "key": response["key"],
                "name": response["name"],
                "projectTypeKey": response["projectTypeKey"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get project info for {project_key}: {e}")
            return None
