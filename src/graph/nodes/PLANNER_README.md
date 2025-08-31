# Planner Node

The Planner Node is a critical component of the IT Support Workflow that generates comprehensive execution plans for IT support requests. It analyzes classified requests and creates detailed action plans that specify who does what, when, and how.

## Overview

The Planner Node:
1. **Generates PlanRecord objects** from the planner.md prompt
2. **Persists plans** to the database for tracking and audit
3. **Handles manager approval requirements** by attaching email drafts to tickets
4. **Marks tickets as requires_approval** when necessary

## Key Features

### Plan Generation
- Creates detailed execution plans with step-by-step actions
- Assigns responsibilities to different actor types (IT agents, employees, managers, systems)
- Estimates duration and identifies dependencies between steps
- Includes risk assessment and compliance checklists

### Approval Workflow Management
- Automatically detects when manager approval is required
- Creates professional email drafts for approval requests
- Attaches approval metadata to tickets
- Manages escalation paths and timeouts

### Database Persistence
- Stores complete plan records in the database
- Maintains audit trail of all planning decisions
- Links plans to tickets and requests for traceability

## Architecture

### Core Classes

#### PlannerPromptCaller
- Calls the planner LLM with the planner.md prompt
- Handles retries and fallback responses
- Formats input data for optimal LLM performance

#### JSONResponseParser
- Parses and validates LLM responses
- Ensures all required fields are present
- Validates field values meet requirements

#### PlanRepository
- Manages persistence of plan records
- Supports both database and in-memory storage
- Handles plan retrieval and updates

#### ApprovalManager
- Manages approval workflows
- Creates enhanced email drafts
- Sends approval emails when configured

### Data Flow

```
User Request → Decision Record → Planner Node → Plan Record → Database
                                    ↓
                              Approval Check
                                    ↓
                              Email Draft → Ticket Attachment
                                    ↓
                              Status Update (requires_approval)
```

## Usage

### Basic Usage

```python
from src.graph.nodes.planner import planner_node

# Create state with required data
state = {
    'user_request': {...},
    'decision_record': {...},
    'retrieved_docs': [...],
    'employee': {...},
    'ticket_record': {...}
}

# Run planner node
result_state = planner_node(state)

# Access generated plan
plan = result_state['plan_record']
requires_approval = result_state['metadata']['planning']['requires_approval']
```

### Integration with Workflow

The planner node is typically called after:
1. **Router Node** - Determines which model to use
2. **Classifier Node** - Provides decision classification
3. **Retrieve Node** - Gathers relevant policies and documents

It prepares data for:
1. **IT Agent Node** - Executes technical tasks
2. **HIL Node** - Manages human-in-the-loop processes
3. **Closer Node** - Finalizes and closes tickets

## Configuration

### LLM Models
- **Planner Model**: Configured in `src/config.py`
- **Fallback Models**: Automatic fallback to emergency procedures
- **Model Selection**: Based on router verdict or default configuration

### Email Configuration
- **SMTP Settings**: Configured in environment variables
- **Template Support**: Uses email templates for consistent formatting
- **Dry Run Mode**: Available for testing without sending emails

### Database Schema
The planner uses the enhanced `Plan` table with fields:
- `plan_id`: Unique plan identifier
- `ticket_id`: Associated ticket
- `request_id`: Associated request
- `classification`: Decision classification
- `priority`: Plan priority level
- `steps`: JSON-encoded execution steps
- `approval_workflow`: JSON-encoded approval details
- `email_draft`: JSON-encoded email content

## Error Handling

### Graceful Degradation
- **Parsing Errors**: Creates fallback plans with manual review requirements
- **LLM Failures**: Falls back to emergency procedures
- **Database Errors**: Continues with in-memory storage

### Error Recovery
- **Automatic Retries**: LLM calls retry up to 3 times
- **Fallback Plans**: Emergency plans created for critical failures
- **Error Logging**: Comprehensive error tracking and reporting

## Testing

### Test Scripts
```bash
# Run basic tests
python src/graph/nodes/test_planner.py

# Test specific functionality
python -c "from src.graph.nodes.planner import test_planner_node; test_planner_node()"
```

### Test Coverage
- **Basic Functionality**: Plan generation and persistence
- **Error Handling**: Graceful degradation and recovery
- **Approval Workflows**: Email draft creation and ticket updates
- **Database Integration**: Plan storage and retrieval

## Monitoring and Debugging

### State Inspection
```python
# Check planning metadata
planning_meta = state.get('metadata', {}).get('planning', {})
print(f"Plan ID: {planning_meta.get('plan_id')}")
print(f"Requires Approval: {planning_meta.get('requires_approval')}")
print(f"Approval Actors: {planning_meta.get('approval_actors')}")
```

### Error Tracking
```python
# Check for errors
errors = state.get('errors', [])
for error in errors:
    print(f"Error: {error['message']}")
    print(f"Severity: {error['severity']}")
```

## Best Practices

### Plan Design
1. **Clear Steps**: Each step should have a single, clear purpose
2. **Actor Assignment**: Assign steps to appropriate actors
3. **Dependency Management**: Clearly define step dependencies
4. **Risk Assessment**: Include comprehensive risk evaluation

### Approval Workflows
1. **Clear Communication**: Use professional, detailed email drafts
2. **Escalation Paths**: Define clear escalation procedures
3. **Timeout Management**: Set reasonable approval timeouts
4. **Documentation**: Maintain complete approval audit trails

### Performance Optimization
1. **LLM Efficiency**: Use appropriate model sizes for complexity
2. **Caching**: Cache frequently used policy information
3. **Async Processing**: Consider async processing for non-blocking operations
4. **Resource Management**: Monitor and optimize resource usage

## Troubleshooting

### Common Issues

#### LLM Response Parsing Failures
- **Symptom**: Plans marked as requiring manual review
- **Cause**: LLM response format doesn't match expected JSON structure
- **Solution**: Check LLM model configuration and prompt formatting

#### Database Persistence Errors
- **Symptom**: Plans not saved to database
- **Cause**: Database connection or schema issues
- **Solution**: Verify database configuration and table structure

#### Email Delivery Failures
- **Symptom**: Approval emails not sent
- **Cause**: SMTP configuration or network issues
- **Solution**: Check email configuration and network connectivity

### Debug Mode
Enable debug logging to see detailed execution information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Advanced Workflow Engine**: Support for complex approval chains
2. **Template Customization**: Configurable email and plan templates
3. **Performance Analytics**: Track planning efficiency and success rates
4. **Integration APIs**: REST APIs for external system integration

### Scalability Improvements
1. **Distributed Processing**: Support for distributed plan execution
2. **Caching Layer**: Redis-based caching for improved performance
3. **Queue Management**: Async job queues for plan processing
4. **Load Balancing**: Support for multiple planner instances

## Contributing

### Development Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables
3. Initialize database: `python -c "from src.store.db import init_db; init_db()"`
4. Run tests: `python src/graph/nodes/test_planner.py`

### Code Standards
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Write unit tests for new functionality
- Update documentation for API changes

### Testing Guidelines
- Test both success and failure scenarios
- Verify error handling and recovery
- Test database integration thoroughly
- Validate email functionality in test mode
