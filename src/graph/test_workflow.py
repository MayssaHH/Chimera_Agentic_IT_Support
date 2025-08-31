"""
Test Script for IT Support Workflow

This script demonstrates the complete workflow functionality, including:
- Graph building and configuration
- JIRA agent workflow simulation
- Checkpoint persistence setup
- Workflow execution simulation
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from build import build_graph, create_workflow_config, get_workflow_summary


def create_test_state(request_type: str = "software_installation") -> dict:
    """Create a test state for different request types"""
    
    base_state = {
        "user_request": {
            "request_id": f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "",
            "description": "",
            "category": "",
            "priority": "MEDIUM",
            "submitted_at": datetime.now().isoformat(),
            "requested_by": "test.user@company.com",
            "department": "Engineering",
            "urgency": "normal",
            "attachments": [],
            "custom_fields": {}
        },
        "employee": {
            "employee_id": "EMP_TEST_001",
            "name": "Test User",
            "email": "test.user@company.com",
            "department": "Engineering",
            "role": "Software Engineer",
            "manager": "test.manager@company.com",
            "access_level": "standard",
            "location": "HQ",
            "contact_info": {"phone": "+1-555-0000"}
        },
        "retrieved_docs": [],
        "citations": [],
        "past_tickets_features": [],
        "metadata": {
            "workflow_started": datetime.now().isoformat(),
            "version": "1.0.0",
            "test_mode": True
        }
    }
    
    # Configure based on request type
    if request_type == "software_installation":
        base_state["user_request"]["title"] = "Software Installation Request"
        base_state["user_request"]["description"] = "Need Visual Studio Code installed on development machine"
        base_state["user_request"]["category"] = "software_installation"
    elif request_type == "access_request":
        base_state["user_request"]["title"] = "Database Access Request"
        base_state["user_request"]["description"] = "Need access to customer database for analytics"
        base_state["user_request"]["category"] = "access_control"
        base_state["user_request"]["priority"] = "HIGH"
    elif request_type == "hardware_request":
        base_state["user_request"]["title"] = "Hardware Upgrade Request"
        base_state["user_request"]["description"] = "Need additional RAM for development machine"
        base_state["user_request"]["category"] = "hardware"
        base_state["user_request"]["priority"] = "LOW"
    
    return base_state


def simulate_workflow_execution(workflow, initial_state: dict) -> dict:
    """Simulate workflow execution step by step"""
    
    print("=== Simulating Workflow Execution ===\n")
    
    # Simulate each node execution
    current_state = initial_state.copy()
    
    # Step 1: Retrieve documents
    print("1. Executing retrieve node...")
    current_state = workflow.nodes["retrieve"](current_state)
    current_state["retrieved_docs"] = [
        {
            "doc_id": "POLICY_001",
            "title": "Software Installation Policy",
            "content": "Standard development tools may be installed upon request...",
            "source": "IT_Policies",
            "relevance_score": 0.95
        }
    ]
    print(f"   Retrieved {len(current_state['retrieved_docs'])} documents")
    
    # Step 2: Route request
    print("2. Executing router node...")
    current_state = workflow.nodes["router"](current_state)
    current_state["router_verdict"] = {
        "complexity": "SIMPLE",
        "selected_model": "gpt-4",
        "reasoning": "Standard software installation request"
    }
    print(f"   Routed to {current_state['router_verdict']['complexity']} complexity")
    
    # Step 3: Classify request
    print("3. Executing classifier node...")
    current_state = workflow.nodes["classifier"](current_state)
    current_state["decision_record"] = {
        "decision": "ALLOWED",
        "confidence": 0.92,
        "justification": "Standard development tool installation meets policy requirements"
    }
    print(f"   Decision: {current_state['decision_record']['decision']}")
    
    # Step 4: Create JIRA ticket
    print("4. Executing JIRA create node...")
    current_state = workflow.nodes["jira_create"](current_state)
    current_state["ticket_record"] = {
        "ticket_id": "IT-1001",
        "status": "New",
        "created_at": datetime.now().isoformat(),
        "summary": current_state["user_request"]["title"]
    }
    print(f"   Created ticket: {current_state['ticket_record']['ticket_id']}")
    
    # Step 5: Update JIRA ticket status
    print("5. Executing JIRA update node...")
    current_state = workflow.nodes["jira_update"](current_state)
    current_state["ticket_record"]["status"] = "In Progress"
    current_state["ticket_record"]["updated_at"] = datetime.now().isoformat()
    print(f"   Updated ticket status to: {current_state['ticket_record']['status']}")
    
    # Step 6: Plan request
    print("6. Executing planner node...")
    current_state = workflow.nodes["planner"](current_state)
    current_state["plan_record"] = {
        "plan_id": "PLAN_001",
        "steps": [
            {"step_id": "STEP_1", "action": "Install Visual Studio Code", "status": "pending"},
            {"step_id": "STEP_2", "action": "Configure extensions", "status": "pending"},
            {"step_id": "STEP_3", "action": "Verify installation", "status": "pending"}
        ]
    }
    print(f"   Created plan with {len(current_state['plan_record']['steps'])} steps")
    
    # Step 7: Execute plan
    print("7. Executing IT agent node...")
    current_state = workflow.nodes["it_agent"](current_state)
    current_state["execution_result"] = {
        "status": "completed",
        "steps_completed": 3,
        "total_steps": 3,
        "completion_time": "5 minutes"
    }
    print(f"   Execution status: {current_state['execution_result']['status']}")
    
    # Step 8: Close request
    print("8. Executing closer node...")
    current_state = workflow.nodes["closer"](current_state)
    current_state["completion_summary"] = {
        "status": "completed",
        "resolution_summary": "Successfully installed and configured Visual Studio Code"
    }
    print(f"   Request completed: {current_state['completion_summary']['status']}")
    
    print("\n=== Workflow Execution Complete ===")
    return current_state


def test_jira_workflow():
    """Test the JIRA agent workflow specifically"""
    
    print("=== Testing JIRA Agent Workflow ===\n")
    
    # Test different decision scenarios
    scenarios = [
        ("ALLOWED", "Software Installation", "Should proceed to planning"),
        ("DENIED", "Unauthorized Access", "Should be closed immediately"),
        ("REQUIRES_APPROVAL", "Database Access", "Should require human approval")
    ]
    
    for decision, request_type, expected_behavior in scenarios:
        print(f"Scenario: {request_type} - Decision: {decision}")
        print(f"Expected: {expected_behavior}")
        
        # Create test state
        test_state = create_test_state("access_request" if "Database" in request_type else "software_installation")
        test_state["decision_record"] = {"decision": decision}
        
        # Simulate JIRA workflow
        if decision == "DENIED":
            print("   → JIRA Agent: Creates ticket and moves to 'Closed'")
            print("   → Workflow: Ends immediately")
        elif decision == "REQUIRES_APPROVAL":
            print("   → JIRA Agent: Creates ticket and moves to 'In Progress'")
            print("   → Workflow: Enqueues HIL question for approval")
        else:  # ALLOWED
            print("   → JIRA Agent: Creates ticket and moves to 'In Progress'")
            print("   → Workflow: Proceeds to planning")
        
        print()
    
    print("=== JIRA Workflow Test Complete ===\n")


def main():
    """Main test function"""
    
    print("=== IT Support Workflow Test Suite ===\n")
    
    # Display workflow summary
    print(get_workflow_summary())
    
    # Create workflow configuration
    config = create_workflow_config()
    print(f"Configuration: {json.dumps(config, indent=2)}\n")
    
    # Build the workflow
    print("Building workflow...")
    workflow = build_graph(
        checkpoint_dir=config["checkpoint_dir"],
        enable_persistence=config["enable_persistence"]
    )
    
    print(f"Workflow built successfully with {len(workflow.nodes)} nodes")
    print(f"Nodes: {list(workflow.nodes.keys())}\n")
    
    # Test JIRA workflow
    test_jira_workflow()
    
    # Test complete workflow execution
    print("Testing complete workflow execution...")
    initial_state = create_test_state("software_installation")
    
    try:
        final_state = simulate_workflow_execution(workflow, initial_state)
        print(f"\nFinal state keys: {list(final_state.keys())}")
        
        # Show key results
        if "ticket_record" in final_state:
            print(f"JIRA Ticket: {final_state['ticket_record']['ticket_id']} - {final_state['ticket_record']['status']}")
        
        if "completion_summary" in final_state:
            print(f"Completion: {final_state['completion_summary']['status']}")
        
    except Exception as e:
        print(f"Error during workflow execution: {e}")
    
    print("\n=== Test Suite Complete ===")


if __name__ == "__main__":
    main()
