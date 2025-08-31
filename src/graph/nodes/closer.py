"""
Closer Node for IT Support Workflow

This node handles the final completion of IT support requests, including:
- Satisfaction surveys
- Final status updates
- Ticket closure confirmation
- Knowledge base updates
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..state import (
    ITGraphState, TicketRecord, PlanRecord, DecisionRecord, DecisionType
)


class CompletionStatus(str, Enum):
    """Status of request completion"""
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class SatisfactionLevel(str, Enum):
    """User satisfaction levels"""
    VERY_SATISFIED = "very_satisfied"
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    DISSATISFIED = "dissatisfied"
    VERY_DISSATISFIED = "very_dissatisfied"


@dataclass
class CompletionSummary:
    """Summary of request completion"""
    completion_id: str
    ticket_id: str
    status: CompletionStatus
    completion_date: datetime
    resolution_summary: str
    time_to_resolution: float  # in hours
    steps_completed: int
    total_steps: int
    human_intervention_required: bool
    escalation_reason: Optional[str]
    knowledge_gaps: List[str]
    improvement_suggestions: List[str]


@dataclass
class SatisfactionSurvey:
    """User satisfaction survey data"""
    survey_id: str
    ticket_id: str
    satisfaction_level: SatisfactionLevel
    response_time_rating: int  # 1-5
    solution_quality_rating: int  # 1-5
    communication_rating: int  # 1-5
    overall_experience_rating: int  # 1-5
    feedback_comments: Optional[str]
    would_recommend: bool
    submitted_at: datetime


class CompletionHandler:
    """Handles request completion and closure"""
    
    def __init__(self):
        self.completion_records = {}
        self.satisfaction_surveys = {}
        
    def complete_request(self, state: ITGraphState) -> CompletionSummary:
        """Complete the IT support request"""
        ticket_record = state.get('ticket_record', {})
        plan_record = state.get('plan_record', {})
        
        # Calculate completion metrics
        steps_completed = self._count_completed_steps(plan_record)
        total_steps = self._count_total_steps(plan_record)
        time_to_resolution = self._calculate_resolution_time(ticket_record)
        
        # Determine completion status
        status = self._determine_completion_status(steps_completed, total_steps, state)
        
        # Generate completion summary
        completion_summary = CompletionSummary(
            completion_id=str(uuid.uuid4()),
            ticket_id=ticket_record.get('ticket_id', ''),
            status=status,
            completion_date=datetime.now(),
            resolution_summary=self._generate_resolution_summary(state),
            time_to_resolution=time_to_resolution,
            steps_completed=steps_completed,
            total_steps=total_steps,
            human_intervention_required=self._check_human_intervention(state),
            escalation_reason=self._get_escalation_reason(state) if status == CompletionStatus.ESCALATED else None,
            knowledge_gaps=self._identify_knowledge_gaps(state),
            improvement_suggestions=self._generate_improvement_suggestions(state)
        )
        
        # Store completion record
        self.completion_records[completion_summary.completion_id] = completion_summary
        
        return completion_summary
    
    def _count_completed_steps(self, plan_record: Dict[str, Any]) -> int:
        """Count completed plan steps"""
        if not plan_record or 'steps' not in plan_record:
            return 0
        
        completed = 0
        for step in plan_record['steps']:
            if step.get('status') == 'completed':
                completed += 1
        
        return completed
    
    def _count_total_steps(self, plan_record: Dict[str, Any]) -> int:
        """Count total plan steps"""
        if not plan_record or 'steps' not in plan_record:
            return 0
        
        return len(plan_record['steps'])
    
    def _calculate_resolution_time(self, ticket_record: Dict[str, Any]) -> float:
        """Calculate time to resolution in hours"""
        if not ticket_record:
            return 0.0
        
        created_at = ticket_record.get('created_at')
        if not created_at:
            return 0.0
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        now = datetime.now()
        if created_at.tzinfo:
            now = now.replace(tzinfo=created_at.tzinfo)
        
        delta = now - created_at
        return delta.total_seconds() / 3600  # Convert to hours
    
    def _determine_completion_status(self, steps_completed: int, total_steps: int, 
                                   state: ITGraphState) -> CompletionStatus:
        """Determine the completion status"""
        if steps_completed == 0:
            return CompletionStatus.CANCELLED
        
        if steps_completed == total_steps:
            return CompletionStatus.COMPLETED
        
        # Check if escalated
        if state.get('escalation_record'):
            return CompletionStatus.ESCALATED
        
        return CompletionStatus.PARTIALLY_COMPLETED
    
    def _generate_resolution_summary(self, state: ITGraphState) -> str:
        """Generate a summary of the resolution"""
        plan_record = state.get('plan_record', {})
        decision_record = state.get('decision_record', {})
        
        if decision_record.get('decision') == DecisionType.DENIED:
            return "Request denied based on policy compliance requirements"
        
        if plan_record and 'steps' in plan_record:
            completed_steps = [s for s in plan_record['steps'] if s.get('status') == 'completed']
            if completed_steps:
                return f"Successfully completed {len(completed_steps)} out of {len(plan_record['steps'])} planned steps"
        
        return "Request processed and resolved"
    
    def _check_human_intervention(self, state: ITGraphState) -> bool:
        """Check if human intervention was required"""
        return bool(state.get('hil_pending') or state.get('escalation_record'))
    
    def _get_escalation_reason(self, state: ITGraphState) -> Optional[str]:
        """Get the reason for escalation if any"""
        escalation_record = state.get('escalation_record', {})
        return escalation_record.get('reason')
    
    def _identify_knowledge_gaps(self, state: ITGraphState) -> List[str]:
        """Identify knowledge gaps that could be addressed"""
        gaps = []
        
        # Check if policies were insufficient
        retrieved_docs = state.get('retrieved_docs', [])
        if not retrieved_docs:
            gaps.append("No relevant policies found for request category")
        
        # Check if past tickets provided insufficient guidance
        past_tickets = state.get('past_tickets_features', [])
        if not past_tickets:
            gaps.append("No similar past tickets for reference")
        
        return gaps
    
    def _generate_improvement_suggestions(self, state: ITGraphState) -> List[str]:
        """Generate suggestions for process improvement"""
        suggestions = []
        
        # Check response time
        ticket_record = state.get('ticket_record', {})
        if ticket_record:
            time_to_resolution = self._calculate_resolution_time(ticket_record)
            if time_to_resolution > 24:  # More than 24 hours
                suggestions.append("Consider automation for faster response times")
        
        # Check human intervention
        if self._check_human_intervention(state):
            suggestions.append("Review process to reduce manual intervention requirements")
        
        # Check knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(state)
        if knowledge_gaps:
            suggestions.append("Update knowledge base with missing policies and procedures")
        
        return suggestions


class SatisfactionSurveyHandler:
    """Handles user satisfaction surveys"""
    
    def __init__(self):
        self.surveys = {}
        
    def create_survey(self, ticket_id: str) -> Dict[str, Any]:
        """Create a satisfaction survey for a completed ticket"""
        survey = {
            'survey_id': str(uuid.uuid4()),
            'ticket_id': ticket_id,
            'created_at': datetime.now(),
            'status': 'pending',
            'questions': [
                {
                    'id': 'overall_satisfaction',
                    'type': 'rating',
                    'question': 'How satisfied are you with the overall resolution?',
                    'options': [level.value for level in SatisfactionLevel]
                },
                {
                    'id': 'response_time',
                    'type': 'rating',
                    'question': 'How would you rate the response time?',
                    'options': ['1', '2', '3', '4', '5']
                },
                {
                    'id': 'solution_quality',
                    'type': 'rating',
                    'question': 'How would you rate the quality of the solution?',
                    'options': ['1', '2', '3', '4', '5']
                },
                {
                    'id': 'communication',
                    'type': 'rating',
                    'question': 'How would you rate the communication during the process?',
                    'options': ['1', '2', '3', '4', '5']
                },
                {
                    'id': 'recommendation',
                    'type': 'boolean',
                    'question': 'Would you recommend our IT support to others?',
                    'options': ['Yes', 'No']
                },
                {
                    'id': 'feedback',
                    'type': 'text',
                    'question': 'Any additional feedback or suggestions?',
                    'options': []
                }
            ]
        }
        
        self.surveys[survey['survey_id']] = survey
        return survey
    
    def submit_survey(self, survey_id: str, responses: Dict[str, Any]) -> SatisfactionSurvey:
        """Submit a completed satisfaction survey"""
        survey = self.surveys.get(survey_id)
        if not survey:
            raise ValueError(f"Survey {survey_id} not found")
        
        # Create satisfaction survey record
        satisfaction_survey = SatisfactionSurvey(
            survey_id=survey_id,
            ticket_id=survey['ticket_id'],
            satisfaction_level=SatisfactionLevel(responses.get('overall_satisfaction', 'neutral')),
            response_time_rating=int(responses.get('response_time', 3)),
            solution_quality_rating=int(responses.get('solution_quality', 3)),
            communication_rating=int(responses.get('communication', 3)),
            overall_experience_rating=int(responses.get('overall_satisfaction', 3)),
            feedback_comments=responses.get('feedback'),
            would_recommend=responses.get('recommendation', 'Yes') == 'Yes',
            submitted_at=datetime.now()
        )
        
        # Store the survey response
        self.satisfaction_surveys[survey_id] = satisfaction_survey
        
        # Update survey status
        survey['status'] = 'completed'
        survey['responses'] = responses
        
        return satisfaction_survey


def close_request(state: ITGraphState) -> Dict[str, Any]:
    """Main function to close an IT support request"""
    print("\n" + "="*80)
    print("✅ CLOSER NODE: STARTING EXECUTION")
    print("="*80)
    
    print(f"✅ CLOSER: Starting closer node execution")
    print(f"✅ CLOSER: State keys: {list(state.keys())}")
    
    completion_handler = CompletionHandler()
    survey_handler = SatisfactionSurveyHandler()
    
    # Complete the request
    print(f"✅ CLOSER: Completing request...")
    completion_summary = completion_handler.complete_request(state)
    
    # Create satisfaction survey if completed successfully
    survey = None
    if completion_summary.status == CompletionStatus.COMPLETED:
        survey = survey_handler.create_survey(completion_summary.ticket_id)
    
    result = {
        'completion_summary': completion_summary,
        'satisfaction_survey': survey,
        'status': 'closed',
        'closed_at': datetime.now().isoformat()
    }
    
    print(f"\n✅ CLOSER: Request closed successfully")
    print(f"✅ CLOSER: Status: {result['status']}")
    print(f"✅ CLOSER: Survey created: {survey is not None}")
    print("="*80)
    print("✅ CLOSER NODE: EXECUTION COMPLETED")
    print("="*80)
    
    return result
