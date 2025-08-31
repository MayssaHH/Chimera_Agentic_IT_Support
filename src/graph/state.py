"""
IT Support Workflow State Management

This module defines the state structure for the IT support workflow graph,
including both TypedDict and Pydantic models for flexible state handling.
"""

from typing import List, Optional, Dict, Any, Union
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# Enums for state values
class RequestStatus(str, Enum):
    """Status of the IT support request"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DENIED = "denied"
    ESCALATED = "escalated"
    ERROR = "error"


class DecisionType(str, Enum):
    """Classification decision types"""
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


class ActorType(str, Enum):
    """Types of actors in the workflow"""
    IT_AGENT = "it_agent"
    EMPLOYEE = "employee"
    MANAGER_APPROVAL = "manager_approval"
    SYSTEM = "system"


class PriorityLevel(str, Enum):
    """Priority levels for requests"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# TypedDict definitions for type safety
class UserRequest(TypedDict):
    """User's original IT support request"""
    request_id: str
    title: str
    description: str
    category: str
    priority: PriorityLevel
    submitted_at: datetime
    requested_by: str
    department: str
    urgency: str
    attachments: List[str]
    custom_fields: Dict[str, Any]


class Employee(TypedDict):
    """Employee information"""
    employee_id: str
    name: str
    email: str
    department: str
    role: str
    manager: str
    access_level: str
    location: str
    contact_info: Dict[str, str]


class RetrievedDocument(TypedDict):
    """Retrieved policy or procedure document"""
    doc_id: str
    title: str
    content: str
    source: str
    relevance_score: float
    retrieval_date: datetime
    document_type: str
    version: str
    last_updated: datetime
    metadata: Dict[str, Any]


class Citation(TypedDict):
    """Citation from policy documents"""
    source: str
    text: str
    relevance: str
    document_id: str
    page_number: Optional[int]
    section: Optional[str]


class RouterVerdict(TypedDict):
    """Model routing decision"""
    target_model: str
    reason: str
    escalation_needed: bool
    escalation_reason: Optional[str]
    model_capabilities: Dict[str, str]
    request_analysis: Dict[str, Any]
    routing_decision: Dict[str, Any]
    quality_metrics: Dict[str, Any]


class DecisionRecord(TypedDict):
    """Classification decision record"""
    decision: DecisionType
    citations: List[Citation]
    confidence: float
    needs_human: bool
    missing_fields: List[str]
    justification_brief: str
    decision_date: datetime
    decision_model: str
    policy_references: List[str]
    risk_assessment: Dict[str, Any]


class PlanStep(TypedDict):
    """Individual step in the execution plan"""
    step_id: str
    order: int
    description: str
    actor: ActorType
    actor_details: str
    required_tools: List[str]
    preconditions: List[str]
    postconditions: List[str]
    estimated_duration: int
    data_privacy_notes: str
    dependencies: List[str]
    automation_possible: bool
    fallback_actor: Optional[str]


class PlanRecord(TypedDict):
    """Execution plan record"""
    plan_id: str
    request_summary: str
    classification: DecisionType
    priority: PriorityLevel
    estimated_duration: float
    steps: List[PlanStep]
    approval_workflow: Dict[str, Any]
    email_draft: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    compliance_checklist: List[str]
    success_criteria: List[str]
    created_at: datetime
    last_updated: datetime


class TicketRecord(TypedDict):
    """IT support ticket record"""
    ticket_id: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str]
    priority: PriorityLevel
    category: str
    description: str
    resolution: Optional[str]
    resolution_date: Optional[datetime]
    time_spent: Optional[float]
    tags: List[str]
    custom_fields: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]


class HILPending(TypedDict):
    """Human-in-the-loop pending items"""
    item_id: str
    type: str
    description: str
    assigned_to: str
    priority: PriorityLevel
    created_at: datetime
    due_date: Optional[datetime]
    status: str
    escalation_path: List[str]
    timeout_hours: int


class ErrorRecord(TypedDict):
    """Error record for workflow issues"""
    error_id: str
    timestamp: datetime
    error_type: str
    message: str
    stack_trace: Optional[str]
    context: Dict[str, Any]
    severity: str
    resolved: bool
    resolution_notes: Optional[str]


# Main state structure using TypedDict
class ITGraphState(TypedDict):
    """Main state structure for IT support workflow graph"""
    user_request: UserRequest
    employee: Employee
    retrieved_docs: List[RetrievedDocument]
    citations: List[Citation]
    router_verdict: RouterVerdict
    decision_record: DecisionRecord
    plan_record: PlanRecord
    ticket_record: TicketRecord
    hil_pending: List[HILPending]
    errors: List[ErrorRecord]


# Pydantic models for validation and serialization
class UserRequestModel(BaseModel):
    """Pydantic model for user request"""
    request_id: str = Field(..., description="Unique request identifier")
    title: str = Field(..., description="Request title")
    description: str = Field(..., description="Detailed request description")
    category: str = Field(..., description="Request category")
    priority: PriorityLevel = Field(..., description="Request priority level")
    submitted_at: datetime = Field(default_factory=datetime.now, description="Submission timestamp")
    requested_by: str = Field(..., description="Requesting employee ID")
    department: str = Field(..., description="Department making the request")
    urgency: str = Field(..., description="Urgency level")
    attachments: List[str] = Field(default_factory=list, description="Attached files")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Additional custom fields")


class EmployeeModel(BaseModel):
    """Pydantic model for employee information"""
    employee_id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Employee full name")
    email: str = Field(..., description="Employee email address")
    department: str = Field(..., description="Employee department")
    role: str = Field(..., description="Employee role/title")
    manager: str = Field(..., description="Manager's employee ID")
    access_level: str = Field(..., description="Current access level")
    location: str = Field(..., description="Employee location")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Additional contact information")


class RetrievedDocumentModel(BaseModel):
    """Pydantic model for retrieved documents"""
    doc_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    source: str = Field(..., description="Document source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    retrieval_date: datetime = Field(default_factory=datetime.now, description="Retrieval timestamp")
    document_type: str = Field(..., description="Type of document")
    version: str = Field(..., description="Document version")
    last_updated: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CitationModel(BaseModel):
    """Pydantic model for citations"""
    source: str = Field(..., description="Citation source")
    text: str = Field(..., description="Cited text")
    relevance: str = Field(..., description="Relevance explanation")
    document_id: str = Field(..., description="Source document ID")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    section: Optional[str] = Field(None, description="Section if applicable")


class RouterVerdictModel(BaseModel):
    """Pydantic model for router verdict"""
    target_model: str = Field(..., description="Selected target model")
    reason: str = Field(..., description="Reason for model selection")
    escalation_needed: bool = Field(..., description="Whether escalation is needed")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")
    model_capabilities: Dict[str, str] = Field(..., description="Model capability information")
    request_analysis: Dict[str, Any] = Field(..., description="Request analysis results")
    routing_decision: Dict[str, Any] = Field(..., description="Routing decision details")
    quality_metrics: Dict[str, Any] = Field(..., description="Quality metrics")


class DecisionRecordModel(BaseModel):
    """Pydantic model for decision record"""
    decision: DecisionType = Field(..., description="Classification decision")
    citations: List[CitationModel] = Field(..., description="Supporting citations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    needs_human: bool = Field(..., description="Whether human review is needed")
    missing_fields: List[str] = Field(default_factory=list, description="Missing required fields")
    justification_brief: str = Field(..., description="Brief justification")
    decision_date: datetime = Field(default_factory=datetime.now, description="Decision timestamp")
    decision_model: str = Field(..., description="Model that made the decision")
    policy_references: List[str] = Field(default_factory=list, description="Referenced policies")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk assessment")


class PlanStepModel(BaseModel):
    """Pydantic model for plan step"""
    step_id: str = Field(..., description="Unique step identifier")
    order: int = Field(..., ge=1, description="Step execution order")
    description: str = Field(..., description="Step description")
    actor: ActorType = Field(..., description="Actor type for this step")
    actor_details: str = Field(..., description="Specific actor details")
    required_tools: List[str] = Field(..., description="Required tools for this step")
    preconditions: List[str] = Field(default_factory=list, description="Step preconditions")
    postconditions: List[str] = Field(default_factory=list, description="Step postconditions")
    estimated_duration: int = Field(..., ge=1, description="Estimated duration in minutes")
    data_privacy_notes: str = Field(..., description="Data privacy considerations")
    dependencies: List[str] = Field(default_factory=list, description="Step dependencies")
    automation_possible: bool = Field(..., description="Whether automation is possible")
    fallback_actor: Optional[str] = Field(None, description="Fallback actor if primary unavailable")


class PlanRecordModel(BaseModel):
    """Pydantic model for plan record"""
    plan_id: str = Field(..., description="Unique plan identifier")
    request_summary: str = Field(..., description="Request summary")
    classification: DecisionType = Field(..., description="Request classification")
    priority: PriorityLevel = Field(..., description="Request priority")
    estimated_duration: float = Field(..., ge=0.0, description="Estimated duration in hours")
    steps: List[PlanStepModel] = Field(..., description="Execution steps")
    approval_workflow: Dict[str, Any] = Field(..., description="Approval workflow details")
    email_draft: Dict[str, Any] = Field(..., description="Email draft for approvals")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment")
    compliance_checklist: List[str] = Field(default_factory=list, description="Compliance checklist")
    success_criteria: List[str] = Field(default_factory=list, description="Success criteria")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


class TicketRecordModel(BaseModel):
    """Pydantic model for ticket record"""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    status: RequestStatus = Field(..., description="Ticket status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    assigned_to: Optional[str] = Field(None, description="Assigned agent")
    priority: PriorityLevel = Field(..., description="Ticket priority")
    category: str = Field(..., description="Ticket category")
    description: str = Field(..., description="Ticket description")
    resolution: Optional[str] = Field(None, description="Resolution details")
    resolution_date: Optional[datetime] = Field(None, description="Resolution timestamp")
    time_spent: Optional[float] = Field(None, description="Time spent on ticket")
    tags: List[str] = Field(default_factory=list, description="Ticket tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list, description="Audit trail")


class HILPendingModel(BaseModel):
    """Pydantic model for HIL pending items"""
    item_id: str = Field(..., description="Unique item identifier")
    type: str = Field(..., description="Item type")
    description: str = Field(..., description="Item description")
    assigned_to: str = Field(..., description="Assigned person")
    priority: PriorityLevel = Field(..., description="Item priority")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date")
    status: str = Field(..., description="Current status")
    escalation_path: List[str] = Field(default_factory=list, description="Escalation path")
    timeout_hours: int = Field(..., ge=1, description="Timeout in hours")


class ErrorRecordModel(BaseModel):
    """Pydantic model for error records"""
    error_id: str = Field(..., description="Unique error identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")
    severity: str = Field(..., description="Error severity")
    resolved: bool = Field(False, description="Whether error is resolved")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")


# Main Pydantic state model
class ITGraphStateModel(BaseModel):
    """Main Pydantic state model for IT support workflow graph"""
    user_request: UserRequestModel = Field(..., description="User's original request")
    employee: EmployeeModel = Field(..., description="Employee information")
    retrieved_docs: List[RetrievedDocumentModel] = Field(default_factory=list, description="Retrieved documents")
    citations: List[CitationModel] = Field(default_factory=list, description="Policy citations")
    router_verdict: RouterVerdictModel = Field(..., description="Model routing decision")
    decision_record: DecisionRecordModel = Field(..., description="Classification decision")
    plan_record: PlanRecordModel = Field(..., description="Execution plan")
    ticket_record: TicketRecordModel = Field(..., description="IT support ticket")
    hil_pending: List[HILPendingModel] = Field(default_factory=list, description="Human-in-loop pending items")
    errors: List[ErrorRecordModel] = Field(default_factory=list, description="Error records")

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Utility functions for state management
def create_empty_state() -> ITGraphState:
    """Create an empty state structure with default values"""
    return {
        "user_request": {},
        "employee": {},
        "retrieved_docs": [],
        "citations": [],
        "router_verdict": {},
        "decision_record": {},
        "plan_record": {},
        "ticket_record": {},
        "hil_pending": [],
        "errors": []
    }


def validate_state(state: ITGraphState) -> bool:
    """Validate state structure and required fields"""
    required_keys = [
        "user_request", "employee", "retrieved_docs", "citations",
        "router_verdict", "decision_record", "plan_record", 
        "ticket_record", "hil_pending", "errors"
    ]
    
    for key in required_keys:
        if key not in state:
            return False
    
    return True


def get_state_summary(state: ITGraphState) -> Dict[str, Any]:
    """Get a summary of the current state"""
    return {
        "request_id": state.get("user_request", {}).get("request_id"),
        "status": state.get("ticket_record", {}).get("status"),
        "decision": state.get("decision_record", {}).get("decision"),
        "plan_steps": len(state.get("plan_record", {}).get("steps", [])),
        "pending_hil": len(state.get("hil_pending", [])),
        "error_count": len(state.get("errors", [])),
        "last_updated": state.get("ticket_record", {}).get("updated_at")
    }
