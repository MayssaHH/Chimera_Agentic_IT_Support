"""
Human-in-the-Loop (HIL) Node for IT Support Workflow

This node manages the pause/resume workflow when human review is required,
enqueuing questions for IT staff and providing resume functionality.
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..state import (
    ITGraphState, HILPending, DecisionRecord, DecisionType
)


class HILStatus(str, Enum):
    """Status of HIL items"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"


class HILQuestionType(str, Enum):
    """Types of questions for IT staff"""
    CLASSIFICATION_REVIEW = "classification_review"
    POLICY_INTERPRETATION = "policy_interpretation"
    RISK_ASSESSMENT = "risk_assessment"
    APPROVAL_DECISION = "approval_decision"
    EXCEPTION_GRANTING = "exception_granting"


@dataclass
class HILQuestion:
    """Question for IT staff review"""
    question_id: str
    ticket_id: str
    question_type: HILQuestionType
    title: str
    description: str
    context: Dict[str, Any]
    options: List[Dict[str, Any]]
    assigned_to: str
    priority: str
    created_at: datetime
    due_date: datetime
    status: HILStatus
    escalation_path: List[str]
    timeout_hours: int


@dataclass
class HILAnswer:
    """Answer from IT staff"""
    answer_id: str
    question_id: str
    ticket_id: str
    answered_by: str
    answer: str
    decision: str
    justification: str
    confidence: float
    additional_notes: str
    answered_at: datetime
    metadata: Dict[str, Any]


class HILQueue:
    """Manages the queue of HIL questions for IT staff"""
    
    def __init__(self, queue_client=None):
        self.queue_client = queue_client
        self.pending_questions = []
        self.completed_answers = {}
        
    def enqueue_question(self, question: HILQuestion) -> str:
        """Add question to the queue"""
        if self.queue_client:
            # Real queue implementation
            return self.queue_client.enqueue('hil_questions', question)
        else:
            # In-memory queue for testing
            self.pending_questions.append(question)
            return question.question_id
    
    def get_pending_questions(self, assigned_to: str = None) -> List[HILQuestion]:
        """Get pending questions, optionally filtered by assignee"""
        if self.queue_client:
            return self.queue_client.get_pending('hil_questions', assigned_to)
        else:
            if assigned_to:
                return [q for q in self.pending_questions if q.assigned_to == assigned_to]
            return self.pending_questions.copy()
    
    def mark_question_completed(self, question_id: str, answer: HILAnswer):
        """Mark question as completed with answer"""
        if self.queue_client:
            self.queue_client.complete('hil_questions', question_id, answer)
        else:
            # Remove from pending and store answer
            self.pending_questions = [q for q in self.pending_questions if q.question_id != question_id]
            self.completed_answers[question_id] = answer
    
    def get_answer(self, question_id: str) -> Optional[HILAnswer]:
        """Get answer for a completed question"""
        if self.queue_client:
            return self.queue_client.get_answer('hil_questions', question_id)
        else:
            return self.completed_answers.get(question_id)


class HILQuestionGenerator:
    """Generates appropriate questions for IT staff based on HIL pending items"""
    
    def __init__(self):
        self.question_templates = {
            'classification_review': {
                'title': 'Review Classification Decision',
                'description': 'Review the automated classification decision and provide human oversight.',
                'options': [
                    {'value': 'confirm', 'label': 'Confirm Decision', 'description': 'Agree with the automated decision'},
                    {'value': 'modify', 'label': 'Modify Decision', 'description': 'Change the decision with justification'},
                    {'value': 'escalate', 'label': 'Escalate', 'description': 'Escalate to higher authority'}
                ]
            },
            'policy_interpretation': {
                'title': 'Policy Interpretation Required',
                'description': 'Clarify policy interpretation for this request.',
                'options': [
                    {'value': 'clarify', 'label': 'Clarify Policy', 'description': 'Provide policy clarification'},
                    {'value': 'exception', 'label': 'Grant Exception', 'description': 'Grant policy exception'},
                    {'value': 'deny', 'label': 'Deny Request', 'description': 'Deny based on policy'}
                ]
            },
            'risk_assessment': {
                'title': 'Risk Assessment Required',
                'description': 'Assess the risk level and provide recommendations.',
                'options': [
                    {'value': 'low_risk', 'label': 'Low Risk', 'description': 'Approve - low risk'},
                    {'value': 'medium_risk', 'label': 'Medium Risk', 'description': 'Approve with conditions'},
                    {'value': 'high_risk', 'label': 'High Risk', 'description': 'Deny or require additional approval'}
                ]
            }
        }
    
    def generate_question(self, hil_item: HILPending, 
                         decision_record: DecisionRecord) -> HILQuestion:
        """Generate appropriate question based on HIL item type"""
        question_type = self._determine_question_type(hil_item, decision_record)
        template = self.question_templates.get(question_type, self.question_templates['classification_review'])
        
        # Generate unique question ID
        question_id = f"hil_q_{uuid.uuid4().hex[:8]}"
        
        # Create context for the question
        context = self._create_question_context(hil_item, decision_record)
        
        # Determine assignee based on priority and type
        assigned_to = self._determine_assignee(hil_item, decision_record)
        
        # Calculate due date based on priority
        due_date = self._calculate_due_date(hil_item.priority)
        
        return HILQuestion(
            question_id=question_id,
            ticket_id=hil_item.item_id.split('_')[1],  # Extract ticket ID from HIL item ID
            question_type=question_type,
            title=template['title'],
            description=template['description'],
            context=context,
            options=template['options'],
            assigned_to=assigned_to,
            priority=hil_item.priority,
            created_at=datetime.now(),
            due_date=due_date,
            status=HILStatus.PENDING,
            escalation_path=hil_item.escalation_path,
            timeout_hours=hil_item.timeout_hours
        )
    
    def _determine_question_type(self, hil_item: HILPending, 
                                decision_record: DecisionRecord) -> HILQuestionType:
        """Determine the type of question needed"""
        if 'classification' in hil_item.type.lower():
            return HILQuestionType.CLASSIFICATION_REVIEW
        elif 'policy' in hil_item.type.lower():
            return HILQuestionType.POLICY_INTERPRETATION
        elif 'risk' in hil_item.type.lower():
            return HILQuestionType.RISK_ASSESSMENT
        else:
            return HILQuestionType.CLASSIFICATION_REVIEW
    
    def _create_question_context(self, hil_item: HILPending, 
                                decision_record: DecisionRecord) -> Dict[str, Any]:
        """Create context information for the question"""
        return {
            'request_summary': {
                'title': decision_record.get('justification_brief', '')[:200],
                'decision': decision_record.get('decision', ''),
                'confidence': decision_record.get('confidence', 0.0),
                'citations_count': len(decision_record.get('citations', []))
            },
            'hil_reason': hil_item.description,
            'priority': hil_item.priority,
            'escalation_path': hil_item.escalation_path,
            'timeout_hours': hil_item.timeout_hours
        }
    
    def _determine_assignee(self, hil_item: HILPending, 
                           decision_record: DecisionRecord) -> str:
        """Determine who should review this question"""
        if hil_item.assigned_to != 'unassigned':
            return hil_item.assigned_to
        
        # Auto-assign based on decision type and priority
        decision = decision_record.get('decision', '')
        priority = hil_item.priority
        
        if decision == 'DENIED' or priority == 'CRITICAL':
            return 'senior_analyst'
        elif decision == 'REQUIRES_APPROVAL':
            return 'team_lead'
        else:
            return 'analyst'
    
    def _calculate_due_date(self, priority: str) -> datetime:
        """Calculate due date based on priority"""
        now = datetime.now()
        
        if priority == 'CRITICAL':
            return now + timedelta(hours=1)
        elif priority == 'HIGH':
            return now + timedelta(hours=4)
        elif priority == 'MEDIUM':
            return now + timedelta(hours=8)
        else:  # LOW
            return now + timedelta(hours=24)


class HILWorkflowManager:
    """Manages the HIL workflow pause/resume cycle"""
    
    def __init__(self, queue: HILQueue):
        self.queue = queue
        self.paused_workflows = {}  # ticket_id -> pause_info
        
    def pause_workflow(self, state: ITGraphState) -> bool:
        """Pause workflow if HIL is pending"""
        hil_pending = state.get('hil_pending', [])
        
        if not hil_pending:
            return False  # No HIL needed, continue workflow
        
        # Generate questions for each HIL item
        question_generator = HILQuestionGenerator()
        
        for hil_item in hil_pending:
            decision_record = state.get('decision_record', {})
            question = question_generator.generate_question(hil_item, decision_record)
            
            # Enqueue question
            self.queue.enqueue_question(question)
            
            # Record pause information
            ticket_id = question.ticket_id
            self.paused_workflows[ticket_id] = {
                'pause_time': datetime.now(),
                'hil_items': [hil_item.item_id for hil_item in hil_pending],
                'questions': [question.question_id for question in [question]],
                'status': 'waiting_for_human_review'
            }
        
        return True  # Workflow paused
    
    def resume_workflow(self, ticket_id: str, human_answer: HILAnswer) -> Optional[ITGraphState]:
        """Resume workflow with human answer"""
        if ticket_id not in self.paused_workflows:
            return None  # No paused workflow for this ticket
        
        # Get the paused workflow state (in real implementation, this would be retrieved from storage)
        # For now, we'll return None to indicate the workflow should be restarted
        return None
    
    def get_pause_status(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get status of paused workflow"""
        return self.paused_workflows.get(ticket_id)


def hil_node(state: ITGraphState) -> ITGraphState:
    """
    HIL node: checks if human review is needed and pauses workflow if so
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state (workflow continues if no HIL needed)
    """
    try:
        # Initialize HIL components
        queue = HILQueue()
        workflow_manager = HILWorkflowManager(queue)
        
        # Check if workflow should be paused
        workflow_paused = workflow_manager.pause_workflow(state)
        
        if workflow_paused:
            # Add HIL pause metadata
            if 'metadata' not in state:
                state['metadata'] = {}
            state['metadata']['hil_pause'] = {
                'paused_at': datetime.now().isoformat(),
                'pause_reason': 'Human review required',
                'hil_items_count': len(state.get('hil_pending', [])),
                'status': 'paused_waiting_for_review'
            }
            
            # Set workflow status to paused
            if 'workflow_status' not in state:
                state['workflow_status'] = {}
            state['workflow_status']['status'] = 'PAUSED'
            state['workflow_status']['reason'] = 'Human review required'
            state['workflow_status']['paused_at'] = datetime.now().isoformat()
        
        return state
        
    except Exception as e:
        # Handle errors gracefully
        error_record = {
            'error_id': f"hil_error_{datetime.now().timestamp()}",
            'timestamp': datetime.now(),
            'error_type': 'hil_error',
            'message': f"Error in HIL node: {str(e)}",
            'stack_trace': None,
            'context': {'node': 'hil', 'state_keys': list(state.keys())},
            'severity': 'medium',
            'resolved': False,
            'resolution_notes': None
        }
        
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(error_record)
        
        return state


def resume_from_hil(ticket_id: str, human_answer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resume workflow from HIL pause with human answer
    
    Args:
        ticket_id: ID of the ticket to resume
        human_answer: Answer from IT staff
        
    Returns:
        Updated decision record and workflow status
    """
    try:
        # Create HILAnswer object
        answer = HILAnswer(
            answer_id=f"answer_{uuid.uuid4().hex[:8]}",
            question_id=human_answer.get('question_id', ''),
            ticket_id=ticket_id,
            answered_by=human_answer.get('answered_by', 'unknown'),
            answer=human_answer.get('answer', ''),
            decision=human_answer.get('decision', ''),
            justification=human_answer.get('justification', ''),
            confidence=float(human_answer.get('confidence', 0.0)),
            additional_notes=human_answer.get('additional_notes', ''),
            answered_at=datetime.now(),
            metadata=human_answer.get('metadata', {})
        )
        
        # Update decision record based on human answer
        updated_decision = {
            'decision': answer.decision,
            'justification_brief': answer.justification,
            'confidence': answer.confidence,
            'needs_human': False,  # Human review completed
            'human_review': {
                'reviewed_by': answer.answered_by,
                'reviewed_at': answer.answered_at.isoformat(),
                'human_decision': answer.decision,
                'human_justification': answer.justification,
                'human_confidence': answer.confidence
            },
            'updated_at': datetime.now().isoformat()
        }
        
        # Mark HIL pending as completed
        hil_status = {
            'completed_at': datetime.now().isoformat(),
            'completed_by': answer.answered_by,
            'human_answer': answer.answer,
            'status': 'completed'
        }
        
        return {
            'success': True,
            'ticket_id': ticket_id,
            'updated_decision': updated_decision,
            'hil_status': hil_status,
            'workflow_status': 'resumed',
            'resumed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'ticket_id': ticket_id
        }


# Convenience functions for testing and direct usage
def create_hil_question(question_data: Dict[str, Any]) -> HILQuestion:
    """Create a HILQuestion from dictionary data"""
    return HILQuestion(**question_data)


def create_hil_answer(answer_data: Dict[str, Any]) -> HILAnswer:
    """Create a HILAnswer from dictionary data"""
    return HILAnswer(**answer_data)


def test_hil_node():
    """Test function for the HIL node"""
    # Create test state with HIL pending
    test_state = {
        'user_request': {
            'title': 'Database Access Request',
            'description': 'Need elevated access to production database'
        },
        'decision_record': {
            'decision': 'REQUIRES_APPROVAL',
            'confidence': 0.45,
            'needs_human': True
        },
        'hil_pending': [
            {
                'item_id': 'hil_12345',
                'type': 'classification_review',
                'description': 'Low confidence decision requires human review',
                'assigned_to': 'unassigned',
                'priority': 'MEDIUM',
                'created_at': datetime.now(),
                'status': 'pending',
                'escalation_path': ['supervisor'],
                'timeout_hours': 24
            }
        ]
    }
    
    # Run HIL node
    result_state = hil_node(test_state)
    
    print(f"Workflow paused: {result_state.get('workflow_status', {}).get('status') == 'PAUSED'}")
    print(f"HIL pause metadata: {result_state.get('metadata', {}).get('hil_pause')}")
    
    return result_state


def test_resume_from_hil():
    """Test function for resume functionality"""
    human_answer = {
        'question_id': 'hil_q_abc123',
        'answered_by': 'analyst_john',
        'answer': 'confirm',
        'decision': 'ALLOWED',
        'justification': 'Request meets policy requirements with manager approval',
        'confidence': 0.95,
        'additional_notes': 'Standard access request, no special risks'
    }
    
    result = resume_from_hil('12345', human_answer)
    
    print(f"Resume successful: {result['success']}")
    print(f"Updated decision: {result['updated_decision']['decision']}")
    
    return result


if __name__ == "__main__":
    # Run tests if executed directly
    test_hil_node()
    test_resume_from_hil()
