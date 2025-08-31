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
from domain.schemas import (
    UserRequest as DomainUserRequest,
    TicketRecord,
    DecisionRecord,
    PlanRecord,
    RequestDecision,
    TicketStatus
)

# Import graph components
from graph.build import build_workflow
from graph.state import ITGraphState, RequestStatus, DecisionType


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
        self.workflow = build_workflow()
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self.event_streams: Dict[str, asyncio.Queue] = {}
    
    def create_ticket(self, request: UserRequest) -> str:
        """Create a new ticket and initialize workflow state."""
        ticket_id = str(uuid.uuid4())
        
        # Initialize workflow state
        initial_state = ITGraphState(
            request_id=ticket_id,
            status=RequestStatus.PENDING,
            user_request={
                "request_id": ticket_id,
                "title": request.title,
                "description": request.description,
                "category": request.request_type,
                "priority": request.priority,
                "submitted_at": datetime.utcnow(),
                "requested_by": request.employee_id,
                "department": "",  # Will be retrieved from employee data
                "urgency": request.urgency,
                "attachments": [],
                "custom_fields": {
                    "business_justification": request.business_justification,
                    "desired_completion_date": request.desired_completion_date
                }
            },
            employee={},
            retrieved_documents=[],
            citations=[],
            router_verdict=None,
            classification_decision=None,
            execution_plan=None,
            current_step=None,
            tool_calls=[],
            risk_flags=[],
            approval_required=False,
            approval_level=None,
            approval_chain=[],
            human_input=None,
            final_decision=None,
            resolution_summary=None,
            error_message=None,
            metadata={}
        )
        
        # Store ticket info
        self.active_tickets[ticket_id] = {
            "state": initial_state,
            "created_at": datetime.utcnow(),
            "status": "pending",
            "employee_id": request.employee_id,
            "title": request.title,
            "request_type": request.request_type
        }
        
        # Initialize event stream
        self.event_streams[ticket_id] = asyncio.Queue()
        
        return ticket_id
    
    async def run_workflow(self, ticket_id: str) -> TicketResponse:
        """Run the workflow for a ticket until it pauses or completes."""
        if ticket_id not in self.active_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket_info = self.active_tickets[ticket_id]
        state = ticket_info["state"]
        
        try:
            # Run workflow until it pauses or completes
            config = {"configurable": {"thread_id": ticket_id}}
            result = await self.workflow.ainvoke(state, config)
            
            # Update stored state
            ticket_info["state"] = result
            
            # Determine response based on workflow state
            decision = self._get_decision(result)
            plan_summary = self._get_plan_summary(result)
            status = result.get("status", "unknown")
            next_action = self._get_next_action(result)
            
            # Emit events for real-time updates
            await self._emit_event(ticket_id, {
                "type": "workflow_update",
                "ticket_id": ticket_id,
                "status": status,
                "decision": decision,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return TicketResponse(
                ticket_id=ticket_id,
                decision=decision,
                plan_summary=plan_summary,
                status=status,
                next_action=next_action
            )
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            await self._emit_event(ticket_id, {
                "type": "error",
                "ticket_id": ticket_id,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            })
            raise HTTPException(status_code=500, detail=error_msg)
    
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
            "timestamp": datetime.utcnow()
        }
        
        # Emit HIL event
        await self._emit_event(ticket_id, {
            "type": "hil_response",
            "ticket_id": ticket_id,
            "approval": hil_response.approval,
            "approver_id": hil_response.approver_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Continue workflow execution
        return await self.run_workflow(ticket_id)
    
    def get_tickets(self, filters: TicketFilter) -> List[Dict[str, Any]]:
        """Get tickets based on filters."""
        tickets = []
        
        for ticket_id, ticket_info in self.active_tickets.items():
            # Apply filters
            if filters.employee_id and ticket_info["employee_id"] != filters.employee_id:
                continue
            if filters.status and ticket_info["status"] != filters.status:
                continue
            if filters.priority and ticket_info["state"].get("user_request", {}).get("priority") != filters.priority:
                continue
            if filters.category and ticket_info["request_type"] != filters.category:
                continue
            
            tickets.append({
                "ticket_id": ticket_id,
                "title": ticket_info["title"],
                "status": ticket_info["status"],
                "employee_id": ticket_info["employee_id"],
                "request_type": ticket_info["request_type"],
                "created_at": ticket_info["created_at"].isoformat(),
                "priority": ticket_info["state"].get("user_request", {}).get("priority", "medium")
            })
        
        return tickets
    
    async def _emit_event(self, ticket_id: str, event: Dict[str, Any]):
        """Emit an event to the ticket's event stream."""
        if ticket_id in self.event_streams:
            await self.event_streams[ticket_id].put(event)
    
    def _get_decision(self, state: ITGraphState) -> str:
        """Extract decision from workflow state."""
        if state.get("final_decision"):
            return state["final_decision"]
        elif state.get("classification_decision"):
            decision = state["classification_decision"]
            if isinstance(decision, dict):
                return decision.get("decision", "pending")
            return str(decision)
        return "pending"
    
    def _get_plan_summary(self, state: ITGraphState) -> Optional[str]:
        """Extract plan summary from workflow state."""
        if state.get("execution_plan"):
            plan = state["execution_plan"]
            if isinstance(plan, dict) and "description" in plan:
                return plan["description"]
        return None
    
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
        
        # Run workflow in background
        background_tasks.add_task(app_state.run_workflow, ticket_id)
        
        # Return initial response
        return TicketResponse(
            ticket_id=ticket_id,
            decision="pending",
            plan_summary=None,
            status="pending",
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
        
        try:
            while True:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            # Client disconnected
            pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


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
        port=8000,
        reload=True,
        log_level="info"
    )
