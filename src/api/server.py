"""
FastAPI Server for Local IT Support System

This server provides REST API endpoints and Server-Sent Events for:
- Processing IT support requests through the workflow graph
- Human-in-the-loop interactions
- Ticket management and status tracking
- Real-time event streaming
"""

import asyncio
import json
import logging
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import domain schemas
try:
    from ..domain.schemas import (
        UserRequest as DomainUserRequest,
        TicketRecord,
        DecisionRecord,
        PlanRecord,
        RequestDecision,
        TicketStatus
    )
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('/Users/Mayssa/Chimera_Agentic_IT_Support')
    from src.domain.schemas import (
        UserRequest as DomainUserRequest,
        TicketRecord,
        DecisionRecord,
        PlanRecord,
        RequestDecision,
        TicketStatus
    )

# Import graph components
try:
    from ..graph.build import build_graph
    from ..graph.state import ITGraphState, RequestStatus, DecisionType
except ImportError:
    # Fallback for direct execution
    from src.graph.build import build_graph
from src.graph.state import ITGraphState, RequestStatus, DecisionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# API Models
class UserRequest(BaseModel):
    """API model for user requests."""
    employee_id: str = Field(..., description="Employee ID making the request")
    request_type: str = Field(..., description="Type of request")
    title: str = Field(..., description="Request title")
    description: str = Field(..., description="Request description")
    priority: str = Field("medium", description="Request priority")
    urgency: str = Field("normal", description="Request urgency")
    business_justification: Optional[str] = Field(None, description="Business justification")
    desired_completion_date: Optional[datetime] = Field(None, description="Desired completion date")


class HILResponse(BaseModel):
    """Human-in-the-loop response."""
    answer: str = Field(..., description="Human answer or decision")
    approval: bool = Field(..., description="Whether request is approved")
    comments: Optional[str] = Field(None, description="Additional comments")
    approver_id: str = Field(..., description="ID of the person providing the response")


class TicketResponse(BaseModel):
    """Response model for ticket creation."""
    ticket_id: str = Field(..., description="Generated ticket ID")
    decision: str = Field(..., description="Decision made by the system")
    plan_summary: Optional[str] = Field(None, description="Summary of the execution plan")
    status: str = Field(..., description="Current ticket status")
    message: Optional[str] = Field(None, description="Response message")
    next_action: Optional[str] = Field(..., description="Next action required")


class TicketFilter(BaseModel):
    """Filter model for ticket queries."""
    employee_id: Optional[str] = Field(None, description="Filter by employee ID")
    status: Optional[str] = Field(None, description="Filter by ticket status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    category: Optional[str] = Field(None, description="Filter by category")


# Global state for the application
class AppState:
    """Application state for managing workflows and tickets."""
    
    def __init__(self):
        self.workflow = build_graph()
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self.event_streams: Dict[str, asyncio.Queue] = {}
    
    def create_ticket(self, request: UserRequest) -> str:
        """Create a new ticket and initialize workflow state."""
        ticket_id = str(uuid.uuid4())
        
        # Store ticket info
        self.active_tickets[ticket_id] = {
            "employee_id": request.employee_id,
            "request_type": request.request_type,
            "title": request.title,
            "description": request.description,
            "priority": request.priority,
            "urgency": request.urgency,
            "business_justification": request.business_justification,
            "desired_completion_date": request.desired_completion_date,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "events": []
        }
        
        # Initialize event stream
        self.event_streams[ticket_id] = asyncio.Queue()
        
        return ticket_id
    
    def add_event(self, ticket_id: str, event_type: str, data: Dict[str, Any]):
        """Add event to ticket history"""
        if ticket_id in self.active_tickets:
            event = {
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'data': data
            }
            self.active_tickets[ticket_id]['events'].append(event)
            
            # Notify event stream if exists
            if ticket_id in self.event_streams:
                try:
                    # Use asyncio.run_coroutine_threadsafe for thread safety
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.event_streams[ticket_id].put(event))
                    else:
                        # Fallback for when loop is not running
                        asyncio.run_coroutine_threadsafe(
                            self.event_streams[ticket_id].put(event), 
                            loop
                        )
                except Exception as e:
                    logger.warning(f"Failed to add event to stream: {e}")
    
    async def run_workflow(self, ticket_id: str, state: ITGraphState):
        """Run the workflow for a ticket"""
        try:
            logger.info(f"Starting workflow for ticket {ticket_id}")
            
            # Add workflow start event
            self.add_event(ticket_id, "workflow_started", {
                "message": "AI workflow execution started"
            })
            
            # Execute workflow with proper method detection
            result = await self._execute_workflow(state)
            
            # Update ticket status based on result
            if result:
                # Extract decision from the workflow state
                decision = self._get_decision(result)
                plan_summary = self._get_plan_summary(result)
                status = self._get_status(result)
                
                # Update ticket
                if ticket_id in self.active_tickets:
                    self.active_tickets[ticket_id]['status'] = status
                    self.active_tickets[ticket_id]['decision'] = decision
                    self.active_tickets[ticket_id]['plan_summary'] = plan_summary
                
                # Add completion event
                self.add_event(ticket_id, "workflow_completed", {
                    "decision": decision,
                    "plan_summary": plan_summary,
                    "status": status
                })
                
                logger.info(f"Workflow completed for ticket {ticket_id}: {decision}")
            else:
                logger.warning(f"Workflow returned no result for ticket {ticket_id}")
                self.add_event(ticket_id, "workflow_error", {
                    "error": "Workflow execution returned no result"
                })
                
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Add error event
            self.add_event(ticket_id, "workflow_error", {
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            
            # Update ticket status
            if ticket_id in self.active_tickets:
                self.active_tickets[ticket_id]['status'] = RequestStatus.DENIED
    
    async def resume_workflow(self, ticket_id: str, hil_response: HILResponse) -> TicketResponse:
        """Resume workflow with human input."""
        if ticket_id not in self.active_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket_info = self.active_tickets[ticket_id]
        state = ticket_info["state"]
        
        # Update state with human input
        state["human_input"] = {
            "answer": hil_response.answer,
            "approval": hil_response.approval,
            "comments": hil_response.comments,
            "approver_id": hil_response.approver_id,
            "timestamp": datetime.now()
        }
        
        # Emit HIL event
        await self._emit_event(ticket_id, {
            "type": "hil_response",
            "ticket_id": ticket_id,
            "approval": hil_response.approval,
            "approver_id": hil_response.approver_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Continue workflow execution
        return await self.run_workflow(ticket_id)
    
    async def _execute_workflow(self, state: ITGraphState) -> Dict[str, Any]:
        """Execute workflow with proper method detection"""
        if not self.workflow:
            raise Exception("Workflow not initialized")
        
        # Execute the real workflow
        if hasattr(self.workflow, 'ainvoke'):
            result = await self.workflow.ainvoke(state)
        elif hasattr(self.workflow, 'invoke'):
            result = self.workflow.invoke(state)
        else:
            raise Exception("Workflow has no execution methods available")
        
        return result

    def get_tickets(self, filters: TicketFilter) -> List[Dict[str, Any]]:
        """Get tickets based on filters."""
        tickets = []
        
        for ticket_id, ticket_info in self.active_tickets.items():
            # Apply filters
            if filters.employee_id and ticket_info["employee_id"] != filters.employee_id:
                continue
            if filters.status and ticket_info["status"] != filters.status:
                continue
            if filters.priority and ticket_info["priority"] != filters.priority:
                continue
            if filters.category and ticket_info["request_type"] != filters.category:
                continue
            
            tickets.append({
                "ticket_id": ticket_id,
                "title": ticket_info["title"],
                "status": ticket_info["status"],
                "employee_id": ticket_info["employee_id"],
                "request_type": ticket_info["request_type"],
                "created_at": ticket_info["created_at"],
                "priority": ticket_info["priority"]
            })
        
        return tickets
    
    async def _emit_event(self, ticket_id: str, event: Dict[str, Any]):
        """Emit an event to the ticket's event stream."""
        if ticket_id in self.event_streams:
            await self.event_streams[ticket_id].put(event)
    
    def _get_decision(self, state: ITGraphState) -> str:
        """Extract decision from workflow state."""
        # Check for decision_record from classifier node
        if state.get("decision_record"):
            decision_record = state["decision_record"]
            if isinstance(decision_record, dict):
                return decision_record.get("decision", "pending")
            elif hasattr(decision_record, 'decision'):
                return str(decision_record.decision)
            return str(decision_record)
        
        # Check for final decision in metadata
        if state.get("metadata", {}).get("classification", {}).get("decision"):
            return state["metadata"]["classification"]["decision"]
        
        # Check for any decision field
        if state.get("decision"):
            return str(state["decision"])
        
        return "pending"
    
    def _get_plan_summary(self, state: ITGraphState) -> Optional[str]:
        """Extract plan summary from workflow state."""
        # Check for plan_record from planner node
        if state.get("plan_record"):
            plan_record = state["plan_record"]
            if isinstance(plan_record, dict):
                return plan_record.get("description", "No plan available")
            elif hasattr(plan_record, 'description'):
                return plan_record.description
            return str(plan_record)
        
        # Check for plan in metadata
        if state.get("metadata", {}).get("planning", {}).get("plan_summary"):
            return state["metadata"]["planning"]["plan_summary"]
        
        # Check for execution plan
        if state.get("execution_plan"):
            plan = state["execution_plan"]
            if isinstance(plan, dict) and "description" in plan:
                return plan["description"]
        
        return "No plan available"
    
    def _get_next_action(self, state: ITGraphState) -> Optional[str]:
        """Determine next action required."""
        status = state.get("status")
        if status == RequestStatus.WAITING_FOR_USER:
            return "human_input_required"
        elif status == RequestStatus.WAITING_FOR_APPROVAL:
            return "approval_required"
        elif status == RequestStatus.IN_PROGRESS:
            return "workflow_in_progress"
        elif status == RequestStatus.RESOLVED:
            return "completed"
        elif status == RequestStatus.DENIED:
            return "request_denied"
        return None
    
    def _get_status(self, state: ITGraphState) -> str:
        """Extract status from workflow state."""
        # Check for ticket_record status
        if state.get("ticket_record", {}).get("status"):
            return state["ticket_record"]["status"]
        
        # Check for decision-based status
        decision = self._get_decision(state)
        if decision == "DENIED":
            return RequestStatus.DENIED
        elif decision == "ALLOWED":
            return RequestStatus.IN_PROGRESS
        elif decision == "REQUIRES_APPROVAL":
            return RequestStatus.WAITING_FOR_APPROVAL
        
        # Check for HIL pending
        if state.get("hil_pending"):
            return RequestStatus.WAITING_FOR_APPROVAL
        
        # Default status
        return RequestStatus.PENDING


# Application state
app_state = AppState()


# FastAPI app setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Local IT Support API",
    description="API for AI-powered IT support workflow management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints

@app.post("/request", response_model=TicketResponse)
async def create_request(
    request: UserRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new IT support request and run the workflow.
    
    Returns ticket ID, decision, and plan summary.
    """
    try:
        # Create ticket
        ticket_id = app_state.create_ticket(request)
        
        # Initialize workflow state with all required fields
        state = ITGraphState(
            user_request={
                "request_id": ticket_id,
                "title": request.title,
                "description": request.description,
                "category": request.request_type,
                "priority": request.priority,
                "submitted_at": datetime.now(),
                "requested_by": request.employee_id,
                "department": "IT",  # Default department
                "urgency": request.urgency,
                "attachments": [],
                "custom_fields": {
                    "business_justification": request.business_justification,
                    "desired_completion_date": request.desired_completion_date
                }
            },
            employee={
                "employee_id": request.employee_id,
                "name": f"Employee {request.employee_id}",
                "email": f"{request.employee_id}@company.com",
                "department": "IT",
                "role": "Employee",
                "manager": "IT_Manager",
                "access_level": "Standard",
                "location": "Main Office",
                "contact_info": {}
            },
            retrieved_docs=[],
            citations=[],
            router_verdict={},
            decision_record={},
            plan_record={},
            ticket_record={
                "ticket_id": ticket_id,
                "status": RequestStatus.PENDING,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            hil_pending=[],
            errors=[]
        )
        
        # Run workflow in background
        background_tasks.add_task(app_state.run_workflow, ticket_id, state)
        
        # Return initial response
        return TicketResponse(
            ticket_id=ticket_id,
            decision="pending",
            plan_summary="Workflow started, processing request...",
            status="pending",
            message="Request submitted successfully. Workflow is processing in the background.",
            next_action="workflow_starting"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create request: {str(e)}")


@app.post("/hil/{ticket_id}", response_model=TicketResponse)
async def human_in_loop(
    ticket_id: str,
    hil_response: HILResponse
):
    """
    Resume workflow with human input/approval.
    
    This endpoint is called when human intervention is required.
    """
    try:
        return await app_state.resume_workflow(ticket_id, hil_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")


@app.get("/tickets")
async def get_tickets(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Get tickets for the frontend board.
    
    Supports filtering by employee_id, status, priority, and category.
    """
    try:
        filters = TicketFilter(
            employee_id=employee_id,
            status=status,
            priority=priority,
            category=category
        )
        tickets = app_state.get_tickets(filters)
        return {"tickets": tickets, "count": len(tickets)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tickets: {str(e)}")


@app.get("/events/{ticket_id}")
async def stream_events(ticket_id: str):
    """
    Stream graph events via Server-Sent Events.
    
    Provides real-time updates for a specific ticket.
    """
    if ticket_id not in app_state.event_streams:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    async def event_generator():
        queue = app_state.event_streams[ticket_id]
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'ticket_id': ticket_id})}\n\n"
        
        # Send existing events first
        if ticket_id in app_state.active_tickets:
            existing_events = app_state.active_tickets[ticket_id].get('events', [])
            for event in existing_events[-5:]:  # Send last 5 events
                yield f"data: {json.dumps(event)}\n\n"
        
        try:
            while True:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=10.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive and check if ticket still exists
                    if ticket_id not in app_state.active_tickets:
                        yield f"data: {json.dumps({'type': 'ticket_closed', 'message': 'Ticket no longer exists'})}\n\n"
                        break
                    
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            # Client disconnected
            pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@app.get("/events/{ticket_id}/history")
async def get_ticket_events(ticket_id: str):
    """
    Get ticket event history (non-streaming).
    
    Useful for debugging and getting all events at once.
    """
    if ticket_id not in app_state.active_tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket_info = app_state.active_tickets[ticket_id]
    events = ticket_info.get('events', [])
    
    return {
        "ticket_id": ticket_id,
        "events": events,
        "event_count": len(events),
        "last_updated": ticket_info.get('updated_at', ticket_info.get('created_at'))
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Local IT Support API",
        "version": "1.0.0",
        "endpoints": {
            "POST /request": "Create new IT support request",
            "POST /hil/{ticket_id}": "Resume workflow with human input",
            "GET /tickets": "Get tickets with optional filters",
            "GET /events/{ticket_id}": "Stream real-time events",
            "GET /health": "Health check"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
