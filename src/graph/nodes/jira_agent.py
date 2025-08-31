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
        if not self.config.get('base_url') or not self.config.get('user') or not self.config.get('token'):
            raise Exception("❌ JIRA CREDENTIALS REQUIRED! NO MOCKS ALLOWED!")
        # NO MOCK TICKETS - REAL JIRA ONLY!
        
    def create_ticket(self, ticket_data: JiraTicketData) -> str:
        """Create a new Jira ticket"""
        print(f"\n🔧 JIRA CLIENT: Creating REAL JIRA ticket:")
        print(f"  - Summary: {ticket_data.summary}")
        print(f"  - Issue Type: {ticket_data.issue_type}")
        print(f"  - Priority: {ticket_data.priority}")
        print(f"  - Components: {ticket_data.components}")
        print(f"  - Labels: {ticket_data.labels}")
        print(f"  - JIRA URL: {self.config['base_url']}")
        
        # REAL JIRA API CALL - NO MOCKS!
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Prepare JIRA API payload
            payload = {
                "fields": {
                    "project": {"key": self.config['project_key']},
                    "summary": ticket_data.summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": ticket_data.description}]
                            }
                        ]
                    },
                    "issuetype": {"name": ticket_data.issue_type},
                    "priority": {"name": ticket_data.priority},
                    "components": [{"name": comp} for comp in ticket_data.components],
                    "labels": ticket_data.labels
                }
            }
            
            if ticket_data.assignee:
                payload["fields"]["assignee"] = {"name": ticket_data.assignee}
            
            # Make API call to JIRA
            url = f"{self.config['base_url']}/rest/api/3/issue"
            auth = HTTPBasicAuth(self.config['user'], self.config['token'])
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            
            print(f"🔧 JIRA CLIENT: Making API call to {url}")
            response = requests.post(url, json=payload, auth=auth, headers=headers)
            
            if response.status_code == 201:
                ticket_data = response.json()
                ticket_id = ticket_data['key']
                print(f"🔧 JIRA CLIENT: REAL JIRA ticket created: {ticket_id}")
                return ticket_id
            else:
                raise Exception(f"JIRA API failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ JIRA API ERROR: {e}")
            raise Exception(f"Failed to create JIRA ticket: {e}")
    
    def transition_ticket(self, transition_data: JiraTransitionData) -> bool:
        """Transition ticket to new status"""
        # NO MOCKS ALLOWED - REAL JIRA ONLY!
        if not self.config.get('base_url') or not self.config.get('user') or not self.config.get('token'):
            raise Exception("❌ JIRA CREDENTIALS REQUIRED! NO MOCKS ALLOWED!")
        else:
            # Real Jira API implementation
            try:
                import requests
                from requests.auth import HTTPBasicAuth
                
                # Get available transitions for the ticket
                transitions_url = f"{self.config['base_url']}/rest/api/3/issue/{transition_data.ticket_id}/transitions"
                auth = HTTPBasicAuth(self.config['user'], self.config['token'])
                headers = {"Accept": "application/json"}
                
                transitions_response = requests.get(transitions_url, auth=auth, headers=headers)
                
                if transitions_response.status_code == 200:
                    transitions_data = transitions_response.json()
                    
                    # Find the target transition
                    target_transition = None
                    for transition in transitions_data['transitions']:
                        if transition['name'] == transition_data.transition_name:
                            target_transition = transition
                            break
                    
                    if target_transition:
                        # Execute the transition
                        transition_payload = {
                            "transition": {"id": target_transition['id']}
                        }
                        
                        if transition_data.comment:
                            transition_payload["update"] = {
                                "comment": [
                                    {
                                        "add": {
                                            "body": {
                                                "type": "doc",
                                                "version": 1,
                                                "content": [
                                                    {
                                                        "type": "paragraph",
                                                        "content": [
                                                            {
                                                                "type": "text",
                                                                "text": transition_data.comment
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ]
                            }
                        
                        transition_url = f"{self.config['base_url']}/rest/api/3/issue/{transition_data.ticket_id}/transitions"
                        transition_response = requests.post(
                            transition_url, 
                            json=transition_payload, 
                            auth=auth, 
                            headers={"Accept": "application/json", "Content-Type": "application/json"}
                        )
                        
                        if transition_response.status_code == 204:
                            return True
                        else:
                            raise Exception(f"Transition failed: {transition_response.status_code} - {transition_response.text}")
                    else:
                        raise Exception(f"Transition '{transition_data.transition_name}' not available")
                else:
                    raise Exception(f"Failed to get transitions: {transitions_response.status_code} - {transitions_response.text}")
                    
            except Exception as e:
                # NO MOCKS ALLOWED - FAIL FAST!
                print(f"❌ JIRA API FAILED: {e}")
                raise Exception(f"JIRA API failed - NO MOCK FALLBACK ALLOWED: {e}")
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket details"""
        # NO MOCKS ALLOWED - REAL JIRA ONLY!
        if not self.config.get('base_url') or not self.config.get('user') or not self.config.get('token'):
            raise Exception("❌ JIRA CREDENTIALS REQUIRED! NO MOCKS ALLOWED!")
        
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Get ticket details from Jira API
            url = f"{self.config['base_url']}/rest/api/3/issue/{ticket_id}"
            auth = HTTPBasicAuth(self.config['user'], self.config['token'])
            headers = {"Accept": "application/json"}
            
            response = requests.get(url, auth=auth, headers=headers)
            
            if response.status_code == 200:
                jira_data = response.json()
                return {
                    'id': jira_data['id'],
                    'key': jira_data['key'],
                    'summary': jira_data['fields']['summary'],
                    'description': jira_data['fields']['description'],
                    'status': jira_data['fields']['status']['name'],
                    'priority': jira_data['fields']['priority']['name'],
                    'assignee': jira_data['fields'].get('assignee', {}).get('displayName'),
                    'components': [comp['name'] for comp in jira_data['fields'].get('components', [])],
                    'labels': jira_data['fields'].get('labels', []),
                    'created_at': jira_data['fields']['created'],
                    'updated_at': jira_data['fields']['updated']
                }
            else:
                raise Exception(f"Failed to get ticket: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ JIRA API ERROR: {e}")
            raise Exception(f"Failed to get JIRA ticket: {e}")
    
    def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add comment to ticket"""
        # NO MOCKS ALLOWED - REAL JIRA ONLY!
        if not self.config.get('base_url') or not self.config.get('user') or not self.config.get('token'):
            raise Exception("❌ JIRA CREDENTIALS REQUIRED! NO MOCKS ALLOWED!")
        
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Add comment to Jira ticket
            url = f"{self.config['base_url']}/rest/api/3/issue/{ticket_id}/comment"
            auth = HTTPBasicAuth(self.config['user'], self.config['token'])
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            
            comment_payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, json=comment_payload, auth=auth, headers=headers)
            
            if response.status_code == 201:
                return True
            else:
                raise Exception(f"Failed to add comment: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ JIRA API ERROR: {e}")
            raise Exception(f"Failed to add JIRA comment: {e}")


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
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Processing workflow state")
        print(f"🔧 JIRA WORKFLOW MANAGER: State keys: {list(state.keys())}")
        print(f"🔧 JIRA WORKFLOW MANAGER: State content:")
        for key, value in state.items():
            if isinstance(value, dict):
                print(f"  - {key}: {type(value).__name__} with keys: {list(value.keys())}")
            else:
                print(f"  - {key}: {type(value).__name__} = {value}")
        
        # Create ticket if it doesn't exist (first pass)
        if 'ticket_record' not in state:
            print(f"\n🔧 JIRA WORKFLOW MANAGER: No ticket record found, creating initial ticket...")
            ticket_record = self._create_initial_ticket(state)
            state['ticket_record'] = ticket_record
            print(f"🔧 JIRA WORKFLOW MANAGER: Initial ticket created: {ticket_record.get('ticket_id')}")
        else:
            print(f"\n🔧 JIRA WORKFLOW MANAGER: Existing ticket found: {state['ticket_record'].get('ticket_id')}")
        
        # Get current ticket and workflow state
        ticket_record = state['ticket_record']
        current_status = ticket_record.get('status', 'New')
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Current ticket status: {current_status}")
        
        # Determine what action to take based on current state
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Determining workflow action...")
        action = self._determine_workflow_action(state, current_status)
        
        if action:
            print(f"\n🔧 JIRA WORKFLOW MANAGER: Action determined: {action['action']} -> {action['target_status']}")
            # Execute the action
            success = self._execute_workflow_action(action, ticket_record, state)
            if success:
                print(f"🔧 JIRA WORKFLOW MANAGER: Action executed successfully")
                # Update ticket record
                ticket_record['status'] = action['target_status']
                ticket_record['updated_at'] = datetime.now()
                
                # Add action comment
                print(f"🔧 JIRA WORKFLOW MANAGER: Adding comment to ticket...")
                self.jira_client.add_comment(
                    ticket_record['ticket_id'],
                    action['comment']
                )
        else:
            print(f"\n🔧 JIRA WORKFLOW MANAGER: No action needed at this stage")
        
        # Persist updated ticket record
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Persisting ticket record...")
        self.ticket_persister.persist_ticket(ticket_record)
        
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Workflow state processing completed")
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
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Creating initial ticket...")
        
        user_request = state.get('user_request', {})
        decision_record = state.get('decision_record', {})
        
        print(f"🔧 JIRA WORKFLOW MANAGER: User request data:")
        print(f"  - Title: {user_request.get('title', 'No title')}")
        print(f"  - Priority: {user_request.get('priority', 'MEDIUM')}")
        print(f"  - Category: {user_request.get('category', 'general')}")
        print(f"  - Department: {user_request.get('department', 'Unknown')}")
        print(f"  - Urgency: {user_request.get('urgency', 'Unknown')}")
        
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Decision record data:")
        print(f"  - Decision: {decision_record.get('decision', 'Unknown')}")
        print(f"  - Confidence: {decision_record.get('confidence', 'Unknown')}")
        print(f"  - Needs Human: {decision_record.get('needs_human', 'Unknown')}")
        
        # Build ticket description
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Building ticket description...")
        description_builder = TicketDescriptionBuilder()
        description = description_builder.build_description(state)
        print(f"🔧 JIRA WORKFLOW MANAGER: Description built, length: {len(description)}")
        print(f"🔧 JIRA WORKFLOW MANAGER: Description preview: {description[:200]}...")
        
        # Create Jira ticket
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Preparing Jira ticket data...")
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
        
        print(f"🔧 JIRA WORKFLOW MANAGER: Ticket data prepared:")
        print(f"  - Summary: {ticket_data.summary}")
        print(f"  - Issue Type: {ticket_data.issue_type}")
        print(f"  - Priority: {ticket_data.priority}")
        print(f"  - Components: {ticket_data.components}")
        print(f"  - Labels: {ticket_data.labels}")
        
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Calling Jira client to create ticket...")
        jira_ticket_id = self.jira_client.create_ticket(ticket_data)
        print(f"🔧 JIRA WORKFLOW MANAGER: Jira ticket created with ID: {jira_ticket_id}")
        
        # Create ticket record
        print(f"\n🔧 JIRA WORKFLOW MANAGER: Creating ticket record...")
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
        
        print(f"🔧 JIRA WORKFLOW MANAGER: Ticket record created successfully")
        print(f"🔧 JIRA WORKFLOW MANAGER: Ticket record keys: {list(ticket_record.keys())}")
        return ticket_record
    



def jira_agent_node(state: ITGraphState) -> ITGraphState:
    """
    Jira agent node: creates tickets, manages status transitions, persists records
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with ticket_record populated/updated
    """
    print("\n" + "="*80)
    print("🔧 JIRA AGENT NODE: STARTING EXECUTION")
    print("="*80)
    
    try:
        print(f"🔧 JIRA AGENT: Starting Jira agent node execution")
        print(f"🔧 JIRA AGENT: State keys: {list(state.keys())}")
        print(f"🔧 JIRA AGENT: State content preview:")
        for key, value in state.items():
            if isinstance(value, dict):
                print(f"  - {key}: {type(value).__name__} with keys: {list(value.keys())}")
            else:
                print(f"  - {key}: {type(value).__name__} = {value}")
        
        # Load Jira configuration from centralized config
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        try:
    from config import settings
except ImportError:
    # Fallback for when config module is not available
    class MockSettings:
        jira_base_url = None
        jira_user = None
        jira_token = None
        jira_project_key = None
    settings = MockSettings()
        
        print(f"\n🔧 JIRA AGENT: Configuration loading...")
        print(f"  - Config file location: {os.path.join(os.path.dirname(__file__), '..', '..')}")
        print(f"  - Python path: {sys.path[:3]}...")
        
        # NO MOCKS ALLOWED - REAL JIRA ONLY!
        try:
            # Try to import the new config system
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'config'))
            from jira_config import get_jira_config
            
            jira_config_obj = get_jira_config()
            
            if not jira_config_obj.validate():
                raise Exception("❌ JIRA CREDENTIALS REQUIRED! Configure JIRA in src/config/jira_settings.py or set environment variables. NO MOCKS ALLOWED!")
            
            jira_config = {
                'base_url': jira_config_obj.base_url,
                'user': jira_config_obj.user,
                'token': jira_config_obj.token,
                'project_key': jira_config_obj.project_key,
                'use_mock': False,  # NEVER USE MOCKS
                'api_version': jira_config_obj.api_version,
                'timeout_seconds': jira_config_obj.timeout_seconds,
                'max_retries': jira_config_obj.max_retries
            }
            
        except ImportError as e:
            print(f"⚠️  New config system import failed: {e}")
            # Fallback to old settings method
            if not settings.jira_base_url or not settings.jira_user or not settings.jira_token:
                raise Exception("❌ JIRA CREDENTIALS REQUIRED! Set JIRA_BASE_URL, JIRA_USER, and JIRA_TOKEN environment variables. NO MOCKS ALLOWED!")
            
            jira_config = {
                'base_url': settings.jira_base_url,
                'user': settings.jira_user,
                'token': settings.jira_token,
                'project_key': settings.jira_project_key,
                'use_mock': False  # NEVER USE MOCKS
            }
        
        print(f"\n🔧 JIRA AGENT: Configuration loaded:")
        print(f"  - Base URL: {jira_config['base_url']}")
        print(f"  - User: {jira_config['user']}")
        print(f"  - Token: {'***' if jira_config['token'] else 'NOT SET'}")
        print(f"  - Project Key: {jira_config['project_key']}")
        print(f"  - Use Mock: {jira_config['use_mock']}")
        
        # Initialize Jira components with configuration
        print(f"\n🔧 JIRA AGENT: Initializing Jira components...")
        jira_client = JiraClient(jira_config)
        ticket_persister = TicketRecordPersister()
        workflow_manager = JiraWorkflowManager(jira_client, ticket_persister)
        
        print(f"\n🔧 JIRA AGENT: Processing workflow state...")
        # Process workflow state and manage Jira ticket throughout pipeline
        updated_state = workflow_manager.process_workflow_state(state)
        
        print(f"\n🔧 JIRA AGENT: Workflow state processed")
        print(f"🔧 JIRA AGENT: Updated state keys: {list(updated_state.keys())}")
        
        # Add Jira metadata
        if 'metadata' not in updated_state:
            updated_state['metadata'] = {}
        updated_state['metadata']['jira'] = {
            'ticket_created': 'ticket_record' in updated_state,
            'ticket_id': updated_state.get('ticket_record', {}).get('ticket_id'),
            'status': updated_state.get('ticket_record', {}).get('status'),
            'last_updated': datetime.now().isoformat(),
            'pipeline_managed': True,
            'workflow_stage': 'ticket_created',
            'config_loaded': bool(jira_config['base_url']),
            'use_mock': jira_config['use_mock']
        }
        
        print(f"\n🔧 JIRA AGENT: Jira metadata added:")
        print(f"  - Ticket Created: {updated_state['metadata']['jira']['ticket_created']}")
        print(f"  - Ticket ID: {updated_state['metadata']['jira']['ticket_id']}")
        print(f"  - Status: {updated_state['metadata']['jira']['status']}")
        print(f"  - Use Mock: {updated_state['metadata']['jira']['use_mock']}")
        
        print(f"\n🔧 JIRA AGENT: Node execution completed successfully")
        print("="*80)
        print("🔧 JIRA AGENT NODE: EXECUTION COMPLETED")
        print("="*80)
        return updated_state
        
    except Exception as e:
        # Handle errors gracefully
        print(f"\n❌ JIRA AGENT ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        error_record = {
            'error_id': f"jira_error_{datetime.now().timestamp()}",
            'timestamp': datetime.now(),
            'error_type': 'jira_error',
            'message': f"Error in Jira agent node: {str(e)}",
            'stack_trace': traceback.format_exc(),
            'context': {'node': 'jira_agent', 'state_keys': list(state.keys())},
            'severity': 'high',
            'resolved': False,
            'resolution_notes': None
        }
        
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(error_record)
        
        print(f"\n🔧 JIRA AGENT: Error recorded, returning state with errors")
        print("="*80)
        print("🔧 JIRA AGENT NODE: EXECUTION FAILED")
        print("="*80)
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
