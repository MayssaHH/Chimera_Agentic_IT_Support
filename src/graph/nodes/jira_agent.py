"""
Jira Agent Node for IT Support Workflow

This node manages Jira ticket creation, status transitions, and ticket record persistence
based on classification decisions.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..state import (
    ITGraphState, TicketRecord, DecisionRecord, Citation, DecisionType
)


class JiraStatus(str, Enum):
    """Jira ticket status values"""
    NEW = "New"
    IN_PROGRESS = "In Progress"
    WAITING_FOR_APPROVAL = "Waiting for Approval"
    WAITING_FOR_HUMAN_REVIEW = "Waiting for Human Review"
    CLOSED = "Closed"
    REOPENED = "Reopened"
    RESOLVED = "Resolved"


class JiraTransition(str, Enum):
    """Jira status transitions"""
    START_PROGRESS = "Start Progress"
    APPROVE = "Approve"
    DENY = "Deny"
    CLOSE = "Close"
    REOPEN = "Reopen"


@dataclass
class JiraTicketData:
    """Data for Jira ticket creation/update"""
    summary: str
    description: str
    issue_type: str
    priority: str
    assignee: Optional[str]
    components: List[str]
    labels: List[str]
    custom_fields: Dict[str, Any]


@dataclass
class JiraTransitionData:
    """Data for Jira status transitions"""
    ticket_id: str
    transition_name: str
    comment: str
    assignee: Optional[str]
    resolution: Optional[str]


class JiraClient:
    """Client for Jira API operations"""
    
    def __init__(self, jira_config: Dict[str, Any] = None):
        self.config = jira_config or {}
        self.mock_tickets = {}  # For testing without real Jira
        self.ticket_counter = 1000
        
    def create_ticket(self, ticket_data: JiraTicketData) -> str:
        """Create a new Jira ticket"""
        if self.config.get('use_mock', True):
            # Mock implementation for testing
            ticket_id = f"IT-{self.ticket_counter}"
            self.ticket_counter += 1
            
            mock_ticket = {
                'id': ticket_id,
                'key': ticket_id,
                'summary': ticket_data.summary,
                'description': ticket_data.description,
                'status': JiraStatus.NEW,
                'priority': ticket_data.priority,
                'assignee': ticket_data.assignee,
                'components': ticket_data.components,
                'labels': ticket_data.labels,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            self.mock_tickets[ticket_id] = mock_ticket
            return ticket_id
        else:
            # Real Jira API implementation
            # This would call the actual Jira REST API
            pass
    
    def transition_ticket(self, transition_data: JiraTransitionData) -> bool:
        """Transition ticket to new status"""
        if self.config.get('use_mock', True):
            # Mock implementation
            ticket_id = transition_data.ticket_id
            if ticket_id in self.mock_tickets:
                ticket = self.mock_tickets[ticket_id]
                
                # Update status based on transition
                if transition_data.transition_name == JiraTransition.START_PROGRESS:
                    ticket['status'] = JiraStatus.IN_PROGRESS
                elif transition_data.transition_name == JiraTransition.CLOSE:
                    ticket['status'] = JiraStatus.CLOSED
                elif transition_data.transition_name == JiraTransition.APPROVE:
                    ticket['status'] = JiraStatus.IN_PROGRESS
                
                # Update assignee if provided
                if transition_data.assignee:
                    ticket['assignee'] = transition_data.assignee
                
                ticket['updated_at'] = datetime.now()
                return True
            
            return False
        else:
            # Real Jira API implementation
            pass
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket details"""
        if self.config.get('use_mock', True):
            return self.mock_tickets.get(ticket_id)
        else:
            # Real Jira API implementation
            pass
    
    def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add comment to ticket"""
        if self.config.get('use_mock', True):
            if ticket_id in self.mock_tickets:
                ticket = self.mock_tickets[ticket_id]
                if 'comments' not in ticket:
                    ticket['comments'] = []
                ticket['comments'].append({
                    'text': comment,
                    'author': 'system',
                    'timestamp': datetime.now()
                })
                return True
            return False
        else:
            # Real Jira API implementation
            pass


class TicketDescriptionBuilder:
    """Builds comprehensive ticket descriptions with decision details"""
    
    def __init__(self):
        self.description_template = """
## Request Details
{request_summary}

## Classification Decision
**Decision:** {decision}
**Confidence:** {confidence}%
**Needs Human Review:** {needs_human}

## Justification
{justification}

## Policy Citations
{citations_section}

## Missing Information
{missing_fields_section}

## Risk Assessment
{risk_assessment}

## Next Steps
{next_steps}

---
*Ticket created automatically by IT Support Workflow System*
*Created at: {timestamp}*
"""
    
    def build_description(self, state: ITGraphState) -> str:
        """Build complete ticket description"""
        user_request = state.get('user_request', {})
        decision_record = state.get('decision_record', {})
        
        # Format citations
        citations_section = self._format_citations(decision_record.get('citations', []))
        
        # Format missing fields
        missing_fields = decision_record.get('missing_fields', [])
        missing_fields_section = self._format_missing_fields(missing_fields)
        
        # Determine next steps
        next_steps = self._determine_next_steps(decision_record)
        
        # Build risk assessment
        risk_assessment = self._format_risk_assessment(decision_record)
        
        # Fill template
        description = self.description_template.format(
            request_summary=self._format_request_summary(user_request),
            decision=decision_record.get('decision', 'UNKNOWN'),
            confidence=int(decision_record.get('confidence', 0) * 100),
            needs_human='Yes' if decision_record.get('needs_human', False) else 'No',
            justification=decision_record.get('justification_brief', 'No justification provided'),
            citations_section=citations_section,
            missing_fields_section=missing_fields_section,
            risk_assessment=risk_assessment,
            next_steps=next_steps,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return description.strip()
    
    def _format_citations(self, citations: List[Citation]) -> str:
        """Format citations for ticket description"""
        if not citations:
            return "No specific policy citations provided."
        
        formatted = []
        for i, citation in enumerate(citations, 1):
            formatted.append(f"""
**Citation {i}:**
- **Source:** {citation.get('source', 'Unknown')}
- **Text:** {citation.get('text', 'No text provided')}
- **Relevance:** {citation.get('relevance', 'No relevance explanation')}
""")
        
        return '\n'.join(formatted)
    
    def _format_missing_fields(self, missing_fields: List[str]) -> str:
        """Format missing fields for ticket description"""
        if not missing_fields:
            return "All required information provided."
        
        formatted = []
        for field in missing_fields:
            formatted.append(f"- {field}")
        
        return '\n'.join(formatted)
    
    def _determine_next_steps(self, decision_record: DecisionRecord) -> str:
        """Determine next steps based on decision"""
        decision = decision_record.get('decision', '')
        
        if decision == DecisionType.ALLOWED:
            return "1. Proceed with request fulfillment\n2. Update ticket status to 'In Progress'\n3. Complete implementation"
        elif decision == DecisionType.DENIED:
            return "1. Notify requester of denial\n2. Provide policy justification\n3. Close ticket"
        elif decision == DecisionType.REQUIRES_APPROVAL:
            return "1. Route to appropriate approver\n2. Wait for approval decision\n3. Update ticket based on approval outcome"
        else:
            return "1. Review decision\n2. Determine appropriate action\n3. Update ticket accordingly"
    
    def _format_risk_assessment(self, decision_record: DecisionRecord) -> str:
        """Format risk assessment for ticket description"""
        risk_assessment = decision_record.get('risk_assessment', {})
        
        if not risk_assessment:
            return "No risk assessment provided."
        
        risk_level = risk_assessment.get('risk_level', 'UNKNOWN')
        reason = risk_assessment.get('reason', 'No reason provided')
        
        return f"**Risk Level:** {risk_level}\n**Reason:** {reason}"
    
    def _format_request_summary(self, user_request: Dict[str, Any]) -> str:
        """Format request summary for ticket description"""
        return f"""
**Title:** {user_request.get('title', 'No title')}
**Description:** {user_request.get('description', 'No description')}
**Category:** {user_request.get('category', 'Unknown')}
**Priority:** {user_request.get('priority', 'Unknown')}
**Department:** {user_request.get('department', 'Unknown')}
**Urgency:** {user_request.get('urgency', 'Unknown')}
**Submitted By:** {user_request.get('requested_by', 'Unknown')}
**Submitted At:** {user_request.get('submitted_at', 'Unknown')}
"""


class TicketRecordPersister:
    """Persists ticket records to storage"""
    
    def __init__(self, storage_client=None):
        self.storage_client = storage_client
        self.ticket_records = []  # In-memory storage for testing
    
    def persist_ticket(self, ticket_record: TicketRecord) -> str:
        """Persist ticket record and return record ID"""
        # Generate unique ID if not present
        if 'ticket_id' not in ticket_record:
            ticket_record['ticket_id'] = f"ticket_{datetime.now().timestamp()}_{len(self.ticket_records)}"
        
        # Add metadata
        ticket_record['persisted_at'] = datetime.now()
        
        # Store ticket record
        if self.storage_client:
            # Real storage implementation
            self.storage_client.store('tickets', ticket_record['ticket_id'], ticket_record)
        else:
            # In-memory storage for testing
            self.ticket_records.append(ticket_record)
        
        return ticket_record['ticket_id']
    
    def get_ticket(self, ticket_id: str) -> Optional[TicketRecord]:
        """Retrieve ticket record by ID"""
        if self.storage_client:
            return self.storage_client.retrieve('tickets', ticket_id)
        else:
            # In-memory lookup
            for ticket in self.ticket_records:
                if ticket.get('ticket_id') == ticket_id:
                    return ticket
        return None


class JiraWorkflowManager:
    """Manages Jira workflow throughout the entire pipeline lifecycle"""
    
    def __init__(self, jira_client: JiraClient, ticket_persister: TicketRecordPersister):
        self.jira_client = jira_client
        self.ticket_persister = ticket_persister
        
    def process_workflow_state(self, state: ITGraphState) -> ITGraphState:
        """Process current workflow state and manage Jira ticket accordingly"""
        # Create ticket if it doesn't exist (first pass)
        if 'ticket_record' not in state:
            ticket_record = self._create_initial_ticket(state)
            state['ticket_record'] = ticket_record
        
        # Get current ticket and workflow state
        ticket_record = state['ticket_record']
        current_status = ticket_record.get('status', 'New')
        
        # Determine what action to take based on current state
        action = self._determine_workflow_action(state, current_status)
        
        if action:
            # Execute the action
            success = self._execute_workflow_action(action, ticket_record, state)
            if success:
                # Update ticket record
                ticket_record['status'] = action['target_status']
                ticket_record['updated_at'] = datetime.now()
                
                # Add action comment
                self.jira_client.add_comment(
                    ticket_record['ticket_id'],
                    action['comment']
                )
        
        # Persist updated ticket record
        self.ticket_persister.persist_ticket(ticket_record)
        
        return state
    
    def _determine_workflow_action(self, state: ITGraphState, current_status: str) -> Optional[Dict[str, Any]]:
        """Determine what Jira action to take based on current workflow state"""
        decision_record = state.get('decision_record', {})
        plan_record = state.get('plan_record', {})
        hil_pending = state.get('hil_pending', [])
        workflow_status = state.get('workflow_status', {})
        
        # Check if this is initial classification
        if decision_record and current_status == 'New':
            decision = decision_record.get('decision', '')
            if decision == DecisionType.ALLOWED:
                return {
                    'action': 'start_progress',
                    'target_status': 'In Progress',
                    'comment': f"Request approved - moving to 'In Progress' for implementation. Decision: {decision}"
                }
            elif decision == DecisionType.REQUIRES_APPROVAL:
                return {
                    'action': 'start_progress',
                    'target_status': 'In Progress',
                    'comment': f"Request requires approval - moving to 'In Progress' for approval workflow. Decision: {decision}"
                }
            elif decision == DecisionType.DENIED:
                return {
                    'action': 'close_denied',
                    'target_status': 'Closed',
                    'comment': f"Request denied based on policy compliance. Resolution: Denied. Decision: {decision}"
                }
        
        # Check if IT agent has completed work
        if plan_record and current_status == 'In Progress':
            # Check if HIL is needed
            if hil_pending:
                return {
                    'action': 'wait_for_human',
                    'target_status': 'Waiting for Human Review',
                    'comment': f"IT agent work completed but human review required. HIL items: {len(hil_pending)}"
                }
            else:
                # Check if work is fully complete
                if workflow_status.get('status') == 'COMPLETED':
                    return {
                        'action': 'resolve_completed',
                        'target_status': 'Resolved',
                        'comment': "Request fully completed and resolved. All work finished successfully."
                    }
                elif workflow_status.get('status') == 'IN_PROGRESS':
                    return {
                        'action': 'continue_progress',
                        'target_status': 'In Progress',
                        'comment': "IT agent work in progress. Continuing implementation."
                    }
        
        # Check if HIL has been completed
        if current_status == 'Waiting for Human Review' and not hil_pending:
            return {
                'action': 'resume_after_hil',
                'target_status': 'In Progress',
                'comment': "Human review completed. Resuming workflow implementation."
            }
        
        # Check if request is fully satisfied
        if workflow_status.get('status') == 'RESOLVED':
            return {
                'action': 'close_resolved',
                'target_status': 'Closed',
                'comment': "Request fully resolved and employer satisfied. Closing ticket."
            }
        
        return None
    
    def _execute_workflow_action(self, action: Dict[str, Any], ticket_record: TicketRecord, state: ITGraphState) -> bool:
        """Execute the determined workflow action"""
        transition_data = JiraTransitionData(
            ticket_id=ticket_record['ticket_id'],
            transition_name=self._get_transition_name(action['action']),
            comment=action['comment'],
            assignee=self._get_assignee_for_action(action['action'], state),
            resolution=self._get_resolution_for_action(action['action'])
        )
        
        return self.jira_client.transition_ticket(transition_data)
    
    def _get_transition_name(self, action: str) -> str:
        """Get Jira transition name for action"""
        transition_map = {
            'start_progress': JiraTransition.START_PROGRESS,
            'close_denied': JiraTransition.CLOSE,
            'wait_for_human': JiraTransition.START_PROGRESS,  # Keep in progress but add comment
            'continue_progress': JiraTransition.START_PROGRESS,
            'resume_after_hil': JiraTransition.START_PROGRESS,
            'resolve_completed': JiraTransition.START_PROGRESS,
            'close_resolved': JiraTransition.CLOSE
        }
        return transition_map.get(action, JiraTransition.START_PROGRESS)
    
    def _get_assignee_for_action(self, action: str, state: ITGraphState) -> Optional[str]:
        """Get appropriate assignee for the action"""
        if action == 'start_progress':
            decision_record = state.get('decision_record', {})
            decision = decision_record.get('decision', '')
            if decision == DecisionType.REQUIRES_APPROVAL:
                return 'approval_queue'
            else:
                return 'it_agent'
        elif action == 'wait_for_human':
            return 'human_review_queue'
        elif action == 'resume_after_hil':
            return 'it_agent'
        else:
            return None
    
    def _get_resolution_for_action(self, action: str) -> Optional[str]:
        """Get resolution for the action"""
        if action == 'close_denied':
            return 'Denied'
        elif action == 'close_resolved':
            return 'Resolved'
        else:
            return None
    
    def _get_workflow_stage(self, state: ITGraphState) -> str:
        """Determine current workflow stage for metadata"""
        if state.get('workflow_status', {}).get('status') == 'PAUSED':
            return 'human_review'
        elif state.get('plan_record'):
            if state.get('hil_pending'):
                return 'waiting_for_human'
            else:
                return 'implementation'
        elif state.get('decision_record'):
            return 'classified'
        else:
            return 'initial'
    
    def _create_initial_ticket(self, state: ITGraphState) -> TicketRecord:
        """Create initial ticket with status 'New'"""
        user_request = state.get('user_request', {})
        decision_record = state.get('decision_record', {})
        
        # Build ticket description
        description_builder = TicketDescriptionBuilder()
        description = description_builder.build_description(state)
        
        # Create Jira ticket
        ticket_data = JiraTicketData(
            summary=f"IT Support Request: {user_request.get('title', 'No title')}",
            description=description,
            issue_type="Task",
            priority=user_request.get('priority', 'MEDIUM'),
            assignee=None,  # Will be assigned based on decision
            components=["IT Support"],
            labels=[user_request.get('category', 'general'), 'automated'],
            custom_fields={}
        )
        
        jira_ticket_id = self.jira_client.create_ticket(ticket_data)
        
        # Create ticket record
        ticket_record = TicketRecord(
            ticket_id=jira_ticket_id,
            status="New",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            assigned_to=None,
            priority=user_request.get('priority', 'MEDIUM'),
            category=user_request.get('category', 'general'),
            description=description,
            resolution=None,
            resolution_date=None,
            time_spent=0.0,
            tags=[user_request.get('category', 'general'), 'automated'],
            custom_fields={},
            audit_trail=[{
                'action': 'ticket_created',
                'timestamp': datetime.now().isoformat(),
                'details': 'Ticket created automatically based on classification decision'
            }]
        )
        
        return ticket_record
    



def jira_agent_node(state: ITGraphState) -> ITGraphState:
    """
    Jira agent node: creates tickets, manages status transitions, persists records
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with ticket_record populated/updated
    """
    try:
        # Initialize Jira components
        jira_client = JiraClient()
        ticket_persister = TicketRecordPersister()
        workflow_manager = JiraWorkflowManager(jira_client, ticket_persister)
        
        # Process workflow state and manage Jira ticket throughout pipeline
        updated_state = workflow_manager.process_workflow_state(state)
        
        # Add Jira metadata
        if 'metadata' not in updated_state:
            updated_state['metadata'] = {}
        updated_state['metadata']['jira'] = {
            'ticket_created': 'ticket_record' in updated_state,
            'ticket_id': updated_state.get('ticket_record', {}).get('ticket_id'),
            'status': updated_state.get('ticket_record', {}).get('status'),
            'last_updated': datetime.now().isoformat(),
            'pipeline_managed': True,
            'workflow_stage': self._get_workflow_stage(updated_state)
        }
        
        return updated_state
        
    except Exception as e:
        # Handle errors gracefully
        error_record = {
            'error_id': f"jira_error_{datetime.now().timestamp()}",
            'timestamp': datetime.now(),
            'error_type': 'jira_error',
            'message': f"Error in Jira agent node: {str(e)}",
            'stack_trace': None,
            'context': {'node': 'jira_agent', 'state_keys': list(state.keys())},
            'severity': 'medium',
            'resolved': False,
            'resolution_notes': None
        }
        
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(error_record)
        
        return state


# Convenience functions for testing and direct usage
def create_jira_ticket_data(ticket_data: Dict[str, Any]) -> JiraTicketData:
    """Create a JiraTicketData from dictionary data"""
    return JiraTicketData(**ticket_data)


def create_jira_transition_data(transition_data: Dict[str, Any]) -> JiraTransitionData:
    """Create a JiraTransitionData from dictionary data"""
    return JiraTransitionData(**transition_data)


def test_jira_agent_node():
    """Test function for the Jira agent node"""
    # Create test state
    test_state = {
        'user_request': {
            'title': 'Software Installation Request',
            'description': 'Need Visual Studio Code installed on development machine',
            'category': 'software',
            'priority': 'MEDIUM',
            'department': 'engineering',
            'urgency': 'normal',
            'requested_by': 'dev_user_001'
        },
        'decision_record': {
            'decision': 'ALLOWED',
            'confidence': 0.92,
            'needs_human': False,
            'justification_brief': 'Standard software installation request meets policy requirements',
            'citations': [
                {
                    'source': 'Software_Installation_Policy',
                    'text': 'Standard development tools may be installed upon request',
                    'relevance': 'Directly applicable policy for development software'
                }
            ],
            'missing_fields': [],
            'risk_assessment': {'risk_level': 'LOW', 'reason': 'Standard development tool'}
        }
    }
    
    # Run Jira agent node
    result_state = jira_agent_node(test_state)
    
    print(f"Ticket created: {result_state.get('ticket_record', {}).get('ticket_id')}")
    print(f"Ticket status: {result_state.get('ticket_record', {}).get('status')}")
    print(f"Jira metadata: {result_state.get('metadata', {}).get('jira')}")
    print(f"Workflow stage: {result_state.get('metadata', {}).get('jira', {}).get('workflow_stage')}")
    
    return result_state


if __name__ == "__main__":
    # Run test if executed directly
    test_jira_agent_node()
