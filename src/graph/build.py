"""
Graph Builder for IT Support Workflow

This module builds the LangGraph workflow by wiring nodes with edges and implementing
persistence for checkpoints. The workflow follows the pattern:
retrieve → router → classifier → (jira) → (hil?) → planner → it_agent → closer

JIRA Agent manages ticket status throughout the workflow:
- Creates ticket when request is received
- Moves to "In Progress" when classifier allows/requires approval
- Moves to "Closed" when denied
- Updates status based on IT Agent completion
- Closes ticket when request is fully resolved
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Try to import LangGraph components, with fallback for missing dependencies
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint import LocalCheckpointSaver
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LangGraph not properly installed: {e}")
    print("Please install LangGraph with: pip install langgraph")
    LANGGRAPH_AVAILABLE = False
    # Create mock classes for development
    class StateGraph:
        def __init__(self, state_type):
            self.state_type = state_type
            self.nodes = {}
            self.checkpointer = None
            
        def add_node(self, name, func):
            self.nodes[name] = func
            
        def add_edge(self, from_node, to_node):
            pass
            
        def add_conditional_edges(self, from_node, condition_func, edge_map):
            pass
            
        def set_entry_point(self, node_name):
            pass
            
        def set_checkpointer(self, checkpointer):
            self.checkpointer = checkpointer
            
        def compile(self):
            return self
    
    class END:
        pass
    
    class LocalCheckpointSaver:
        def __init__(self, dir_path, thread_id):
            self.dir_path = dir_path
            self.thread_id = thread_id

# Try to import state and nodes with fallback
try:
    from graph.state import ITGraphState
    from graph.nodes.retrieve import retrieve_node
    from graph.nodes.router import router_node
    from graph.nodes.classifier import classifier_node
    from graph.nodes.jira_agent import jira_agent_node
    from graph.nodes.hil import hil_node
    from graph.nodes.planner import planner_node
    from graph.nodes.it_agent import it_agent_node
    from graph.nodes.closer import close_request
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some node imports failed: {e}")
    print("This is expected when running build.py directly")
    IMPORTS_AVAILABLE = False
    # Create mock functions for development
    def retrieve_node(state): return state
    def router_node(state): return state
    def classifier_node(state): return state
    def jira_agent_node(state): return state
    def hil_node(state): return state
    def planner_node(state): return state
    def it_agent_node(state): return state
    def close_request(state): return state
    # Mock state type
    class ITGraphState:
        pass


def create_ticket(state: ITGraphState) -> ITGraphState:
    """
    Wrapper function to create JIRA ticket when request is received
    This is called after classifier determines the request should proceed
    """
    # Add metadata to indicate this is the ticket creation stage
    if 'metadata' not in state:
        state['metadata'] = {}
    state['metadata']['jira_stage'] = 'ticket_creation'
    
    # Call the main JIRA agent node
    return jira_agent_node(state)


def update_ticket_status(state: ITGraphState) -> ITGraphState:
    """
    Wrapper function to update JIRA ticket status based on workflow stage
    This handles status transitions throughout the workflow
    """
    # Add metadata to indicate this is the status update stage
    if 'metadata' not in state:
        state['metadata'] = {}
    state['metadata']['jira_stage'] = 'status_update'
    
    # Call the main JIRA agent node
    return jira_agent_node(state)


def enqueue_hil_question(state: ITGraphState) -> ITGraphState:
    """
    Wrapper function to enqueue human-in-the-loop questions
    """
    # Add metadata to indicate this is the HIL enqueue stage
    if 'metadata' not in state:
        state['metadata'] = {}
    state['metadata']['hil_stage'] = 'enqueue'
    
    # Call the main HIL node
    return hil_node(state)


def process_hil_response(state: ITGraphState) -> ITGraphState:
    """
    Wrapper function to process human-in-the-loop responses
    """
    # Add metadata to indicate this is the HIL processing stage
    if 'metadata' not in state:
        state['metadata'] = {}
    state['metadata']['hil_stage'] = 'process_response'
    
    # Call the main HIL node
    return hil_node(state)


def plan_request(state: ITGraphState) -> ITGraphState:
    """
    Wrapper function to plan the IT support request
    """
    # Add metadata to indicate this is the planning stage
    if 'metadata' not in state:
        state['metadata'] = {}
    state['metadata']['workflow_stage'] = 'planning'
    
    # Call the main planner node
    return planner_node(state)


def execute_plan(state: ITGraphState) -> ITGraphState:
    """
    Wrapper function to execute the IT support plan
    """
    # Add metadata to indicate this is the execution stage
    if 'metadata' not in state:
        state['metadata'] = {}
    state['metadata']['workflow_stage'] = 'execution'
    
    # Call the main IT agent node
    return it_agent_node(state)


def build_graph(
    checkpoint_dir: str = "./storage/checkpoints",
    enable_persistence: bool = True
) -> StateGraph:
    """
    Build the IT Support Workflow Graph
    
    Args:
        checkpoint_dir: Directory for storing checkpoints
        enable_persistence: Whether to enable checkpoint persistence
    
    Returns:
        StateGraph: The configured workflow graph
    """
    
    if not LANGGRAPH_AVAILABLE:
        print("Warning: Building graph without LangGraph - this is for development only")
        print("Please install LangGraph for production use")
    
    if not IMPORTS_AVAILABLE:
        print("Warning: Some node imports failed - using mock functions")
        print("This is expected when running build.py directly")
    
    # Create checkpoint directory if it doesn't exist
    if enable_persistence:
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Initialize the graph
    workflow = StateGraph(ITGraphState)
    
    # Add nodes to the graph
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("router", router_node)
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("jira_create", create_ticket)
    workflow.add_node("jira_update", update_ticket_status)
    workflow.add_node("hil_enqueue", enqueue_hil_question)
    workflow.add_node("hil_process", process_hil_response)
    workflow.add_node("planner", plan_request)
    workflow.add_node("it_agent", execute_plan)
    workflow.add_node("closer", close_request)
    
    # Define the main workflow edges
    # Start with retrieve
    workflow.set_entry_point("retrieve")
    
    # retrieve → router
    workflow.add_edge("retrieve", "router")
    
    # router → classifier
    workflow.add_edge("router", "classifier")
    
    # classifier → conditional routing based on decision
    workflow.add_conditional_edges(
        "classifier",
        _route_after_classification,
        {
            "jira_create": "jira_create",
            "hil_enqueue": "hil_enqueue",
            "end": END
        }
    )
    
    # jira_create → jira_update (for status transitions)
    workflow.add_edge("jira_create", "jira_update")
    
    # jira_update → conditional routing
    workflow.add_conditional_edges(
        "jira_update",
        _route_after_jira_update,
        {
            "planner": "planner",
            "hil_enqueue": "hil_enqueue",
            "end": END
        }
    )
    
    # hil_enqueue → wait for human response (end current execution)
    workflow.add_edge("hil_enqueue", END)
    
    # hil_process → conditional routing
    workflow.add_conditional_edges(
        "hil_process",
        _route_after_hil,
        {
            "jira_update": "jira_update",
            "planner": "planner",
            "end": END
        }
    )
    
    # planner → it_agent
    workflow.add_edge("planner", "it_agent")
    
    # it_agent → conditional routing
    workflow.add_conditional_edges(
        "it_agent",
        _route_after_it_agent,
        {
            "jira_update": "jira_update",
            "closer": "closer",
            "end": END
        }
    )
    
    # closer → end
    workflow.add_edge("closer", END)
    
    # Configure persistence if enabled and LangGraph is available
    if enable_persistence and LANGGRAPH_AVAILABLE:
        checkpoint_saver = LocalCheckpointSaver(
            dir_path=checkpoint_dir,
            thread_id="it_support_workflow"
        )
        workflow.set_checkpointer(checkpoint_saver)
    elif enable_persistence:
        print("Warning: Checkpoint persistence disabled - LangGraph not available")
    
    return workflow


def _route_after_classification(state: ITGraphState) -> str:
    """
    Route after classification based on decision type
    
    Returns:
        str: Next node to execute
    """
    decision_record = state.get('decision_record', {})
    decision = decision_record.get('decision', '')
    
    if decision == 'DENIED':
        # Request denied - create JIRA ticket and close
        return "jira_create"
    elif decision == 'REQUIRES_APPROVAL':
        # Requires approval - create JIRA ticket and enqueue HIL
        return "jira_create"
    elif decision == 'ALLOWED':
        # Request allowed - create JIRA ticket and proceed to planning
        return "jira_create"
    else:
        # Unknown decision - end workflow
        return "end"


def _route_after_jira_update(state: ITGraphState) -> str:
    """
    Route after JIRA ticket update based on current status
    
    Returns:
        str: Next node to execute
    """
    ticket_record = state.get('ticket_record', {})
    status = ticket_record.get('status', '')
    decision_record = state.get('decision_record', {})
    decision = decision_record.get('decision', '')
    
    if decision == 'DENIED':
        # Ticket already closed by JIRA agent - end workflow
        return "end"
    elif decision == 'REQUIRES_APPROVAL':
        # Requires approval - enqueue HIL question
        return "hil_enqueue"
    elif decision == 'ALLOWED':
        # Request allowed - proceed to planning
        return "planner"
    else:
        # Unknown status - end workflow
        return "end"


def _route_after_hil(state: ITGraphState) -> str:
    """
    Route after human-in-the-loop processing
    
    Returns:
        str: Next node to execute
    """
    hil_response = state.get('hil_response', {})
    decision = hil_response.get('decision', '')
    
    if decision == 'APPROVED':
        # Approved by human - proceed to planning
        return "planner"
    elif decision == 'DENIED':
        # Denied by human - update JIRA ticket status
        return "jira_update"
    elif decision == 'NEEDS_MORE_INFO':
        # Needs more information - update JIRA ticket
        return "jira_update"
    else:
        # Unknown decision - end workflow
        return "end"


def _route_after_it_agent(state: ITGraphState) -> str:
    """
    Route after IT agent execution
    
    Returns:
        str: Next node to execute
    """
    execution_result = state.get('execution_result', {})
    status = execution_result.get('status', '')
    
    if status == 'completed':
        # Plan fully executed - close the request
        return "closer"
    elif status == 'partially_completed':
        # Plan partially completed - update JIRA ticket
        return "jira_update"
    elif status == 'awaiting_employee':
        # Waiting for employee action - update JIRA ticket
        return "jira_update"
    elif status == 'awaiting_manager':
        # Waiting for manager approval - update JIRA ticket
        return "jira_update"
    else:
        # Unknown status - end workflow
        return "end"


def create_workflow_config() -> Dict[str, Any]:
    """
    Create configuration for the workflow
    
    Returns:
        Dict[str, Any]: Workflow configuration
    """
    return {
        "checkpoint_dir": "./storage/checkpoints",
        "enable_persistence": LANGGRAPH_AVAILABLE,  # Only enable if LangGraph is available
        "max_iterations": 50,
        "timeout_seconds": 3600,  # 1 hour
        "retry_attempts": 3,
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "imports_available": IMPORTS_AVAILABLE,
        "nodes": {
            "retrieve": {"timeout": 300},  # 5 minutes
            "router": {"timeout": 60},     # 1 minute
            "classifier": {"timeout": 120}, # 2 minutes
            "jira_create": {"timeout": 60}, # 1 minute
            "jira_update": {"timeout": 60}, # 1 minute
            "hil_enqueue": {"timeout": 30}, # 30 seconds
            "hil_process": {"timeout": 60}, # 1 minute
            "planner": {"timeout": 300},   # 5 minutes
            "it_agent": {"timeout": 600},  # 10 minutes
            "closer": {"timeout": 60}      # 1 minute
        }
    }


def get_workflow_summary() -> str:
    """
    Get a summary of the workflow structure
    
    Returns:
        str: Workflow summary
    """
    langgraph_status = "Available" if LANGGRAPH_AVAILABLE else "Not Available (Development Mode)"
    imports_status = "Available" if IMPORTS_AVAILABLE else "Partially Available (Mock Functions)"
    
    return f"""
IT Support Workflow Summary:

Flow: retrieve → router → classifier → (jira) → (hil?) → planner → it_agent → closer

Node Details:
1. retrieve: Document retrieval and citation generation
2. router: Request complexity evaluation and model selection
3. classifier: Policy compliance classification (ALLOWED/DENIED/REQUIRES_APPROVAL)
4. jira_create: Create JIRA ticket when request is received
5. jira_update: Update JIRA ticket status throughout workflow
6. hil_enqueue: Enqueue human review questions when needed
7. hil_process: Process human responses and decisions
8. planner: Create execution plan for approved requests
9. it_agent: Execute automated actions and generate user guides
10. closer: Complete request, generate satisfaction survey, close ticket

JIRA Agent Workflow:
- Creates ticket when employer sends request
- Moves to "In Progress" when classifier returns ALLOWED or REQUIRES_APPROVAL
- Moves to "Closed" when DENIED
- Updates status based on IT Agent execution results
- Closes ticket when request is fully resolved and employer satisfied

Checkpoint Persistence:
- LangGraph Status: {langgraph_status}
- Node Imports: {imports_status}
- Stored in ./storage/checkpoints
- Enables workflow resumption and state recovery
- Thread-safe for concurrent executions

Note: {langgraph_status}. For production use, please install LangGraph with: pip install langgraph
"""


# Export the main function
__all__ = ["build_graph", "create_workflow_config", "get_workflow_summary"]


# Test function when run directly
if __name__ == "__main__":
    print("=== Testing IT Support Workflow Builder ===\n")
    
    # Test configuration
    config = create_workflow_config()
    print(f"Configuration: {config}\n")
    
    # Test workflow summary
    summary = get_workflow_summary()
    print(summary)
    
    # Test graph building
    try:
        workflow = build_graph()
        print(f"\nWorkflow built successfully!")
        print(f"Nodes: {list(workflow.nodes.keys())}")
        print(f"State type: {workflow.state_type}")
        print(f"Checkpointer: {workflow.checkpointer}")
    except Exception as e:
        print(f"\nError building workflow: {e}")
    
    print("\n=== Test Complete ===")

