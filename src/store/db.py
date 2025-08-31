"""Database models and repository functions using SQLModel."""

import uuid
from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from contextlib import contextmanager

from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import text

from ..config import settings


class Decision(SQLModel, table=True):
    """Decision table for storing AI-generated decisions."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ticket_id: str = Field(index=True)
    decision_text: str
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(description="Employee ID who created the decision")
    status: str = Field(default="active", description="active, archived, rejected")


class Plan(SQLModel, table=True):
    """Plan table for storing AI-generated action plans."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    plan_id: str = Field(unique=True, index=True, description="Unique plan identifier")
    ticket_id: str = Field(index=True)
    request_id: str = Field(index=True, description="Related request ID")
    plan_title: str
    plan_description: str
    request_summary: str
    classification: str = Field(description="ALLOWED, DENIED, REQUIRES_APPROVAL")
    priority: str = Field(default="medium", description="low, medium, high, critical")
    estimated_duration: float = Field(description="Estimated duration in hours")
    steps: str = Field(description="JSON string of plan steps")
    approval_workflow: str = Field(description="JSON string of approval workflow")
    email_draft: str = Field(description="JSON string of email draft")
    risk_assessment: str = Field(description="JSON string of risk assessment")
    compliance_checklist: str = Field(description="JSON string of compliance checklist")
    success_criteria: str = Field(description="JSON string of success criteria")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(description="Employee ID who created the plan")
    status: str = Field(default="draft", description="draft, approved, in_progress, completed, cancelled")


class Ticket(SQLModel, table=True):
    """Ticket table for storing IT support tickets."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    description: str
    category: str = Field(description="hardware, software, network, access, other")
    priority: str = Field(default="medium", description="low, medium, high, critical")
    status: str = Field(default="open", description="open, in_progress, resolved, closed, cancelled")
    assigned_to: Optional[str] = Field(default=None, description="Employee ID assigned to ticket")
    created_by: str = Field(description="Employee ID who created the ticket")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None, description="Comma-separated tags")


class ToolCall(SQLModel, table=True):
    """Tool call table for storing AI tool execution logs."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ticket_id: str = Field(index=True)
    tool_name: str
    tool_input: str
    tool_output: str
    execution_time_ms: int = Field(description="Execution time in milliseconds")
    success: bool
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(description="Employee ID who initiated the tool call")


# Database engine and session management
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
    return _engine


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    engine = get_engine()
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def init_db():
    """Initialize database tables. Creates tables on first run."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


# Repository functions

def save_decision(decision: Decision) -> Decision:
    """Save a decision to the database."""
    with get_db_session() as session:
        session.add(decision)
        session.commit()
        session.refresh(decision)
        return decision


def save_plan(plan: Plan) -> Plan:
    """Save a plan to the database."""
    with get_db_session() as session:
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan


def save_plan_from_record(plan_record: Dict[str, Any], ticket_id: str, request_id: str, created_by: str) -> Plan:
    """Save a plan from PlanRecord dictionary to the database."""
    import json
    
    plan = Plan(
        plan_id=plan_record.get('plan_id', f"plan_{uuid.uuid4().hex[:8].upper()}"),
        ticket_id=ticket_id,
        request_id=request_id,
        plan_title=plan_record.get('request_summary', ''),
        plan_description=plan_record.get('description', ''),
        request_summary=plan_record.get('request_summary', ''),
        classification=plan_record.get('classification', 'REQUIRES_APPROVAL'),
        priority=plan_record.get('priority', 'medium'),
        estimated_duration=plan_record.get('estimated_duration', 0.0),
        steps=json.dumps(plan_record.get('steps', [])),
        approval_workflow=json.dumps(plan_record.get('approval_workflow', {})),
        email_draft=json.dumps(plan_record.get('email_draft', {})),
        risk_assessment=json.dumps(plan_record.get('risk_assessment', {})),
        compliance_checklist=json.dumps(plan_record.get('compliance_checklist', [])),
        success_criteria=json.dumps(plan_record.get('success_criteria', [])),
        created_by=created_by
    )
    
    return save_plan(plan)


def save_ticket(ticket: Ticket) -> Ticket:
    """Save a ticket to the database."""
    with get_db_session() as session:
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return ticket


def update_ticket_status(ticket_id: str, new_status: str, resolution_notes: Optional[str] = None) -> Optional[Ticket]:
    """Update ticket status and optionally add resolution notes."""
    with get_db_session() as session:
        ticket = session.get(Ticket, ticket_id)
        if ticket:
            ticket.status = new_status
            ticket.updated_at = datetime.utcnow()
            
            if new_status in ["resolved", "closed"] and resolution_notes:
                ticket.resolution_notes = resolution_notes
                ticket.resolved_at = datetime.utcnow()
            
            session.commit()
            session.refresh(ticket)
            return ticket
        return None


def list_tickets(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Ticket]:
    """List tickets with optional filtering by employee, status, or category."""
    with get_db_session() as session:
        query = select(Ticket)
        
        if employee_id:
            query = query.where(
                (Ticket.assigned_to == employee_id) | (Ticket.created_by == employee_id)
            )
        
        if status:
            query = query.where(Ticket.status == status)
            
        if category:
            query = query.where(Ticket.category == category)
        
        query = query.order_by(Ticket.created_at.desc()).limit(limit).offset(offset)
        
        result = session.exec(query)
        return list(result.all())


def get_ticket(ticket_id: str) -> Optional[Ticket]:
    """Get a specific ticket by ID."""
    with get_db_session() as session:
        return session.get(Ticket, ticket_id)


def get_decisions_for_ticket(ticket_id: str) -> List[Decision]:
    """Get all decisions for a specific ticket."""
    with get_db_session() as session:
        query = select(Decision).where(Decision.ticket_id == ticket_id).order_by(Decision.created_at.desc())
        result = session.exec(query)
        return list(result.all())


def get_plans_for_ticket(ticket_id: str) -> List[Plan]:
    """Get all plans for a specific ticket."""
    with get_db_session() as session:
        query = select(Plan).where(Plan.ticket_id == ticket_id).order_by(Plan.created_at.desc())
        result = session.exec(query)
        return list(result.all())


def get_tool_calls_for_ticket(ticket_id: str) -> List[ToolCall]:
    """Get all tool calls for a specific ticket."""
    with get_db_session() as session:
        query = select(ToolCall).where(ToolCall.ticket_id == ticket_id).order_by(ToolCall.created_at.desc())
        result = session.exec(query)
        return list(result.all())


def search_tickets(
    search_term: str,
    employee_id: Optional[str] = None,
    limit: int = 50
) -> List[Ticket]:
    """Search tickets by title, description, or tags."""
    with get_db_session() as session:
        query = select(Ticket).where(
            (Ticket.title.contains(search_term)) |
            (Ticket.description.contains(search_term)) |
            (Ticket.tags.contains(search_term))
        )
        
        if employee_id:
            query = query.where(
                (Ticket.assigned_to == employee_id) | (Ticket.created_by == employee_id)
            )
        
        query = query.order_by(Ticket.created_at.desc()).limit(limit)
        result = session.exec(query)
        return list(result.all())


def get_ticket_statistics(employee_id: Optional[str] = None) -> dict:
    """Get ticket statistics for reporting."""
    with get_db_session() as session:
        base_query = select(Ticket)
        if employee_id:
            base_query = base_query.where(
                (Ticket.assigned_to == employee_id) | (Ticket.created_by == employee_id)
            )
        
        # Total tickets
        total_result = session.exec(base_query)
        total_tickets = len(list(total_result.all()))
        
        # Status breakdown
        status_query = base_query.add_columns(Ticket.status)
        status_result = session.exec(status_query)
        status_counts = {}
        for ticket, status in status_result:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Category breakdown
        category_query = base_query.add_columns(Ticket.category)
        category_result = session.exec(category_query)
        category_counts = {}
        for ticket, category in category_result:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_tickets": total_tickets,
            "status_breakdown": status_counts,
            "category_breakdown": category_counts
        }
