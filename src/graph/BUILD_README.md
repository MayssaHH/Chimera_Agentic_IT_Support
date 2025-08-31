# IT Support Workflow Graph Builder

This module provides the `build_graph()` function that creates and configures the complete IT Support Workflow using LangGraph.

## Overview

The workflow follows this pattern:
```
retrieve → router → classifier → (jira) → (hil?) → planner → it_agent → closer
```

## Key Features

- **Complete Node Wiring**: All nodes are properly connected with conditional edges
- **JIRA Agent Integration**: Manages ticket lifecycle throughout the workflow
- **Checkpoint Persistence**: Uses LangGraph persistence for state recovery
- **Human-in-the-Loop Support**: Handles approval workflows and escalations
- **Flexible Routing**: Conditional routing based on workflow state

## Workflow Flow

### 1. Initial Request Processing
- **retrieve**: Fetches relevant policies and procedures
- **router**: Evaluates request complexity and selects appropriate models
- **classifier**: Determines if request is ALLOWED, DENIED, or REQUIRES_APPROVAL

### 2. JIRA Ticket Management
- **jira_create**: Creates JIRA ticket when request is received
- **jira_update**: Updates ticket status throughout the workflow

### 3. Approval & Planning
- **hil_enqueue**: Enqueues human review questions when needed
- **hil_process**: Processes human responses and decisions
- **planner**: Creates execution plan for approved requests

### 4. Execution & Completion
- **it_agent**: Executes automated actions and generates user guides
- **closer**: Completes request, generates satisfaction survey, closes ticket

## JIRA Agent Workflow

The JIRA Agent is a central component that manages ticket status throughout the entire workflow:

1. **Ticket Creation**: Creates ticket when employer sends any request
2. **Status Transitions**:
   - Moves to "In Progress" when classifier returns ALLOWED or REQUIRES_APPROVAL
   - Moves to "Closed" when DENIED
   - Updates status based on IT Agent execution results
3. **Final Closure**: Closes ticket when request is fully resolved and employer satisfied

## Usage

### Basic Usage

```python
from src.graph.build import build_graph

# Create workflow with default settings
workflow = build_graph()

# Compile the workflow
compiled_workflow = workflow.compile()

# Run the workflow
result = await compiled_workflow.ainvoke(initial_state)
```

### With Custom Configuration

```python
from src.graph.build import build_graph, create_workflow_config

# Create custom configuration
config = create_workflow_config()
config["checkpoint_dir"] = "./custom/checkpoints"
config["enable_persistence"] = True

# Build workflow with custom config
workflow = build_graph(
    checkpoint_dir=config["checkpoint_dir"],
    enable_persistence=config["enable_persistence"]
)
```

### Checkpoint Persistence

The workflow automatically creates checkpoints in `./storage/checkpoints` (or custom directory):

```python
# Enable persistence (default: True)
workflow = build_graph(enable_persistence=True)

# Custom checkpoint directory
workflow = build_graph(checkpoint_dir="./my_checkpoints")
```

## Configuration Options

### Workflow Configuration

```python
config = create_workflow_config()
# Returns:
{
    "checkpoint_dir": "./storage/checkpoints",
    "enable_persistence": True,
    "max_iterations": 50,
    "timeout_seconds": 3600,  # 1 hour
    "retry_attempts": 3,
    "nodes": {
        "retrieve": {"timeout": 300},      # 5 minutes
        "router": {"timeout": 60},         # 1 minute
        "classifier": {"timeout": 120},    # 2 minutes
        "jira_create": {"timeout": 60},   # 1 minute
        "jira_update": {"timeout": 60},   # 1 minute
        "hil_enqueue": {"timeout": 30},   # 30 seconds
        "hil_process": {"timeout": 60},   # 1 minute
        "planner": {"timeout": 300},      # 5 minutes
        "it_agent": {"timeout": 600},     # 10 minutes
        "closer": {"timeout": 60}         # 1 minute
    }
}
```

## Routing Logic

### After Classification
- `DENIED` → Create JIRA ticket and close
- `REQUIRES_APPROVAL` → Create JIRA ticket and enqueue HIL
- `ALLOWED` → Create JIRA ticket and proceed to planning

### After JIRA Update
- `DENIED` → End workflow (ticket closed)
- `REQUIRES_APPROVAL` → Enqueue HIL question
- `ALLOWED` → Proceed to planning

### After HIL Processing
- `APPROVED` → Proceed to planning
- `DENIED` → Update JIRA ticket status
- `NEEDS_MORE_INFO` → Update JIRA ticket

### After IT Agent
- `completed` → Close the request
- `partially_completed` → Update JIRA ticket
- `awaiting_employee` → Update JIRA ticket
- `awaiting_manager` → Update JIRA ticket

## Error Handling

The workflow includes comprehensive error handling:

- Each node captures errors in the state
- Errors are logged with context and severity
- Workflow can continue with partial results
- Checkpoint persistence enables error recovery

## Testing

Run the example usage to test the workflow:

```bash
cd src/graph
python example_usage.py
```

## Dependencies

- **LangGraph**: For workflow orchestration and persistence
- **Node Modules**: All node functions must be properly implemented
- **State Management**: ITGraphState must be properly configured

## File Structure

```
src/graph/
├── build.py              # Main graph builder
├── example_usage.py      # Usage examples
├── BUILD_README.md       # This documentation
├── state.py              # State definitions
└── nodes/                # Node implementations
    ├── retrieve.py       # Document retrieval
    ├── router.py         # Request routing
    ├── classifier.py     # Policy classification
    ├── jira_agent.py     # JIRA ticket management
    ├── hil.py            # Human-in-the-loop
    ├── planner.py        # Execution planning
    ├── it_agent.py       # Plan execution
    └── closer.py         # Request completion
```

## Future Enhancements

- **Dynamic Node Configuration**: Runtime node configuration
- **Advanced Persistence**: Database-backed checkpoints
- **Monitoring**: Workflow execution metrics
- **Scaling**: Distributed workflow execution
- **Custom Routing**: User-defined routing logic
