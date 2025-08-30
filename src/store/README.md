# Store Module

The store module provides database operations for the Local IT Support system using SQLModel. It includes tables for decisions, plans, tickets, and tool calls, along with repository functions for common database operations.

## Features

- **SQLModel-based tables**: Modern SQL database models with automatic schema generation
- **Repository pattern**: Clean separation of data access logic
- **Automatic table creation**: Tables are created on first run (no migrations needed)
- **Context manager sessions**: Safe database session handling with automatic rollback on errors
- **Comprehensive querying**: Filtering, searching, and statistics functions

## Tables

### Decision
Stores AI-generated decisions for tickets:
- `id`: Unique identifier
- `ticket_id`: Reference to the related ticket
- `decision_text`: The decision made
- `reasoning`: Explanation for the decision
- `confidence_score`: AI confidence level (0.0-1.0)
- `created_at`/`updated_at`: Timestamps
- `created_by`: Employee ID who created the decision
- `status`: Decision status (active, archived, rejected)

### Plan
Stores AI-generated action plans:
- `id`: Unique identifier
- `ticket_id`: Reference to the related ticket
- `plan_title`: Title of the plan
- `plan_description`: Detailed description
- `steps`: JSON string of plan steps
- `priority`: Priority level (low, medium, high, critical)
- `estimated_duration`: Estimated time in minutes
- `created_at`/`updated_at`: Timestamps
- `created_by`: Employee ID who created the plan
- `status`: Plan status (draft, approved, in_progress, completed, cancelled)

### Ticket
Stores IT support tickets:
- `id`: Unique identifier
- `title`: Ticket title
- `description`: Detailed description
- `category`: Ticket category (hardware, software, network, access, other)
- `priority`: Priority level (low, medium, high, critical)
- `status`: Ticket status (open, in_progress, resolved, closed, cancelled)
- `assigned_to`: Employee ID assigned to the ticket
- `created_by`: Employee ID who created the ticket
- `created_at`/`updated_at`: Timestamps
- `resolved_at`: Resolution timestamp
- `resolution_notes`: Notes about the resolution
- `tags`: Comma-separated tags

### ToolCall
Stores AI tool execution logs:
- `id`: Unique identifier
- `ticket_id`: Reference to the related ticket
- `tool_name`: Name of the tool used
- `tool_input`: Input provided to the tool
- `tool_output`: Output from the tool
- `execution_time_ms`: Execution time in milliseconds
- `success`: Whether the tool call succeeded
- `error_message`: Error message if failed
- `created_at`: Timestamp
- `created_by`: Employee ID who initiated the tool call

## Repository Functions

### Core Operations
- `save_decision(decision)`: Save a decision
- `save_plan(plan)`: Save a plan
- `save_ticket(ticket)`: Save a ticket
- `update_ticket_status(ticket_id, new_status, resolution_notes)`: Update ticket status

### Querying
- `list_tickets(employee_id, status, category, limit, offset)`: List tickets with filtering
- `get_ticket(ticket_id)`: Get a specific ticket
- `search_tickets(search_term, employee_id, limit)`: Search tickets by text
- `get_decisions_for_ticket(ticket_id)`: Get decisions for a ticket
- `get_plans_for_ticket(ticket_id)`: Get plans for a ticket
- `get_tool_calls_for_ticket(ticket_id)`: Get tool calls for a ticket

### Reporting
- `get_ticket_statistics(employee_id)`: Get ticket statistics and breakdowns

## Usage

### Basic Setup
```python
from src.store.db import init_db

# Initialize database (creates tables on first run)
init_db()
```

### Creating and Saving Data
```python
from src.store.db import Ticket, save_ticket

# Create a ticket
ticket = Ticket(
    title="Printer Issue",
    description="Printer not working",
    category="hardware",
    priority="high",
    created_by="emp_001"
)

# Save to database
saved_ticket = save_ticket(ticket)
```

### Querying Data
```python
from src.store.db import list_tickets, search_tickets

# List all tickets
all_tickets = list_tickets()

# List tickets for specific employee
employee_tickets = list_tickets(employee_id="emp_001")

# Search tickets
printer_tickets = search_tickets("printer")
```

### Updating Data
```python
from src.store.db import update_ticket_status

# Update ticket status
updated_ticket = update_ticket_status(
    ticket_id="ticket_123",
    new_status="resolved",
    resolution_notes="Replaced printer cartridge"
)
```

## Database Configuration

The database URL is configured in `src/config.py`:
```python
database_url: str = "sqlite:///./local_it_support.db"
```

For production, you can change this to use PostgreSQL, MySQL, or other databases supported by SQLAlchemy.

## Example Workflow

See `example_usage.py` for a complete workflow demonstrating:
1. Database initialization
2. Creating tickets, decisions, and plans
3. Updating ticket status
4. Querying and searching data
5. Generating statistics

## Error Handling

The module uses context managers for database sessions, automatically handling:
- Transaction commits on success
- Transaction rollbacks on errors
- Proper session cleanup

## Dependencies

- `sqlmodel`: Modern SQL database library
- `sqlalchemy`: Database toolkit
- `pydantic`: Data validation
- `uuid`: Unique identifier generation
