"""
Example Usage of IT Support Workflow

This file demonstrates how to use the build_graph function to create and run
the IT support workflow with checkpoint persistence.
"""

import asyncio
from typing import Dict, Any
from pathlib import Path

from .build import build_graph, create_workflow_config, get_workflow_summary
from .state import ITGraphState


def create_sample_state() -> ITGraphState:
    """Create a sample initial state for testing the workflow"""
    return {
        "user_request": {
            "request_id": "REQ_001",
            "title": "Software Installation Request",
            "description": "Need Visual Studio Code installed on my development machine for Python development",
            "category": "software_installation",
            "priority": "MEDIUM",
            "submitted_at": "2024-01-15T10:00:00Z",
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
            "manager": "jane.smith@company.com",
            "access_level": "standard",
            "location": "HQ",
            "contact_info": {"phone": "+1-555-0123"}
        },
        "retrieved_docs": [],
        "citations": [],
        "past_tickets_features": [],
        "metadata": {
            "workflow_started": "2024-01-15T10:00:00Z",
            "version": "1.0.0"
        }
    }


async def run_workflow_example():
    """Run a complete example of the IT support workflow"""
    
    print("=== IT Support Workflow Example ===\n")
    
    # Print workflow summary
    print(get_workflow_summary())
    
    # Create workflow configuration
    config = create_workflow_config()
    print(f"Workflow Configuration: {config}\n")
    
    # Build the workflow graph
    print("Building workflow graph...")
    workflow = build_graph(
        checkpoint_dir=config["checkpoint_dir"],
        enable_persistence=config["enable_persistence"]
    )
    
    # Create sample initial state
    initial_state = create_sample_state()
    print(f"Initial State Keys: {list(initial_state.keys())}\n")
    
    # Compile the workflow
    print("Compiling workflow...")
    compiled_workflow = workflow.compile()
    
    print("Workflow compiled successfully!")
    print(f"Available nodes: {list(compiled_workflow.nodes.keys())}")
    
    # Note: In a real scenario, you would run the workflow like this:
    # result = await compiled_workflow.ainvoke(initial_state)
    # print(f"Workflow completed with result: {result}")
    
    print("\n=== Example Complete ===")
    print("Note: This is a demonstration. To actually run the workflow,")
    print("uncomment the workflow execution code and ensure all dependencies are configured.")


def demonstrate_checkpoint_persistence():
    """Demonstrate checkpoint persistence functionality"""
    
    print("\n=== Checkpoint Persistence Demo ===\n")
    
    # Create workflow with persistence
    workflow = build_graph(
        checkpoint_dir="./storage/checkpoints",
        enable_persistence=True
    )
    
    # Show checkpoint configuration
    print("Checkpoint Configuration:")
    print(f"- Directory: {workflow.checkpointer.dir_path}")
    print(f"- Thread ID: {workflow.checkpointer.thread_id}")
    print(f"- Persistence enabled: {workflow.checkpointer is not None}")
    
    # List existing checkpoints (if any)
    checkpoint_dir = Path("./storage/checkpoints")
    if checkpoint_dir.exists():
        checkpoints = list(checkpoint_dir.glob("*.json"))
        print(f"\nExisting checkpoints: {len(checkpoints)}")
        for checkpoint in checkpoints[:5]:  # Show first 5
            print(f"  - {checkpoint.name}")
    else:
        print("\nNo checkpoints directory found.")
    
    print("\n=== Checkpoint Demo Complete ===")


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_workflow_example())
    
    # Demonstrate checkpoint persistence
    demonstrate_checkpoint_persistence()
