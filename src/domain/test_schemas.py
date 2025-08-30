"""Test the domain schemas."""

from datetime import datetime, timedelta
from .schemas import (
    RequestDecision, TicketStatus, Employee, UserRequest, PolicyDoc,
    DecisionRecord, PlanStep, PlanRecord, TicketRecord, ToolCall,
    Citation, RiskFlag, RouterVerdict
)


def test_enums():
    """Test the enum values."""
    print("Testing Enums...")
    
    # Test RequestDecision enum
    assert RequestDecision.ALLOWED == "allowed"
    assert RequestDecision.DENIED == "denied"
    assert RequestDecision.REQUIRES_APPROVAL == "requires_approval"
    print("✓ RequestDecision enum values correct")
    
    # Test TicketStatus enum
    assert TicketStatus.NEW == "new"
    assert TicketStatus.IN_PROGRESS == "in_progress"
    assert TicketStatus.RESOLVED == "resolved"
    assert TicketStatus.CLOSED == "closed"
    print("✓ TicketStatus enum values correct")


def test_employee_schema():
    """Test Employee schema creation."""
    print("\nTesting Employee Schema...")
    
    employee = Employee(
        id="emp_001",
        employee_id="E001",
        first_name="John",
        last_name="Doe",
        email="john.doe@company.com",
        department="IT",
        job_title="Software Engineer",
        hire_date=datetime.now() - timedelta(days=365)
    )
    
    assert employee.first_name == "John"
    assert employee.last_name == "Doe"
    assert employee.department == "IT"
    assert employee.is_active is True
    print("✓ Employee schema created successfully")


def test_user_request_schema():
    """Test UserRequest schema creation."""
    print("\nTesting UserRequest Schema...")
    
    request = UserRequest(
        id="req_001",
        employee_id="emp_001",
        request_type="software_access",
        title="Request for VS Code Access",
        description="Need VS Code for development work",
        priority="high",
        business_justification="Required for daily development tasks"
    )
    
    assert request.request_type == "software_access"
    assert request.priority == "high"
    assert request.status == RequestDecision.REQUIRES_APPROVAL
    print("✓ UserRequest schema created successfully")


def test_policy_doc_schema():
    """Test PolicyDoc schema creation."""
    print("\nTesting PolicyDoc Schema...")
    
    policy = PolicyDoc(
        id="pol_001",
        title="Software Installation Policy",
        version="1.0",
        category="security",
        content="Only approved software can be installed...",
        effective_date=datetime.now(),
        approved_by="admin_001"
    )
    
    assert policy.title == "Software Installation Policy"
    assert policy.category == "security"
    assert policy.is_active is True
    print("✓ PolicyDoc schema created successfully")


def test_decision_record_schema():
    """Test DecisionRecord schema creation."""
    print("\nTesting DecisionRecord Schema...")
    
    decision = DecisionRecord(
        id="dec_001",
        request_id="req_001",
        decision_type="access_grant",
        decision=RequestDecision.ALLOWED,
        reasoning="Request meets policy requirements",
        confidence_score=0.95,
        automated=True
    )
    
    assert decision.decision == RequestDecision.ALLOWED
    assert decision.confidence_score == 0.95
    assert decision.automated is True
    print("✓ DecisionRecord schema created successfully")


def test_plan_step_schema():
    """Test PlanStep schema creation."""
    print("\nTesting PlanStep Schema...")
    
    step = PlanStep(
        id="step_001",
        step_number=1,
        title="Grant VS Code Access",
        description="Grant user access to VS Code application",
        action_type="tool_call",
        tool_name="access_management",
        parameters={"application": "VS Code", "permission": "read_write"}
    )
    
    assert step.step_number == 1
    assert step.action_type == "tool_call"
    assert step.status == "pending"
    print("✓ PlanStep schema created successfully")


def test_plan_record_schema():
    """Test PlanRecord schema creation."""
    print("\nTesting PlanRecord Schema...")
    
    plan = PlanRecord(
        id="plan_001",
        request_id="req_001",
        plan_type="access_grant",
        title="VS Code Access Grant Plan",
        description="Plan to grant VS Code access to user",
        steps=[],
        created_by="system"
    )
    
    assert plan.plan_type == "access_grant"
    assert plan.status == "draft"
    assert plan.created_by == "system"
    print("✓ PlanRecord schema created successfully")


def test_ticket_record_schema():
    """Test TicketRecord schema creation."""
    print("\nTesting TicketRecord Schema...")
    
    ticket = TicketRecord(
        id="ticket_001",
        ticket_number="T001",
        title="VS Code Access Request",
        description="User requesting VS Code access",
        requester_id="emp_001",
        category="access_request",
        priority="medium"
    )
    
    assert ticket.ticket_number == "T001"
    assert ticket.status == TicketStatus.NEW
    assert ticket.category == "access_request"
    print("✓ TicketRecord schema created successfully")


def test_tool_call_schema():
    """Test ToolCall schema creation."""
    print("\nTesting ToolCall Schema...")
    
    tool_call = ToolCall(
        id="tool_001",
        plan_step_id="step_001",
        tool_name="access_management",
        parameters={"user": "emp_001", "application": "VS Code"}
    )
    
    assert tool_call.tool_name == "access_management"
    assert tool_call.status == "pending"
    print("✓ ToolCall schema created successfully")


def test_citation_schema():
    """Test Citation schema creation."""
    print("\nTesting Citation Schema...")
    
    citation = Citation(
        id="cit_001",
        source_type="policy",
        source_id="pol_001",
        source_title="Software Installation Policy",
        content="Only approved software can be installed on company devices",
        relevance_score=0.9
    )
    
    assert citation.source_type == "policy"
    assert citation.relevance_score == 0.9
    print("✓ Citation schema created successfully")


def test_risk_flag_schema():
    """Test RiskFlag schema creation."""
    print("\nTesting RiskFlag Schema...")
    
    risk = RiskFlag(
        id="risk_001",
        request_id="req_001",
        risk_type="security",
        severity="medium",
        description="Software installation may introduce security risks",
        impact="Potential malware or unauthorized access"
    )
    
    assert risk.risk_type == "security"
    assert risk.severity == "medium"
    assert risk.is_acknowledged is False
    print("✓ RiskFlag schema created successfully")


def test_router_verdict_schema():
    """Test RouterVerdict schema creation."""
    print("\nTesting RouterVerdict Schema...")
    
    verdict = RouterVerdict(
        id="verdict_001",
        request_id="req_001",
        routing_decision="human_review",
        confidence_score=0.75,
        reasoning="Request requires human review due to security implications",
        assigned_queue="security_review",
        requires_approval=True
    )
    
    assert verdict.routing_decision == "human_review"
    assert verdict.confidence_score == 0.75
    assert verdict.requires_approval is True
    print("✓ RouterVerdict schema created successfully")


def run_all_tests():
    """Run all schema tests."""
    print("Running Domain Schema Tests...\n")
    
    try:
        test_enums()
        test_employee_schema()
        test_user_request_schema()
        test_policy_doc_schema()
        test_decision_record_schema()
        test_plan_step_schema()
        test_plan_record_schema()
        test_ticket_record_schema()
        test_tool_call_schema()
        test_citation_schema()
        test_risk_flag_schema()
        test_router_verdict_schema()
        
        print("\n🎉 All schema tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
