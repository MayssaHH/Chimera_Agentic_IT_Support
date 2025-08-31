"""
Closer Node for IT Support Workflow

This node handles ticket closing based on IT agent execution outcomes:
- If outcome is 'executed' or confirmed by employee: Jira → resolved then closed
- If awaiting employee/manager: leave in_progress
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..state import ITGraphState, RequestStatus
# Mock Jira client for testing without full configuration
class MockJiraClient:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
    
    def update_ticket(self, **kwargs):
        return {"success": True, "message": "Mock ticket updated", "dry_run": self.dry_run}

# Use mock client for now - can be replaced with real client when configuration is available
JiraClient = MockJiraClient


logger = logging.getLogger(__name__)


class TicketCloser:
    """Handles ticket closing logic based on execution outcomes"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.jira_client = JiraClient(dry_run=dry_run)
        
    def determine_ticket_action(self, state: ITGraphState) -> Dict[str, Any]:
        """Determine what action to take on the ticket based on IT agent outcome"""
        try:
            # Get IT agent outcome
            it_outcome = state.get("it_outcome")
            if not it_outcome:
                logger.warning("No IT agent outcome found in state")
                return {
                    "action": "no_action",
                    "reason": "No IT agent outcome available",
                    "ticket_status": state.get("ticket_record", {}).get("status", "unknown")
                }
            
            # Get current ticket status
            ticket_record = state.get("ticket_record", {})
            current_status = ticket_record.get("status", "unknown")
            
            # Determine action based on outcome
            if it_outcome == "executed":
                return self._handle_executed_outcome(state, current_status)
            elif it_outcome == "awaiting_employee":
                return self._handle_awaiting_employee_outcome(state, current_status)
            elif it_outcome == "awaiting_manager":
                return self._handle_awaiting_manager_outcome(state, current_status)
            else:
                logger.warning(f"Unknown IT agent outcome: {it_outcome}")
                return {
                    "action": "no_action",
                    "reason": f"Unknown outcome: {it_outcome}",
                    "ticket_status": current_status
                }
                
        except Exception as e:
            logger.error(f"Error determining ticket action: {e}")
            return {
                "action": "error",
                "reason": f"Error: {str(e)}",
                "ticket_status": "error"
            }
    
    def _handle_executed_outcome(self, state: ITGraphState, current_status: str) -> Dict[str, Any]:
        """Handle case where all steps were executed automatically"""
        ticket_record = state.get("ticket_record", {})
        ticket_id = ticket_record.get("ticket_id")
        
        if not ticket_id:
            return {
                "action": "no_action",
                "reason": "No ticket ID available",
                "ticket_status": current_status
            }
        
        # Check if ticket is already resolved
        if current_status == RequestStatus.RESOLVED:
            return {
                "action": "no_action",
                "reason": f"Ticket already {current_status}",
                "ticket_status": current_status
            }
        
        # Resolve and close the ticket
        resolution_comment = self._generate_resolution_comment(state)
        
        try:
            # First resolve the ticket
            resolve_result = self.jira_client.update_ticket(
                ticket_id=ticket_id,
                fields={"status": RequestStatus.RESOLVED},
                comment=f"Resolved: {resolution_comment}"
            )
            
            if not resolve_result.get("success", False):
                logger.error(f"Failed to resolve ticket {ticket_id}: {resolve_result}")
                return {
                    "action": "error",
                    "reason": f"Failed to resolve ticket: {resolve_result.get('error', 'Unknown error')}",
                    "ticket_status": current_status
                }
            
            # Then close the ticket
            close_result = self.jira_client.update_ticket(
                ticket_id=ticket_id,
                fields={"status": RequestStatus.CLOSED},
                comment="Ticket closed: All automated steps completed successfully"
            )
            
            if not close_result.get("success", False):
                logger.error(f"Failed to close ticket {ticket_id}: {close_result}")
                return {
                    "action": "resolved_only",
                    "reason": f"Resolved but failed to close: {close_result.get('error', 'Unknown error')}",
                    "ticket_status": RequestStatus.RESOLVED
                }
            
            return {
                "action": "closed",
                "reason": "All automated steps completed successfully",
                "ticket_status": RequestStatus.CLOSED,
                "resolution_comment": resolution_comment,
                "jira_results": {
                    "resolve": resolve_result,
                    "close": close_result
                }
            }
            
        except Exception as e:
            logger.error(f"Error closing ticket {ticket_id}: {e}")
            return {
                "action": "error",
                "reason": f"Error during ticket closure: {str(e)}",
                "ticket_status": current_status
            }
    
    def _handle_awaiting_employee_outcome(self, state: ITGraphState, current_status: str) -> Dict[str, Any]:
        """Handle case where employee action is required"""
        # Keep ticket in progress
        if current_status != RequestStatus.IN_PROGRESS:
            # Update ticket status to in_progress if not already
            ticket_record = state.get("ticket_record", {})
            ticket_id = ticket_record.get("ticket_id")
            
            if ticket_id:
                try:
                    update_result = self.jira_client.update_ticket(
                        ticket_id=ticket_id,
                        fields={"status": RequestStatus.IN_PROGRESS},
                        comment="Status updated: Awaiting employee action"
                    )
                    
                    if update_result.get("success", False):
                        return {
                            "action": "status_updated",
                            "reason": "Updated to in_progress - awaiting employee action",
                            "ticket_status": RequestStatus.IN_PROGRESS,
                            "jira_result": update_result
                        }
                    else:
                        logger.warning(f"Failed to update ticket status: {update_result}")
                        
                except Exception as e:
                    logger.error(f"Error updating ticket status: {e}")
        
        return {
            "action": "maintain_status",
            "reason": "Awaiting employee action - keeping in progress",
            "ticket_status": RequestStatus.IN_PROGRESS
        }
    
    def _handle_awaiting_manager_outcome(self, state: ITGraphState, current_status: str) -> Dict[str, Any]:
        """Handle case where manager approval is required"""
        # Keep ticket in progress
        if current_status != RequestStatus.IN_PROGRESS:
            # Update ticket status to in_progress if not already
            ticket_record = state.get("ticket_record", {})
            ticket_id = ticket_record.get("ticket_id")
            
            if ticket_id:
                try:
                    update_result = self.jira_client.update_ticket(
                        ticket_id=ticket_id,
                        fields={"status": RequestStatus.IN_PROGRESS},
                        comment="Status updated: Awaiting manager approval"
                    )
                    
                    if update_result.get("success", False):
                        return {
                            "action": "status_updated",
                            "reason": "Updated to in_progress - awaiting manager approval",
                            "ticket_status": RequestStatus.IN_PROGRESS,
                            "jira_result": update_result
                        }
                    else:
                        logger.warning(f"Failed to update ticket status: {update_result}")
                        
                except Exception as e:
                    logger.error(f"Error updating ticket status: {e}")
        
        return {
            "action": "maintain_status",
            "reason": "Awaiting manager approval - keeping in progress",
            "ticket_status": RequestStatus.IN_PROGRESS
        }
    
    def _generate_resolution_comment(self, state: ITGraphState) -> str:
        """Generate a resolution comment based on the execution results"""
        execution_results = state.get("execution_results", [])
        user_request = state.get("user_request", {})
        request_title = user_request.get("title", "IT support request")
        
        if not execution_results:
            return f"Request '{request_title}' completed successfully"
        
        successful_actions = [r for r in execution_results if r.get("success", False)]
        action_count = len(successful_actions)
        
        if action_count == 0:
            return f"Request '{request_title}' completed (no automated actions required)"
        elif action_count == 1:
            return f"Request '{request_title}' completed successfully with 1 automated action"
        else:
            return f"Request '{request_title}' completed successfully with {action_count} automated actions"
    
    def close_ticket(self, state: ITGraphState) -> ITGraphState:
        """Execute the ticket closing action and update state"""
        try:
            # Determine what action to take
            action_result = self.determine_ticket_action(state)
            
            # Add closing result to state
            if "closing_results" not in state:
                state["closing_results"] = []
            state["closing_results"].append({
                "timestamp": datetime.now().isoformat(),
                "action": action_result["action"],
                "reason": action_result["reason"],
                "ticket_status": action_result["ticket_status"],
                "details": action_result
            })
            
            # Update ticket record status if changed
            if "ticket_record" in state and action_result["ticket_status"] != "error":
                state["ticket_record"]["status"] = action_result["ticket_status"]
                state["ticket_record"]["updated_at"] = datetime.now()
                
                # Add resolution details if ticket was closed
                if action_result["action"] == "closed":
                    state["ticket_record"]["resolution"] = action_result["reason"]
                    state["ticket_record"]["resolution_date"] = datetime.now()
            
            # Add closing metadata
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["ticket_closing"] = {
                "action": action_result["action"],
                "timestamp": datetime.now().isoformat(),
                "final_status": action_result["ticket_status"],
                "closing_reason": action_result["reason"]
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error in ticket closing: {e}")
            
            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "error_id": f"closer_error_{datetime.now().timestamp()}",
                "timestamp": datetime.now(),
                "error_type": "ticket_closing_error",
                "message": str(e),
                "severity": "high",
                "resolved": False
            })
            
            return state


def closer_node(state: ITGraphState) -> ITGraphState:
    """
    Closer node: handles ticket closing based on IT agent outcome
    
    Args:
        state: Current workflow state with IT agent outcome
        
    Returns:
        Updated state with closing results and final ticket status
    """
    try:
        # Initialize ticket closer
        closer = TicketCloser(dry_run=False)  # Set to True for testing
        
        # Execute ticket closing
        updated_state = closer.close_ticket(state)
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in closer node: {e}")
        
        # Add error to state
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append({
            "error_id": f"closer_node_error_{datetime.now().timestamp()}",
            "timestamp": datetime.now(),
            "error_type": "closer_node_error",
            "message": str(e),
            "severity": "high",
            "resolved": False
        })
        
        return state


# Convenience functions for testing and direct usage
def test_closer_node():
    """Test function for the closer node"""
    
    # Test 1: Executed outcome
    print("=== Testing EXECUTED outcome ===")
    executed_state = {
        "it_outcome": "executed",
        "ticket_record": {
            "ticket_id": "IT-1001",
            "status": "in_progress"
        },
        "user_request": {
            "title": "Software Installation Request"
        },
        "execution_results": [
            {"success": True, "action_id": "step_1"},
            {"success": True, "action_id": "step_2"}
        ]
    }
    
    result = closer_node(executed_state)
    print(f"Action: {result.get('closing_results', [{}])[-1].get('action')}")
    print(f"Final Status: {result.get('ticket_record', {}).get('status')}")
    
    # Test 2: Awaiting employee outcome
    print("\n=== Testing AWAITING_EMPLOYEE outcome ===")
    awaiting_employee_state = {
        "it_outcome": "awaiting_employee",
        "ticket_record": {
            "ticket_id": "IT-1002",
            "status": "waiting_for_user"
        },
        "user_request": {
            "title": "Access Request"
        }
    }
    
    result = closer_node(awaiting_employee_state)
    print(f"Action: {result.get('closing_results', [{}])[-1].get('action')}")
    print(f"Final Status: {result.get('ticket_record', {}).get('status')}")
    
    # Test 3: Awaiting manager outcome
    print("\n=== Testing AWAITING_MANAGER outcome ===")
    awaiting_manager_state = {
        "it_outcome": "awaiting_manager",
        "ticket_record": {
            "ticket_id": "IT-1003",
            "status": "waiting_for_approval"
        },
        "user_request": {
            "title": "Admin Access Request"
        }
    }
    
    result = closer_node(awaiting_manager_state)
    print(f"Action: {result.get('closing_results', [{}])[-1].get('action')}")
    print(f"Final Status: {result.get('ticket_record', {}).get('status')}")
    
    return result


if __name__ == "__main__":
    # Run test if executed directly
    test_closer_node()
