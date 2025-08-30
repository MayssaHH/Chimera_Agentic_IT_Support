# Tools Package

The tools package provides external service integrations for the Local IT Support system, including Jira ticket management.

## Jira Client

The `JiraClient` class provides a comprehensive interface for managing IT support tickets in Jira, with support for the complete ticket lifecycle and workflow state transitions.

### Features

- **Ticket Management**: Create, retrieve, and update tickets
- **Workflow Transitions**: Move tickets through defined workflow states
- **Employee Search**: Find tickets by employee assignment or creation
- **Robust Error Handling**: Retry logic with tenacity for network resilience
- **Dry-Run Mode**: Safe testing and development without affecting production
- **Context Manager**: Automatic resource cleanup with `with` statements

### Workflow States

The client maps to standard Jira workflow states:

- **`new`** → "To Do" (ID: 10000)
- **`in_progress`** → "In Progress" (ID: 3)  
- **`resolved`** → "Done" (ID: 10001)
- **`closed`** → "Closed" (ID: 6)

### Configuration

Jira credentials are read from the application configuration:

```python
# In src/config.py or environment variables
jira_base_url: str = "https://your-domain.atlassian.net"
jira_user: str = "your-email@company.com"
jira_token: str = "your-api-token"
```

### Usage Examples

#### Basic Initialization

```python
from src.tools import JiraClient

# Production mode
with JiraClient(dry_run=False) as jira:
    # Use client...

# Development mode (no actual API calls)
with JiraClient(dry_run=True) as jira:
    # Test functionality safely...
```

#### Creating Tickets

```python
ticket = jira.create_ticket(
    summary="Printer not working",
    description="HP LaserJet showing paper jam error",
    employee_id="emp_marketing_001",
    priority="High",
    issue_type="Task"
)

print(f"Created ticket: {ticket['key']}")
```

#### Workflow Transitions

```python
# Start working on ticket
jira.transition_ticket(ticket['id'], "in_progress")

# Mark as resolved
jira.transition_ticket(ticket['id'], "resolved")

# Close ticket
jira.transition_ticket(ticket['id'], "closed")
```

#### Retrieving Tickets

```python
# Get specific ticket
ticket_details = jira.get_ticket("IT-123")
if ticket_details:
    print(f"Status: {ticket_details['status']}")
    print(f"Assignee: {ticket_details['assignee']}")

# Search employee tickets
employee_tickets = jira.search_employee_tickets(
    "emp_001",
    status="in_progress",
    max_results=10
)
```

#### Error Handling and Retry Logic

The client automatically handles:
- Network timeouts and connection errors
- HTTP status errors with detailed logging
- Exponential backoff retry for transient failures
- Graceful degradation for API errors

```python
try:
    ticket = jira.create_ticket(...)
except httpx.HTTPStatusError as e:
    print(f"Jira API error: {e.response.status_code}")
except httpx.RequestError as e:
    print(f"Network error: {e}")
```

### Dry-Run Mode

Dry-run mode is perfect for:
- Local development and testing
- CI/CD pipeline validation
- Documentation and training
- Safe experimentation

```python
# In dry-run mode, all operations return simulated data
with JiraClient(dry_run=True) as jira:
    ticket = jira.create_ticket(...)
    # Returns: {"id": "DRY-RUN-001", "key": "IT-DRY-001", ...}
    
    jira.transition_ticket("TEST-001", "in_progress")
    # Always returns True, logs the operation
```

### Advanced Features

#### Custom Project Configuration

```python
# Get project information
project_info = jira.get_project_info("IT")
print(f"Project: {project_info['name']}")

# Create tickets in different projects
ticket = jira.create_ticket(
    summary="Network issue",
    description="Cannot connect to corporate network",
    employee_id="emp_001",
    issue_type="Bug"
    # Uses default "IT" project
)
```

#### Credential Validation

```python
# Test connection before operations
if jira.validate_credentials():
    print("✓ Jira connection successful")
else:
    print("✗ Jira connection failed")
```

#### Context Manager Benefits

```python
# Automatic cleanup and error handling
with JiraClient(dry_run=False) as jira:
    # Client automatically closes HTTP connections
    # Even if exceptions occur
    ticket = jira.create_ticket(...)
    # Client.close() called automatically
```

### Error Handling

The client provides comprehensive error handling:

- **HTTP Errors**: Detailed logging of Jira API responses
- **Network Errors**: Automatic retry with exponential backoff
- **Validation Errors**: Clear error messages for invalid operations
- **State Errors**: Graceful handling of invalid workflow transitions

### Testing

The package includes comprehensive tests:

```bash
# Run all tests
pytest src/tools/

# Run specific test file
pytest src/tools/test_jira.py

# Run with coverage
pytest --cov=src.tools src/tools/
```

### Dependencies

- `httpx`: Modern HTTP client with async support
- `tenacity`: Retry logic for resilience
- `pydantic-settings`: Configuration management

### Best Practices

1. **Always use context managers** for automatic cleanup
2. **Enable dry-run mode** during development
3. **Handle exceptions gracefully** in production code
4. **Validate credentials** before operations
5. **Use appropriate timeouts** for your network conditions
6. **Monitor retry behavior** in production logs

### Troubleshooting

#### Common Issues

- **Authentication Errors**: Verify API token and user permissions
- **Network Timeouts**: Check firewall and proxy settings
- **Invalid Transitions**: Ensure workflow allows the requested state change
- **Project Access**: Verify user has access to the target project

#### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('src.tools.jira').setLevel(logging.DEBUG)
```

### Integration with Store Module

The Jira client integrates seamlessly with the database store:

```python
from src.store import save_ticket, update_ticket_status
from src.tools import JiraClient

# Create ticket in Jira and store locally
with JiraClient() as jira:
    jira_ticket = jira.create_ticket(...)
    
    # Store in local database
    local_ticket = Ticket(
        title=jira_ticket['summary'],
        description="...",
        external_id=jira_ticket['key'],
        status=jira_ticket['status']
    )
    save_ticket(local_ticket)
```

This provides a complete audit trail and local backup of all Jira operations.
