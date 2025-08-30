"""Domain schemas for Local IT Support."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, HttpUrl


class RequestDecision(str, Enum):
    """Enum for request decisions."""
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"


class TicketStatus(str, Enum):
    """Enum for ticket status."""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Employee(BaseModel):
    """Employee information."""
    id: str = Field(..., description="Unique employee identifier")
    employee_id: str = Field(..., description="Employee ID number")
    first_name: str = Field(..., description="Employee first name")
    last_name: str = Field(..., description="Employee last name")
    email: EmailStr = Field(..., description="Employee email address")
    department: str = Field(..., description="Employee department")
    job_title: str = Field(..., description="Employee job title")
    manager_id: Optional[str] = Field(None, description="Manager's employee ID")
    hire_date: datetime = Field(..., description="Employee hire date")
    is_active: bool = Field(True, description="Whether employee is active")
    permissions: List[str] = Field(default_factory=list, description="Employee permissions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRequest(BaseModel):
    """User request for IT support or access."""
    id: str = Field(..., description="Unique request identifier")
    employee_id: str = Field(..., description="Requesting employee ID")
    request_type: str = Field(..., description="Type of request (access, software, hardware, etc.)")
    title: str = Field(..., description="Request title")
    description: str = Field(..., description="Detailed request description")
    priority: str = Field("medium", description="Request priority (low, medium, high, urgent)")
    urgency: str = Field("normal", description="Request urgency (normal, urgent, critical)")
    business_justification: Optional[str] = Field(None, description="Business justification for request")
    requested_date: datetime = Field(default_factory=datetime.utcnow)
    desired_completion_date: Optional[datetime] = Field(None, description="Desired completion date")
    status: RequestDecision = Field(RequestDecision.REQUIRES_APPROVAL, description="Request decision status")
    approved_by: Optional[str] = Field(None, description="Approver employee ID")
    approved_date: Optional[datetime] = Field(None, description="Approval date")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if denied")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyDoc(BaseModel):
    """IT policy document."""
    id: str = Field(..., description="Unique policy identifier")
    title: str = Field(..., description="Policy title")
    version: str = Field(..., description="Policy version")
    category: str = Field(..., description="Policy category (security, access, etc.)")
    content: str = Field(..., description="Policy content")
    summary: Optional[str] = Field(None, description="Policy summary")
    effective_date: datetime = Field(..., description="Policy effective date")
    expiry_date: Optional[datetime] = Field(None, description="Policy expiry date")
    approved_by: str = Field(..., description="Policy approver")
    is_active: bool = Field(True, description="Whether policy is active")
    tags: List[str] = Field(default_factory=list, description="Policy tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionRecord(BaseModel):
    """Record of a decision made by the system or human."""
    id: str = Field(..., description="Unique decision identifier")
    request_id: str = Field(..., description="Related request ID")
    decision_type: str = Field(..., description="Type of decision made")
    decision: RequestDecision = Field(..., description="Decision outcome")
    reasoning: str = Field(..., description="Reasoning behind the decision")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")
    policy_references: List[str] = Field(default_factory=list, description="Referenced policy IDs")
    risk_assessment: Optional[str] = Field(None, description="Risk assessment details")
    approver_id: Optional[str] = Field(None, description="Human approver ID if applicable")
    automated: bool = Field(True, description="Whether decision was automated")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PlanStep(BaseModel):
    """Individual step in an execution plan."""
    id: str = Field(..., description="Unique step identifier")
    step_number: int = Field(..., description="Step sequence number")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    action_type: str = Field(..., description="Type of action (tool_call, approval, notification, etc.)")
    tool_name: Optional[str] = Field(None, description="Tool to be used if applicable")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    dependencies: List[str] = Field(default_factory=list, description="Dependent step IDs")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    assigned_to: Optional[str] = Field(None, description="Employee assigned to this step")
    status: str = Field("pending", description="Step status (pending, in_progress, completed, failed)")
    result: Optional[Dict[str, Any]] = Field(None, description="Step execution result")
    error_message: Optional[str] = Field(None, description="Error message if step failed")
    completed_at: Optional[datetime] = Field(None, description="Step completion timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PlanRecord(BaseModel):
    """Record of an execution plan."""
    id: str = Field(..., description="Unique plan identifier")
    request_id: str = Field(..., description="Related request ID")
    plan_type: str = Field(..., description="Type of plan (access_grant, software_install, etc.)")
    title: str = Field(..., description="Plan title")
    description: str = Field(..., description="Plan description")
    steps: List[PlanStep] = Field(..., description="Plan execution steps")
    status: str = Field("draft", description="Plan status (draft, active, completed, cancelled)")
    priority: str = Field("medium", description="Plan priority")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion date")
    actual_completion: Optional[datetime] = Field(None, description="Actual completion date")
    created_by: str = Field(..., description="Plan creator ID")
    approved_by: Optional[str] = Field(None, description="Plan approver ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TicketRecord(BaseModel):
    """IT support ticket record."""
    id: str = Field(..., description="Unique ticket identifier")
    ticket_number: str = Field(..., description="Ticket number")
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    requester_id: str = Field(..., description="Requesting employee ID")
    assignee_id: Optional[str] = Field(None, description="Assigned employee ID")
    status: TicketStatus = Field(TicketStatus.NEW, description="Ticket status")
    priority: str = Field("medium", description="Ticket priority")
    category: str = Field(..., description="Ticket category")
    subcategory: Optional[str] = Field(None, description="Ticket subcategory")
    tags: List[str] = Field(default_factory=list, description="Ticket tags")
    related_requests: List[str] = Field(default_factory=list, description="Related request IDs")
    related_plans: List[str] = Field(default_factory=list, description="Related plan IDs")
    jira_issue_key: Optional[str] = Field(None, description="JIRA issue key if synced")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")


class ToolCall(BaseModel):
    """Record of a tool execution."""
    id: str = Field(..., description="Unique tool call identifier")
    plan_step_id: str = Field(..., description="Related plan step ID")
    tool_name: str = Field(..., description="Tool name")
    tool_version: Optional[str] = Field(None, description="Tool version")
    parameters: Dict[str, Any] = Field(..., description="Tool input parameters")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool execution result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    status: str = Field("pending", description="Tool call status (pending, running, completed, failed)")
    started_at: Optional[datetime] = Field(None, description="Execution start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Execution completion timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    """Citation or reference to a source."""
    id: str = Field(..., description="Unique citation identifier")
    source_type: str = Field(..., description="Source type (policy, knowledge_base, external, etc.)")
    source_id: str = Field(..., description="Source identifier")
    source_title: str = Field(..., description="Source title")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL if applicable")
    content: str = Field(..., description="Cited content")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Content relevance score")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    section: Optional[str] = Field(None, description="Section if applicable")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RiskFlag(BaseModel):
    """Risk assessment flag."""
    id: str = Field(..., description="Unique risk flag identifier")
    request_id: str = Field(..., description="Related request ID")
    risk_type: str = Field(..., description="Type of risk (security, compliance, operational, etc.)")
    severity: str = Field(..., description="Risk severity (low, medium, high, critical)")
    description: str = Field(..., description="Risk description")
    impact: str = Field(..., description="Potential impact description")
    mitigation: Optional[str] = Field(None, description="Mitigation strategy")
    is_acknowledged: bool = Field(False, description="Whether risk has been acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Employee who acknowledged the risk")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgement timestamp")
    is_resolved: bool = Field(False, description="Whether risk has been resolved")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RouterVerdict(BaseModel):
    """Routing decision verdict."""
    id: str = Field(..., description="Unique routing verdict identifier")
    request_id: str = Field(..., description="Related request ID")
    routing_decision: str = Field(..., description="Routing decision (auto_approve, human_review, escalate, etc.)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in routing decision")
    reasoning: str = Field(..., description="Reasoning for routing decision")
    assigned_queue: Optional[str] = Field(None, description="Assigned queue or team")
    assigned_priority: str = Field("medium", description="Assigned priority level")
    estimated_processing_time: Optional[int] = Field(None, description="Estimated processing time in hours")
    requires_approval: bool = Field(False, description="Whether approval is required")
    approval_level: Optional[str] = Field(None, description="Required approval level")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation if applicable")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
