"""
Response schemas for LLM calls in the IT Support workflow.

These Pydantic models define the expected structure of LLM responses
for different workflow nodes, ensuring consistent and validated output.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Classifier Response Schema
class Citation(BaseModel):
    """Citation from policy documents."""
    source: str = Field(..., description="Name of the policy document")
    text: str = Field(..., description="Exact quote from the policy")
    relevance: str = Field(..., description="How this citation supports the decision")


class ClassifierResponse(BaseModel):
    """Response from the classifier LLM."""
    decision: Literal["ALLOWED", "DENIED", "REQUIRES_APPROVAL"] = Field(
        ..., description="Classification decision"
    )
    citations: List[Citation] = Field(
        ..., description="Array of at least one citation", min_items=1
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    needs_human: bool = Field(
        ..., description="Whether human review is recommended"
    )
    missing_fields: List[str] = Field(
        default_factory=list, description="Required information that's missing"
    )
    justification_brief: str = Field(
        ..., description="Clear explanation of the decision based on cited policies"
    )


# Router Response Schema
class ModelCapabilities(BaseModel):
    """Model capabilities assessment."""
    complexity_handling: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ..., description="Model's ability to handle complexity"
    )
    policy_knowledge: Literal["BASIC", "COMPREHENSIVE", "EXPERT"] = Field(
        ..., description="Model's policy knowledge level"
    )
    reasoning_ability: Literal["SIMPLE", "MODERATE", "ADVANCED"] = Field(
        ..., description="Model's reasoning capability"
    )
    resource_cost: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ..., description="Resource cost of using this model"
    )


class RequestAnalysis(BaseModel):
    """Analysis of the request requirements."""
    complexity: Literal["SIMPLE", "MODERATE", "COMPLEX"] = Field(
        ..., description="Request complexity level"
    )
    policy_requirements: Literal["BASIC", "STANDARD", "ADVANCED"] = Field(
        ..., description="Policy requirements level"
    )
    confidence_required: float = Field(
        ..., ge=0.0, le=1.0, description="Minimum confidence required"
    )
    retrieval_quality: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Quality of retrieved policy information"
    )


class RoutingDecision(BaseModel):
    """Routing decision details."""
    primary_model: str = Field(..., description="Primary model to use")
    fallback_model: Optional[str] = Field(None, description="Alternative model if primary fails")
    escalation_path: List[str] = Field(
        default_factory=list, description="Path for escalation if needed"
    )
    timeout_seconds: int = Field(..., description="Timeout for model response")


class QualityMetrics(BaseModel):
    """Quality and performance metrics."""
    expected_accuracy: float = Field(..., ge=0.0, le=1.0, description="Expected accuracy")
    response_time_estimate: str = Field(..., description="Estimated response time")
    resource_efficiency: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Resource efficiency rating"
    )


class RouterResponse(BaseModel):
    """Response from the router LLM."""
    router_id: str = Field(..., description="Unique router identifier")
    request_id: str = Field(..., description="Request identifier")
    target_model: str = Field(..., description="Selected model name")
    reason: str = Field(..., description="Clear explanation of model selection")
    escalation_needed: bool = Field(..., description="Whether escalation is needed")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")
    model_capabilities: ModelCapabilities = Field(..., description="Model capabilities assessment")
    request_analysis: RequestAnalysis = Field(..., description="Request requirements analysis")
    routing_decision: RoutingDecision = Field(..., description="Routing decision details")
    quality_metrics: QualityMetrics = Field(..., description="Quality and performance metrics")


# Planner Response Schema
class PlanStep(BaseModel):
    """Individual step in an execution plan."""
    step_id: str = Field(..., description="Unique step identifier")
    order: int = Field(..., description="Step sequence number")
    description: str = Field(..., description="Clear description of what this step accomplishes")
    actor: Literal["it_agent", "employee", "manager_approval", "system"] = Field(
        ..., description="Who or what will execute this step"
    )
    actor_details: Optional[str] = Field(None, description="Specific role or person if applicable")
    required_tools: List[str] = Field(
        default_factory=list, description="Tools required for this step"
    )
    preconditions: List[str] = Field(
        default_factory=list, description="Conditions that must be met before this step"
    )
    postconditions: List[str] = Field(
        default_factory=list, description="Expected outcomes after this step"
    )
    estimated_duration: str = Field(..., description="Estimated time in minutes")
    data_privacy_notes: Optional[str] = Field(None, description="Data handling considerations")
    dependencies: List[str] = Field(
        default_factory=list, description="Dependent step IDs"
    )
    automation_possible: bool = Field(..., description="Whether this step can be automated")
    fallback_actor: Optional[str] = Field(None, description="Alternative actor if primary unavailable")


class ApprovalWorkflow(BaseModel):
    """Approval workflow details."""
    needed: bool = Field(..., description="Whether approval is needed")
    approvers: List[str] = Field(
        default_factory=list, description="Required approver roles"
    )
    approval_order: Literal["sequential", "parallel"] = Field(
        ..., description="Approval sequence type"
    )
    escalation_path: List[str] = Field(
        default_factory=list, description="Escalation path if approval fails"
    )
    timeout_hours: int = Field(..., description="Approval timeout in hours")


class EmailDraft(BaseModel):
    """Email draft for approval requests."""
    subject: str = Field(..., description="Subject line for approval request")
    recipients: List[str] = Field(..., description="Primary recipients")
    cc: List[str] = Field(default_factory=list, description="CC recipients")
    body: str = Field(..., description="Professional email body requesting approval")
    attachments: List[str] = Field(
        default_factory=list, description="Required attachments"
    )
    urgency_note: Optional[str] = Field(None, description="Urgency indicators or deadlines")


class RiskAssessment(BaseModel):
    """Risk assessment details."""
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Overall risk level")
    risks: List[str] = Field(..., description="Identified risks")
    mitigation_strategies: List[str] = Field(..., description="Risk mitigation strategies")
    rollback_plan: str = Field(..., description="How to undo changes if needed")


class PlannerResponse(BaseModel):
    """Response from the planner LLM."""
    plan_id: str = Field(..., description="Unique plan identifier")
    request_summary: str = Field(..., description="Brief description of what needs to be done")
    classification: Literal["ALLOWED", "DENIED", "REQUIRES_APPROVAL"] = Field(
        ..., description="Classification from classifier"
    )
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ..., description="Plan priority level"
    )
    estimated_duration: str = Field(..., description="Estimated time in hours")
    steps: List[PlanStep] = Field(..., description="Execution plan steps", min_items=1)
    approval_workflow: ApprovalWorkflow = Field(..., description="Approval requirements")
    email_draft: Optional[EmailDraft] = Field(None, description="Email draft for approval")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment details")
    compliance_checklist: List[str] = Field(
        default_factory=list, description="Compliance verification items"
    )
    success_criteria: List[str] = Field(
        default_factory=list, description="Success criteria for the plan"
    )


# IT Agent Response Schema
class ExecutableAction(BaseModel):
    """Executable action for IT agents."""
    action_id: str = Field(..., description="Unique action identifier")
    step_reference: str = Field(..., description="Reference to plan step")
    tool: Literal["email", "jira", "directory", "system", "manual"] = Field(
        ..., description="Tool to be used"
    )
    action_type: Literal["send", "create", "update", "query", "execute"] = Field(
        ..., description="Type of action to perform"
    )
    target: str = Field(..., description="Specific target or recipient")
    parameters: Dict[str, Any] = Field(..., description="Action parameters")
    preconditions_met: bool = Field(..., description="Whether preconditions are satisfied")
    execution_notes: Optional[str] = Field(None, description="Special instructions or context")
    estimated_duration: str = Field(..., description="Estimated time in minutes")
    automation_level: Literal["fully_automated", "semi_automated", "manual"] = Field(
        ..., description="Level of automation possible"
    )


class UserGuideStep(BaseModel):
    """Step in the user guide."""
    step_number: int = Field(..., description="Step sequence number")
    title: str = Field(..., description="Clear action title")
    description: str = Field(..., description="Detailed explanation of what to do")
    estimated_time: str = Field(..., description="Time estimate")
    required_materials: List[str] = Field(
        default_factory=list, description="Required materials or information"
    )
    instructions: List[str] = Field(..., description="Specific instructions", min_items=1)
    examples: Optional[str] = Field(None, description="Example of what this should look like")
    contact_info: Optional[str] = Field(None, description="Who to contact for help")
    deadline: Optional[str] = Field(None, description="When this needs to be completed")


class UserGuide(BaseModel):
    """User guide for employee actions."""
    title: str = Field(..., description="Guide title")
    introduction: str = Field(..., description="Brief explanation of what needs to be done")
    steps: List[UserGuideStep] = Field(..., description="Steps to complete", min_items=1)
    completion_criteria: List[str] = Field(
        default_factory=list, description="Criteria for completion"
    )
    next_steps: str = Field(..., description="What happens after completion")


class CompletionArtifact(BaseModel):
    """Artifact for completion documentation."""
    type: Literal["document", "log", "screenshot", "approval", "confirmation"] = Field(
        ..., description="Type of artifact"
    )
    name: str = Field(..., description="Descriptive name of the artifact")
    description: str = Field(..., description="What this artifact proves or documents")
    content: str = Field(..., description="Actual content or reference to content")
    privacy_level: Literal["public", "internal", "confidential", "restricted"] = Field(
        ..., description="Privacy level of the artifact"
    )


class CompletionMetrics(BaseModel):
    """Metrics for completion tracking."""
    total_duration: str = Field(..., description="Actual time taken")
    steps_completed: int = Field(..., description="Number of steps completed")
    automation_used: int = Field(..., description="Number of automated steps")
    manual_steps: int = Field(..., description="Number of manual steps")
    compliance_verified: bool = Field(..., description="Whether compliance was verified")


class TicketUpdate(BaseModel):
    """Ticket status update."""
    status: Literal["RESOLVED", "WAITING_FOR_USER", "ESCALATED"] = Field(
        ..., description="New ticket status"
    )
    resolution: str = Field(..., description="Brief description of resolution")
    next_actions: Optional[str] = Field(None, description="Follow-up actions needed")
    knowledge_base_entry: Optional[str] = Field(None, description="Suggested KB article")


class CompletionPackage(BaseModel):
    """Completion package for ticket closure."""
    summary_message: str = Field(..., description="Professional summary of accomplishments")
    artifacts: List[CompletionArtifact] = Field(
        default_factory=list, description="Completion artifacts"
    )
    metrics: CompletionMetrics = Field(..., description="Completion metrics")
    ticket_update: TicketUpdate = Field(..., description="Ticket status update")


class ITAgentResponse(BaseModel):
    """Response from the IT agent LLM."""
    execution_id: str = Field(..., description="Unique execution identifier")
    plan_reference: str = Field(..., description="Reference to the plan")
    status: Literal["READY_TO_EXECUTE", "IN_PROGRESS", "COMPLETED", "BLOCKED"] = Field(
        ..., description="Execution status"
    )
    executable_actions: List[ExecutableAction] = Field(
        ..., description="Actions to execute", min_items=1
    )
    user_guide: UserGuide = Field(..., description="Guide for employee actions")
    completion_package: CompletionPackage = Field(..., description="Completion documentation")


# Generic Error Response Schema
class ErrorResponse(BaseModel):
    """Generic error response."""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")


# Validation Response Schema
class ValidationResponse(BaseModel):
    """Response indicating validation success or failure."""
    valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")
