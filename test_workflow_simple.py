#!/usr/bin/env python3
"""
Simple Test Script for IT Support Workflow

This script demonstrates the complete workflow with logging:
1. Employee submits request
2. Request goes to JIRA agent to create ticket
3. Classifier makes decision
4. JIRA agent updates ticket status based on decision
5. If not denied, planner creates execution plan
6. IT agent executes the plan
7. JIRA agent moves ticket to done
"""

import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_request():
    """Create a test employee request"""
    return {
        "user_request": {
            "request_id": f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "Software Installation Request",
            "description": "Need Visual Studio Code installed on my development machine for Python development",
            "category": "software_installation",
            "priority": "MEDIUM",
            "submitted_at": datetime.now().isoformat(),
            "requested_by": "john.doe@company.com",
            "department": "Engineering",
            "urgency": "normal",
            "attachments": [],
            "custom_fields": {}
        },
        "employee": {
            "employee_id": "EMP_001",
            "name": "John Doe",
            "email": "john.doe@company.com",
            "department": "Engineering",
            "role": "Software Engineer",
            "manager": "jane.manager@company.com",
            "access_level": "standard",
            "location": "HQ",
            "contact_info": {"phone": "+1-555-0123"}
        },
        "retrieved_docs": [
            {
                "doc_id": "POLICY_001",
                "title": "Software Installation Policy",
                "content": "Standard development tools may be installed upon request. Visual Studio Code is an approved development tool. Installation requires IT approval for non-standard tools.",
                "source": "IT_Policies",
                "relevance_score": 0.95,
                "retrieval_date": datetime.now(),
                "document_type": "policy",
                "version": "2.1",
                "last_updated": datetime.now(),
                "metadata": {"category": "software"}
            }
        ],
        "citations": [],
        "past_tickets_features": [],
        "metadata": {
            "workflow_started": datetime.now().isoformat(),
            "version": "1.0.0",
            "test_mode": True
        }
    }

def run_workflow_step_by_step():
    """Run the workflow step by step with logging"""
    print("🚀 STARTING IT SUPPORT WORKFLOW TEST")
    print("="*80)
    
    # Create initial state
    state = create_test_request()
    print(f"📝 Created test request: {state['user_request']['title']}")
    print(f"👤 Employee: {state['employee']['name']} ({state['employee']['email']})")
    print(f"📚 Retrieved documents: {len(state['retrieved_docs'])}")
    print()
    
    try:
        # Step 1: Retrieve documents (already done in test data)
        print("📚 STEP 1: Document retrieval (simulated)")
        print("   - Documents already retrieved for testing")
        print()
        
        # Step 2: Router evaluation
        print("🔄 STEP 2: Router evaluation")
        from graph.nodes.router import router_node
        state = router_node(state)
        print(f"   - Router verdict: {state.get('router_verdict', {}).get('target_model', 'UNKNOWN')}")
        print()
        
        # Step 3: Classification
        print("🎯 STEP 3: Request classification")
        from graph.nodes.classifier import classifier_node
        state = classifier_node(state)
        decision = state.get('decision_record', {}).get('decision', 'UNKNOWN')
        print(f"   - Classification decision: {decision}")
        print()
        
        # Step 4: JIRA ticket creation
        print("🔧 STEP 4: JIRA ticket creation")
        from graph.nodes.jira_agent import jira_agent_node
        state = jira_agent_node(state)
        ticket_id = state.get('ticket_record', {}).get('ticket_id', 'UNKNOWN')
        print(f"   - JIRA ticket created: {ticket_id}")
        print()
        
        # Step 5: Conditional routing based on decision
        if decision == 'DENIED':
            print("❌ REQUEST DENIED - Workflow ends")
            print("   - JIRA ticket moved to Closed")
            return state
        elif decision == 'REQUIRES_APPROVAL':
            print("⏳ APPROVAL REQUIRED - HIL processing")
            from graph.nodes.hil import hil_node
            state = hil_node(state)
            print("   - Workflow paused for human approval")
            return state
        else:  # ALLOWED
            print("✅ REQUEST APPROVED - Continuing to planning")
            
            # Step 6: Planning
            print("📋 STEP 6: Execution planning")
            from graph.nodes.planner import planner_node
            state = planner_node(state)
            plan_id = state.get('plan_record', {}).get('plan_id', 'UNKNOWN')
            print(f"   - Plan created: {plan_id}")
            print()
            
            # Step 7: IT Agent execution
            print("🛠️ STEP 7: Plan execution")
            from graph.nodes.it_agent import it_agent_node
            state = it_agent_node(state)
            outcome = state.get('it_outcome', 'UNKNOWN')
            print(f"   - Execution outcome: {outcome}")
            print()
            
            # Step 8: Final JIRA update
            print("🔧 STEP 8: Final JIRA status update")
            state = jira_agent_node(state)  # Update ticket to done
            print("   - JIRA ticket moved to Done")
            print()
            
            # Step 9: Close request
            print("✅ STEP 9: Request closure")
            from graph.nodes.closer import close_request
            result = close_request(state)
            print(f"   - Request closed: {result['status']}")
            print()
    
    except Exception as e:
        print(f"❌ ERROR during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        return state
    
    print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*80)
    return state

def main():
    """Main function"""
    print("IT Support Workflow Test")
    print("This will simulate a complete employee request workflow")
    print()
    
    # Run the workflow
    final_state = run_workflow_step_by_step()
    
    # Print final summary
    print("\n📊 FINAL WORKFLOW SUMMARY")
    print("="*40)
    print(f"Request ID: {final_state.get('user_request', {}).get('request_id', 'UNKNOWN')}")
    print(f"JIRA Ticket: {final_state.get('ticket_record', {}).get('ticket_id', 'UNKNOWN')}")
    print(f"Final Decision: {final_state.get('decision_record', {}).get('decision', 'UNKNOWN')}")
    print(f"Plan Created: {'plan_record' in final_state}")
    print(f"IT Execution: {final_state.get('it_outcome', 'UNKNOWN')}")
    print(f"Errors: {len(final_state.get('errors', []))}")
    
    if 'errors' in final_state and final_state['errors']:
        print("\n⚠️ ERRORS ENCOUNTERED:")
        for error in final_state['errors']:
            print(f"  - {error['error_type']}: {error['message']}")

if __name__ == "__main__":
    main()
