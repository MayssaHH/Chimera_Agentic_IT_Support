"""
Example usage of structured LLM calls with JSON schema validation.

This file demonstrates how to use the new LLM registry features:
- JSON schema validation
- Function calling
- Automatic retries
- Role-specific configurations
"""

import asyncio
from typing import Dict, Any

from .llm_registry import (
    get_structured_llm_client,
    call_llm_with_json_schema,
    call_llm_with_function_calling
)
from .response_schemas import (
    ClassifierResponse,
    RouterResponse,
    PlannerResponse,
    ITAgentResponse
)


async def example_classifier_call():
    """Example of calling the classifier with JSON schema validation."""
    print("=== Classifier Example ===")
    
    # Sample input data
    input_data = {
        "user_request": {
            "title": "Request for Admin Access to Database",
            "description": "Need admin access to customer database for data analysis",
            "request_type": "software_access",
            "priority": "high"
        },
        "retrieved_docs": [
            {
                "title": "IT_Access_Policy_v2.1",
                "content": "Administrative access requires written approval from department head.",
                "source": "policy_docs",
                "relevance_score": 0.95
            }
        ],
        "past_tickets_features": [
            {
                "category": "software_access",
                "resolution": "approved_with_conditions"
            }
        ]
    }
    
    try:
        # Call classifier with JSON schema validation
        response = await call_llm_with_json_schema(
            role="classifier",
            prompt="Analyze this IT support request and classify it according to company policies.",
            input_data=input_data,
            response_schema=ClassifierResponse
        )
        
        print(f"✅ Classification successful!")
        print(f"Decision: {response.decision}")
        print(f"Confidence: {response.confidence}")
        print(f"Citations: {len(response.citations)}")
        print(f"Needs Human: {response.needs_human}")
        print(f"Justification: {response.justification_brief}")
        
        return response
        
    except Exception as e:
        print(f"❌ Classifier call failed: {e}")
        return None


async def example_router_call():
    """Example of calling the router with JSON schema validation."""
    print("\n=== Router Example ===")
    
    input_data = {
        "request_details": {
            "complexity": "MODERATE",
            "policy_requirements": "STANDARD"
        },
        "available_models": ["llama3.1:8b", "mistral:7b", "mixtral:8x7b"],
        "retrieval_results": {
            "quality": "HIGH",
            "consistency": "GOOD"
        }
    }
    
    try:
        response = await call_llm_with_json_schema(
            role="router",
            prompt="Select the most appropriate model for this request.",
            input_data=input_data,
            response_schema=RouterResponse
        )
        
        print(f"✅ Routing successful!")
        print(f"Target Model: {response.target_model}")
        print(f"Reason: {response.reason}")
        print(f"Escalation Needed: {response.escalation_needed}")
        print(f"Expected Accuracy: {response.quality_metrics.expected_accuracy}")
        
        return response
        
    except Exception as e:
        print(f"❌ Router call failed: {e}")
        return None


async def example_planner_call():
    """Example of calling the planner with JSON schema validation."""
    print("\n=== Planner Example ===")
    
    input_data = {
        "user_request": {
            "title": "Database Access Request",
            "description": "Need admin access to customer database"
        },
        "decision_record": {
            "decision": "REQUIRES_APPROVAL",
            "citations": ["policy_ref_1", "policy_ref_2"]
        },
        "retrieved_docs": [
            {
                "title": "Access_Control_Policy",
                "content": "Admin access requires approval workflow"
            }
        ],
        "employee": {
            "department": "Data Science",
            "role": "Senior Analyst"
        }
    }
    
    try:
        response = await call_llm_with_json_schema(
            role="planner",
            prompt="Create an execution plan for this IT support request.",
            input_data=input_data,
            response_schema=PlannerResponse
        )
        
        print(f"✅ Planning successful!")
        print(f"Plan ID: {response.plan_id}")
        print(f"Priority: {response.priority}")
        print(f"Steps: {len(response.steps)}")
        print(f"Approval Needed: {response.approval_workflow.needed}")
        print(f"Estimated Duration: {response.estimated_duration}")
        
        return response
        
    except Exception as e:
        print(f"❌ Planner call failed: {e}")
        return None


async def example_it_agent_call():
    """Example of calling the IT agent with JSON schema validation."""
    print("\n=== IT Agent Example ===")
    
    input_data = {
        "plan_record": {
            "plan_id": "PLAN_001",
            "steps": [
                {
                    "step_id": "step_1",
                    "description": "Send approval email to manager"
                }
            ]
        },
        "available_tools": ["email", "jira", "directory"],
        "current_context": {
            "ticket_status": "pending_approval",
            "user_info": "Data Science Team"
        }
    }
    
    try:
        response = await call_llm_with_json_schema(
            role="it",
            prompt="Convert this plan into executable actions.",
            input_data=input_data,
            response_schema=ITAgentResponse
        )
        
        print(f"✅ IT Agent call successful!")
        print(f"Execution ID: {response.execution_id}")
        print(f"Status: {response.status}")
        print(f"Actions: {len(response.executable_actions)}")
        print(f"User Guide Steps: {len(response.user_guide.steps)}")
        
        return response
        
    except Exception as e:
        print(f"❌ IT Agent call failed: {e}")
        return None


async def example_direct_client_usage():
    """Example of using the structured client directly."""
    print("\n=== Direct Client Usage Example ===")
    
    try:
        # Get structured client for classifier
        classifier_client = get_structured_llm_client("classifier")
        
        # Sample data
        input_data = {
            "request": "Simple software installation request",
            "policies": ["Standard software policy"]
        }
        
        # Call with custom schema
        from pydantic import BaseModel
        
        class SimpleResponse(BaseModel):
            decision: str
            reason: str
        
        response = await classifier_client.call_with_json_schema(
            prompt="Make a simple decision about this request.",
            input_data=input_data,
            response_schema=SimpleResponse
        )
        
        print(f"✅ Direct client call successful!")
        print(f"Decision: {response.decision}")
        print(f"Reason: {response.reason}")
        
        return response
        
    except Exception as e:
        print(f"❌ Direct client call failed: {e}")
        return None


async def main():
    """Run all examples."""
    print("Structured LLM Calls Examples")
    print("=" * 50)
    
    # Run examples
    results = {}
    
    results["classifier"] = await example_classifier_call()
    results["router"] = await example_router_call()
    results["planner"] = await example_planner_call()
    results["it_agent"] = await example_it_agent_call()
    results["direct_client"] = await example_direct_client_usage()
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    successful = sum(1 for r in results.values() if r is not None)
    total = len(results)
    print(f"Successful calls: {successful}/{total}")
    
    if successful == total:
        print("🎉 All examples completed successfully!")
    else:
        print(f"⚠️  {total - successful} examples failed. Check the logs above.")


if __name__ == "__main__":
    asyncio.run(main())
