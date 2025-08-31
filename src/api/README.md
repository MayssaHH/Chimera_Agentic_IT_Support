# Local IT Support API

A FastAPI-based REST API for managing AI-powered IT support workflows with human-in-the-loop capabilities.

## Features

- **REST API Endpoints**: Create requests, manage tickets, and handle human approvals
- **Real-time Event Streaming**: Server-Sent Events for live workflow updates
- **Human-in-the-Loop Integration**: Seamless integration of human decision-making
- **Workflow Management**: Integration with LangGraph-based workflow engine
- **Ticket Tracking**: Comprehensive ticket lifecycle management

## Quick Start

### 1. Install Dependencies

```bash
cd src/api
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python server.py
```

The server will start on `http://localhost:8002`

### 3. Access API Documentation

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## API Endpoints

### POST /request

Create a new IT support request and start the workflow.

**Request Body:**
```json
{
  "employee_id": "EMP001",
  "request_type": "software_access",
  "title": "Request for Admin Access",
  "description": "Need admin access to database",
  "priority": "high",
  "urgency": "urgent",
  "business_justification": "Required for quarterly review",
  "desired_completion_date": "2024-01-15T00:00:00Z"
}
```

**Response:**
```json
{
  "ticket_id": "uuid-here",
  "decision": "pending",
  "plan_summary": null,
  "status": "pending",
  "next_action": "workflow_starting"
}
```

### POST /hil/{ticket_id}

Resume workflow with human input/approval.

**Request Body:**
```json
{
  "answer": "Approved with conditions",
  "approval": true,
  "comments": "Access granted for 30 days",
  "approver_id": "MANAGER001"
}
```

**Response:**
```json
{
  "ticket_id": "uuid-here",
  "decision": "approved",
  "plan_summary": "Plan to grant database access",
  "status": "in_progress",
  "next_action": "workflow_in_progress"
}
```

### GET /tickets

Retrieve tickets with optional filtering.

**Query Parameters:**
- `employee_id`: Filter by employee ID
- `status`: Filter by ticket status
- `priority`: Filter by priority level
- `category`: Filter by request category

**Example:**
```
GET /tickets?employee_id=EMP001&status=pending
```

**Response:**
```json
{
  "tickets": [
    {
      "ticket_id": "uuid-here",
      "title": "Request for Admin Access",
      "status": "pending",
      "employee_id": "EMP001",
      "request_type": "software_access",
      "created_at": "2024-01-10T10:00:00Z",
      "priority": "high"
    }
  ],
  "count": 1
}
```

### GET /events/{ticket_id}

Stream real-time events for a specific ticket using Server-Sent Events.

**Response:** Server-Sent Events stream with events like:
```json
{"type": "connected", "ticket_id": "uuid-here"}
{"type": "workflow_update", "ticket_id": "uuid-here", "status": "in_progress", "decision": "approved", "timestamp": "2024-01-10T10:00:00Z"}
{"type": "hil_response", "ticket_id": "uuid-here", "approval": true, "approver_id": "MANAGER001", "timestamp": "2024-01-10T10:00:00Z"}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-10T10:00:00Z"
}
```

## Workflow States

The API manages tickets through various workflow states:

- **pending**: Request created, workflow starting
- **in_progress**: Workflow running
- **waiting_for_user**: Human input required
- **waiting_for_approval**: Manager approval required
- **resolved**: Request completed successfully
- **denied**: Request denied
- **escalated**: Request escalated to higher level
- **error**: Workflow encountered an error

## Event Types

The event stream provides real-time updates:

- **connected**: Client connected to event stream
- **workflow_update**: Workflow status or decision changed
- **hil_response**: Human-in-the-loop response received
- **error**: Error occurred during workflow execution
- **keepalive**: Connection keepalive (every 30 seconds)

## Usage Examples

### Python Client

```python
from api.example_usage import ITSupportAPIClient

client = ITSupportAPIClient()

# Create a request
response = client.create_request({
    "employee_id": "EMP001",
    "request_type": "software_access",
    "title": "Database Access Request",
    "description": "Need access to customer database",
    "priority": "high"
})

ticket_id = response['ticket_id']

# Submit human approval
client.submit_hil_response(ticket_id, {
    "answer": "Approved",
    "approval": True,
    "approver_id": "MANAGER001"
})
```

### JavaScript/Node.js Client

```javascript
// Create a request
const response = await fetch('http://localhost:8000/request', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    employee_id: 'EMP001',
    request_type: 'software_access',
    title: 'Database Access Request',
    description: 'Need access to customer database',
    priority: 'high'
  })
});

const ticket = await response.json();
const ticketId = ticket.ticket_id;

// Stream events
const eventSource = new EventSource(`http://localhost:8000/events/${ticketId}`);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

### cURL Examples

```bash
# Create a request
curl -X POST "http://localhost:8000/request" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP001",
    "request_type": "software_access",
    "title": "Database Access",
    "description": "Need admin access",
    "priority": "high"
  }'

# Submit HIL response
curl -X POST "http://localhost:8000/hil/{ticket_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Approved",
    "approval": true,
    "approver_id": "MANAGER001"
  }'

# Get tickets
curl "http://localhost:8000/tickets?employee_id=EMP001"

# Stream events
curl "http://localhost:8000/events/{ticket_id}"
```

## Configuration

### Environment Variables

Create a `.env` file in the `src/api` directory:

```env
# Server configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# CORS settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Workflow configuration
WORKFLOW_TIMEOUT=300
MAX_CONCURRENT_WORKFLOWS=10
```

### CORS Configuration

The API includes CORS middleware. For production, configure allowed origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Not Found (ticket not found)
- **500**: Internal Server Error (workflow execution failed)

Error responses include a detail message:

```json
{
  "detail": "Failed to create request: Invalid employee ID"
}
```

## Testing

### Run Examples

```bash
cd src/api
python example_usage.py
```

### Manual Testing

1. Start the server: `python server.py`
2. Use the Swagger UI at http://localhost:8000/docs
3. Test endpoints with the interactive interface

## Development

### Project Structure

```
src/api/
├── __init__.py          # Package initialization
├── server.py            # Main FastAPI application
├── requirements.txt     # Python dependencies
├── example_usage.py     # Usage examples
└── README.md           # This file
```

### Adding New Endpoints

1. Define the endpoint function in `server.py`
2. Add appropriate request/response models
3. Update the root endpoint documentation
4. Add tests if applicable

### Workflow Integration

The API integrates with the LangGraph workflow engine:

1. **Request Creation**: Initializes workflow state
2. **Workflow Execution**: Runs the graph until pause/completion
3. **State Management**: Maintains workflow state for each ticket
4. **Event Emission**: Streams workflow updates in real-time

## Production Considerations

### Security

- Implement authentication and authorization
- Validate all input data
- Rate limiting for API endpoints
- HTTPS in production

### Performance

- Database persistence for ticket data
- Redis for event streaming
- Load balancing for multiple instances
- Monitoring and logging

### Deployment

- Use production WSGI server (Gunicorn)
- Environment-specific configuration
- Health checks and monitoring
- Backup and recovery procedures

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Workflow Failures**: Check LangGraph installation and configuration
3. **Event Streaming Issues**: Verify client supports Server-Sent Events
4. **CORS Errors**: Configure allowed origins appropriately

### Logs

Enable debug logging by setting `LOG_LEVEL=debug` in your environment.

### Support

For issues related to:
- **API**: Check this README and example usage
- **Workflow Engine**: See the graph module documentation
- **Domain Models**: Refer to the domain schemas
