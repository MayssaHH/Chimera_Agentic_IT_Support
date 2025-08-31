"""
Planner Node for IT Support Workflow

This node calls the planner LLM with the planner prompt, parses JSON responses,
creates PlanRecord objects, persists them to the database, and handles
manager approval requirements by attaching email drafts to tickets.
"""

import json
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..state import (
    ITGraphState, PlanRecord, PlanRecordModel, PlanStep, PlanStepModel,
    DecisionRecord, DecisionType, PriorityLevel, ActorType
)
from ...models.llm_registry import get_llm
from ...store.db import save_plan_from_record, get_ticket, update_ticket_status
from ...tools.emailer import Emailer


@dataclass
class PlanningInput:
    """Input data for planning"""
    user_request: Dict[str, Any]
    decision_record: DecisionRecord
    retrieved_docs: List[Dict[str, Any]]
    past_tickets_features: List[Dict[str, Any]]
    employee: Dict[str, Any]


@dataclass
class PlanningResult:
    """Result of planning attempt"""
    success: bool
    plan_record: Optional[PlanRecord] = None
    requires_approval: bool = False
    email_draft: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = None


class PlannerPromptCaller:
    """Calls the planner LLM with the planner prompt"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.planner_prompt_path = "src/prompts/planner.md"
        self.max_retries = 3
    
    def call_planner(self, input_data: PlanningInput, 
                     target_model: str) -> str:
        """Call the planner LLM with the prompt and input data"""
        # Read planner prompt
        try:
            with open(self.planner_prompt_path, 'r') as f:
                planner_prompt = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Planner prompt not found at {self.planner_prompt_path}")
        
        # Prepare prompt input
        prompt_input = self._prepare_prompt_input(input_data)
        
        # Call LLM with retries
        for attempt in range(self.max_retries):
            try:
                if self.llm_client:
                    response = self.llm_client.call(
                        prompt=planner_prompt,
                        input_data=prompt_input,
                        model=target_model
                    )
                    return response
                else:
                    # Use LLM registry
                    llm = get_llm("planner")
                    messages = [
                        {"role": "system", "content": planner_prompt},
                        {"role": "user", "content": json.dumps(prompt_input, indent=2)}
                    ]
                    response = llm.invoke(messages)
                    return response.content
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                # Retry on failure
                continue
        
        raise Exception("Failed to get planner response after all retries")
    
    def _prepare_prompt_input(self, input_data: PlanningInput) -> Dict[str, Any]:
        """Prepare input data for planner prompt"""
        # Format retrieved documents
        formatted_docs = []
        for doc in input_data.retrieved_docs:
            formatted_docs.append({
                'title': doc.get('title', ''),
                'content': doc.get('content', '')[:1000],  # Limit content length
                'source': doc.get('source', ''),
                'document_type': doc.get('document_type', ''),
                'relevance_score': doc.get('relevance_score', 0.0)
            })
        
        # Format past tickets features
        formatted_tickets = []
        for ticket in input_data.past_tickets_features:
            formatted_tickets.append({
                'category': ticket.get('category', ''),
                'resolution': ticket.get('resolution', ''),
                'decision': ticket.get('decision', ''),
                'similarity_score': ticket.get('similarity_score', 0.0)
            })
        
        return {
            'request_details': {
                'title': input_data.user_request.get('title', ''),
                'description': input_data.user_request.get('description', ''),
                'category': input_data.user_request.get('category', ''),
                'priority': input_data.user_request.get('priority', ''),
                'department': input_data.user_request.get('department', ''),
                'urgency': input_data.user_request.get('urgency', '')
            },
            'classifier_json': {
                'decision': input_data.decision_record.get('decision', ''),
                'citations': [
                    {
                        'source': citation.get('source', ''),
                        'text': citation.get('text', ''),
                        'relevance': citation.get('relevance', '')
                    }
                    for citation in input_data.decision_record.get('citations', [])
                ],
                'missing_fields': input_data.decision_record.get('missing_fields', []),
                'confidence': input_data.decision_record.get('confidence', 0.0)
            },
            'relevant_policies': formatted_docs,
            'past_ticket_patterns': formatted_tickets
        }
    
    def _generate_mock_response(self, input_data: PlanningInput) -> str:
        """Generate mock response for testing without LLM"""
        # Simple mock based on request category and decision
        category = input_data.user_request.get('category', '').lower()
        decision = input_data.decision_record.get('decision', '')
        
        if 'access' in category or decision == 'REQUIRES_APPROVAL':
            classification = 'REQUIRES_APPROVAL'
            priority = 'MEDIUM'
            estimated_duration = 4
            needs_approval = True
        else:
            classification = 'ALLOWED'
            priority = 'LOW'
            estimated_duration = 2
            needs_approval = False
        
        mock_response = f"""
```json
{{
  "plan_id": "PLAN_{uuid.uuid4().hex[:8].upper()}",
  "request_summary": "Process {category} request for {input_data.user_request.get('title', 'IT request')}",
  "classification": "{classification}",
  "priority": "{priority}",
  "estimated_duration": "{estimated_duration}",
  "steps": [
    {{
      "step_id": "step_1",
      "order": 1,
      "description": "Review request and validate requirements",
      "actor": "it_agent",
      "actor_details": "IT Support Agent",
      "required_tools": ["ticketing_system", "policy_database"],
      "preconditions": ["request_initialized"],
      "postconditions": ["requirements_validated"],
      "estimated_duration": "30",
      "data_privacy_notes": "Standard request processing",
      "dependencies": [],
      "automation_possible": true,
      "fallback_actor": "senior_agent"
    }}
  ],
  "approval_workflow": {{
    "needed": {str(needs_approval).lower()},
    "approvers": ["IT_Manager"] if {needs_approval} else [],
    "approval_order": "sequential" if {needs_approval} else "none",
    "escalation_path": ["IT_Director"] if {needs_approval} else [],
    "timeout_hours": 24 if {needs_approval} else 0
  }},
  "email_draft": {{
    "subject": "Approval Required: {input_data.user_request.get('title', 'IT Request')}",
    "recipients": ["it.manager@company.com"] if {needs_approval} else [],
    "cc": ["it.director@company.com"] if {needs_approval} else [],
    "body": "Please review and approve this IT request." if {needs_approval} else "",
    "attachments": [],
    "urgency_note": "Standard processing time"
  }},
  "risk_assessment": {{
    "risk_level": "MEDIUM",
    "risks": ["Standard operational risk"],
    "mitigation_strategies": ["Follow established procedures"],
    "rollback_plan": "Standard rollback procedures"
  }},
  "compliance_checklist": [
    "Policy_compliance_verified",
    "Audit_trail_created"
  ],
  "success_criteria": [
    "Request processed within SLA",
    "All approvals documented",
    "Compliance requirements met"
  ]
}}
```
"""
        return mock_response


class JSONResponseParser:
    """Parses and validates JSON responses from planner LLM"""
    
    def __init__(self):
        self.required_fields = [
            'plan_id', 'request_summary', 'classification', 'priority', 
            'estimated_duration', 'steps', 'approval_workflow', 'email_draft',
            'risk_assessment', 'compliance_checklist', 'success_criteria'
        ]
        self.valid_classifications = ['ALLOWED', 'DENIED', 'REQUIRES_APPROVAL']
        self.valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    def parse_response(self, response: str) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """Parse LLM response and return success, data, and validation errors"""
        # Extract JSON from response
        json_data = self._extract_json(response)
        if not json_data:
            return False, None, ["No JSON found in response"]
        
        # Validate JSON structure
        validation_errors = self._validate_json_structure(json_data)
        if validation_errors:
            return False, json_data, validation_errors
        
        # Validate field values
        value_errors = self._validate_field_values(json_data)
        if value_errors:
            return False, json_data, value_errors
        
        return True, json_data, []
    
    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response"""
        # Try to find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON without markdown
        try:
            # Look for JSON-like content
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _validate_json_structure(self, data: Dict[str, Any]) -> List[str]:
        """Validate that all required fields are present"""
        errors = []
        
        for field in self.required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def _validate_field_values(self, data: Dict[str, Any]) -> List[str]:
        """Validate field values meet requirements"""
        errors = []
        
        # Validate classification
        if 'classification' in data:
            if data['classification'] not in self.valid_classifications:
                errors.append(f"Invalid classification: {data['classification']}. Must be one of {self.valid_classifications}")
        
        # Validate priority
        if 'priority' in data:
            if data['priority'] not in self.valid_priorities:
                errors.append(f"Invalid priority: {data['priority']}. Must be one of {self.valid_priorities}")
        
        # Validate estimated_duration
        if 'estimated_duration' in data:
            try:
                duration = float(data['estimated_duration'])
                if duration < 0:
                    errors.append(f"Invalid estimated_duration: {duration}. Must be non-negative")
            except (ValueError, TypeError):
                errors.append(f"Invalid estimated_duration: {data['estimated_duration']}. Must be a number")
        
        # Validate steps
        if 'steps' in data:
            if not isinstance(data['steps'], list):
                errors.append("Steps must be a list")
            elif len(data['steps']) == 0:
                errors.append("At least one step is required")
            else:
                for i, step in enumerate(data['steps']):
                    if not isinstance(step, dict):
                        errors.append(f"Step {i} must be a dictionary")
                    else:
                        step_errors = self._validate_step(step, i)
                        errors.extend(step_errors)
        
        # Validate approval_workflow
        if 'approval_workflow' in data:
            workflow = data['approval_workflow']
            if not isinstance(workflow, dict):
                errors.append("Approval workflow must be a dictionary")
            elif 'needed' in workflow and not isinstance(workflow['needed'], bool):
                errors.append("Approval workflow 'needed' must be a boolean")
        
        return errors
    
    def _validate_step(self, step: Dict[str, Any], index: int) -> List[str]:
        """Validate individual step structure"""
        errors = []
        required_step_fields = ['step_id', 'order', 'description', 'actor', 'actor_details', 'estimated_duration']
        
        for field in required_step_fields:
            if field not in step:
                errors.append(f"Step {index} missing required field: {field}")
        
        # Validate actor type
        if 'actor' in step:
            valid_actors = ['it_agent', 'employee', 'manager_approval', 'system']
            if step['actor'] not in valid_actors:
                errors.append(f"Step {index} has invalid actor: {step['actor']}. Must be one of {valid_actors}")
        
        # Validate order
        if 'order' in step:
            try:
                order = int(step['order'])
                if order < 1:
                    errors.append(f"Step {index} has invalid order: {order}. Must be positive")
            except (ValueError, TypeError):
                errors.append(f"Step {index} has invalid order: {step['order']}. Must be an integer")
        
        return errors


class PlanRepository:
    """Repository for persisting plan records"""
    
    def __init__(self, storage_client=None):
        self.storage_client = storage_client
        self.plans = []  # In-memory storage for testing
    
    def persist_plan(self, plan_record: PlanRecord, ticket_id: str = None, request_id: str = None, created_by: str = None) -> str:
        """Persist plan record and return record ID"""
        # Generate unique ID if not provided
        if not plan_record.get('plan_id'):
            plan_record['plan_id'] = f"plan_{uuid.uuid4().hex[:8].upper()}"
        
        # Add metadata
        plan_record['persisted_at'] = datetime.now()
        
        # Store plan using database if ticket_id is provided
        if ticket_id and request_id and created_by:
            try:
                db_plan = save_plan_from_record(plan_record, ticket_id, request_id, created_by)
                return db_plan.plan_id
            except Exception as e:
                print(f"Failed to save plan to database: {e}")
                # Fallback to in-memory storage
        
        # Store plan
        if self.storage_client:
            # Real storage implementation
            self.storage_client.store('plans', plan_record['plan_id'], plan_record)
        else:
            # In-memory storage for testing
            self.plans.append(plan_record)
        
        return plan_record['plan_id']
    
    def get_plan(self, plan_id: str) -> Optional[PlanRecord]:
        """Retrieve plan record by ID"""
        if self.storage_client:
            return self.storage_client.retrieve('plans', plan_id)
        else:
            # In-memory lookup
            for plan in self.plans:
                if plan.get('plan_id') == plan_id:
                    return plan
        return None


class ApprovalManager:
    """Manages approval workflows and email drafts"""
    
    def __init__(self, emailer: Optional[Emailer] = None):
        self.emailer = emailer or Emailer(dry_run=True)
    
    def check_approval_required(self, plan_data: Dict[str, Any]) -> bool:
        """Check if the plan requires approval"""
        approval_workflow = plan_data.get('approval_workflow', {})
        return approval_workflow.get('needed', False)
    
    def get_approval_actors(self, plan_data: Dict[str, Any]) -> List[str]:
        """Get list of actors who need to approve"""
        approval_workflow = plan_data.get('approval_workflow', {})
        return approval_workflow.get('approvers', [])
    
    def create_email_draft(self, plan_data: Dict[str, Any], 
                          user_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create email draft for approval request"""
        email_draft = plan_data.get('email_draft', {})
        
        # Enhance email draft with request context
        enhanced_draft = {
            'subject': email_draft.get('subject', f"Approval Required: {user_request.get('title', 'IT Request')}"),
            'recipients': email_draft.get('recipients', []),
            'cc': email_draft.get('cc', []),
            'body': email_draft.get('body', ''),
            'attachments': email_draft.get('attachments', []),
            'urgency_note': email_draft.get('urgency_note', ''),
            'request_context': {
                'request_id': user_request.get('request_id', ''),
                'title': user_request.get('title', ''),
                'description': user_request.get('description', ''),
                'category': user_request.get('category', ''),
                'priority': user_request.get('priority', ''),
                'department': user_request.get('department', ''),
                'submitted_by': user_request.get('requested_by', ''),
                'submitted_at': user_request.get('submitted_at', ''),
                'estimated_duration': plan_data.get('estimated_duration', ''),
                'risk_level': plan_data.get('risk_assessment', {}).get('risk_level', '')
            },
            'approval_details': {
                'approvers': plan_data.get('approval_workflow', {}).get('approvers', []),
                'timeout_hours': plan_data.get('approval_workflow', {}).get('timeout_hours', 24),
                'escalation_path': plan_data.get('approval_workflow', {}).get('escalation_path', [])
            }
        }
        
        return enhanced_draft
    
    def send_approval_email(self, email_draft: Dict[str, Any], 
                           ticket_id: str) -> bool:
        """Send approval email using the emailer"""
        try:
            # Prepare email content
            subject = email_draft['subject']
            body = self._format_approval_email_body(email_draft)
            recipients = email_draft['recipients']
            cc = email_draft['cc']
            
            # Send email
            success = self.emailer.send_email(
                to=recipients,
                cc=cc,
                subject=subject,
                body=body
            )
            
            if success:
                # Log successful email
                print(f"Approval email sent successfully for ticket {ticket_id}")
            else:
                print(f"Failed to send approval email for ticket {ticket_id}")
            
            return success
            
        except Exception as e:
            print(f"Error sending approval email: {e}")
            return False
    
    def _format_approval_email_body(self, email_draft: Dict[str, Any]) -> str:
        """Format the approval email body"""
        request_context = email_draft.get('request_context', {})
        approval_details = email_draft.get('approval_details', {})
        
        body = f"""
{email_draft.get('body', '')}

Request Details:
- Request ID: {request_context.get('request_id', 'N/A')}
- Title: {request_context.get('title', 'N/A')}
- Category: {request_context.get('category', 'N/A')}
- Priority: {request_context.get('priority', 'N/A')}
- Department: {request_context.get('department', 'N/A')}
- Submitted By: {request_context.get('submitted_by', 'N/A')}
- Submitted At: {request_context.get('submitted_at', 'N/A')}
- Estimated Duration: {request_context.get('estimated_duration', 'N/A')} hours
- Risk Level: {request_context.get('risk_level', 'N/A')}

Approval Details:
- Required Approvers: {', '.join(approval_details.get('approvers', []))}
- Timeout: {approval_details.get('timeout_hours', 24)} hours
- Escalation Path: {', '.join(approval_details.get('escalation_path', []))}

{email_draft.get('urgency_note', '')}

Please review and approve or deny this request within the specified timeframe.
        """
        
        return body.strip()


def planner_node(state: ITGraphState) -> ITGraphState:
    """
    Planner node: calls planner LLM, parses response, creates PlanRecord,
    persists plan, and handles approval requirements
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with plan_record and potential approval requirements
    """
    print("\n" + "="*80)
    print("📋 PLANNER NODE: STARTING EXECUTION")
    print("="*80)
    
    try:
        print(f"📋 PLANNER: Starting planner node execution")
        print(f"📋 PLANNER: State keys: {list(state.keys())}")
        print(f"📋 PLANNER: Decision record: {state.get('decision_record', {}).get('decision', 'UNKNOWN')}")
        
        # Initialize components
        prompt_caller = PlannerPromptCaller()
        json_parser = JSONResponseParser()
        plan_repo = PlanRepository()
        approval_manager = ApprovalManager()
        
        # Prepare planning input
        input_data = PlanningInput(
            user_request=state.get('user_request', {}),
            decision_record=state.get('decision_record', {}),
            retrieved_docs=state.get('retrieved_docs', []),
            past_tickets_features=state.get('metadata', {}).get('past_tickets', []),
            employee=state.get('employee', {})
        )
        
        # Get target model from router verdict or use default
        target_model = state.get('router_verdict', {}).get('target_model', 'planner_model_v1')
        
        # Call planner LLM
        llm_response = prompt_caller.call_planner(input_data, target_model)
        
        # Parse JSON response
        parse_success, json_data, validation_errors = json_parser.parse_response(llm_response)
        
        if not parse_success:
            # Handle parsing/validation errors
            error_record = {
                'error_id': f"planning_error_{datetime.now().timestamp()}",
                'timestamp': datetime.now(),
                'error_type': 'planning_parsing_error',
                'message': f"Failed to parse planner response: {validation_errors}",
                'stack_trace': None,
                'context': {
                    'node': 'planner',
                    'llm_response': llm_response[:500],  # First 500 chars
                    'validation_errors': validation_errors
                },
                'severity': 'high',
                'resolved': False,
                'resolution_notes': None
            }
            
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append(error_record)
            
            # Create fallback plan record
            fallback_plan = PlanRecord(
                plan_id=f"fallback_plan_{uuid.uuid4().hex[:8].upper()}",
                request_summary="Fallback plan due to parsing errors",
                classification=DecisionType.REQUIRES_APPROVAL,
                priority=PriorityLevel.MEDIUM,
                estimated_duration=0.0,
                steps=[],
                approval_workflow={'needed': True, 'approvers': ['IT_Manager'], 'approval_order': 'sequential', 'escalation_path': ['IT_Director'], 'timeout_hours': 24},
                email_draft={'subject': 'Manual Review Required', 'recipients': [], 'cc': [], 'body': 'Manual review required due to planning system error', 'attachments': [], 'urgency_note': 'Immediate attention required'},
                risk_assessment={'risk_level': 'HIGH', 'risks': ['Planning system error'], 'mitigation_strategies': ['Manual review'], 'rollback_plan': 'Manual intervention'},
                compliance_checklist=['Manual_review_required'],
                success_criteria=['Manual review completed', 'Plan validated'],
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            # Persist fallback plan
            ticket_id = state.get('ticket_record', {}).get('ticket_id')
            request_id = state.get('user_request', {}).get('request_id')
            created_by = state.get('employee', {}).get('employee_id', 'system')
            
            fallback_plan_id = plan_repo.persist_plan(fallback_plan, ticket_id, request_id, created_by)
            fallback_plan['plan_id'] = fallback_plan_id
            
            state['plan_record'] = fallback_plan
            
            # Mark ticket as requires approval
            if 'ticket_record' in state and state['ticket_record'].get('ticket_id'):
                ticket_id = state['ticket_record']['ticket_id']
                try:
                    update_ticket_status(ticket_id, 'waiting_for_approval', 'Planning system error - manual review required')
                except Exception as e:
                    print(f"Failed to update ticket status: {e}")
            
            return state
        
        # Create plan record from parsed data
        plan_record = PlanRecord(
            plan_id=json_data['plan_id'],
            request_summary=json_data['request_summary'],
            classification=DecisionType(json_data['classification']),
            priority=PriorityLevel(json_data['priority']),
            estimated_duration=float(json_data['estimated_duration']),
            steps=[
                PlanStep(
                    step_id=step['step_id'],
                    order=step['order'],
                    description=step['description'],
                    actor=ActorType(step['actor']),
                    actor_details=step['actor_details'],
                    required_tools=step.get('required_tools', []),
                    preconditions=step.get('preconditions', []),
                    postconditions=step.get('postconditions', []),
                    estimated_duration=int(step['estimated_duration']),
                    data_privacy_notes=step.get('data_privacy_notes', ''),
                    dependencies=step.get('dependencies', []),
                    automation_possible=step.get('automation_possible', False),
                    fallback_actor=step.get('fallback_actor')
                )
                for step in json_data['steps']
            ],
            approval_workflow=json_data['approval_workflow'],
            email_draft=json_data['email_draft'],
            risk_assessment=json_data['risk_assessment'],
            compliance_checklist=json_data['compliance_checklist'],
            success_criteria=json_data['success_criteria'],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Persist plan record
        ticket_id = state.get('ticket_record', {}).get('ticket_id')
        request_id = state.get('user_request', {}).get('request_id')
        created_by = state.get('employee', {}).get('employee_id', 'system')
        
        plan_id = plan_repo.persist_plan(plan_record, ticket_id, request_id, created_by)
        plan_record['plan_id'] = plan_id
        
        # Update state with plan record
        state['plan_record'] = plan_record
        
        # Check if approval is required
        requires_approval = approval_manager.check_approval_required(json_data)
        
        if requires_approval:
            # Create enhanced email draft
            email_draft = approval_manager.create_email_draft(json_data, input_data.user_request)
            
            # Attach email draft to plan record
            state['plan_record']['email_draft'] = email_draft
            
            # Mark ticket as requires approval
            if 'ticket_record' in state and state['ticket_record'].get('ticket_id'):
                ticket_id = state['ticket_record']['ticket_id']
                try:
                    update_ticket_status(ticket_id, 'waiting_for_approval', 'Manager approval required')
                    
                    # Add approval metadata to ticket
                    if 'custom_fields' not in state['ticket_record']:
                        state['ticket_record']['custom_fields'] = {}
                    
                    state['ticket_record']['custom_fields'].update({
                        'requires_approval': True,
                        'approval_workflow': json_data['approval_workflow'],
                        'email_draft': email_draft,
                        'approval_timeout_hours': json_data['approval_workflow'].get('timeout_hours', 24)
                    })
                    
                except Exception as e:
                    print(f"Failed to update ticket status: {e}")
            
            # Send approval email if emailer is configured
            try:
                if 'ticket_record' in state and state['ticket_record'].get('ticket_id'):
                    approval_manager.send_approval_email(email_draft, state['ticket_record']['ticket_id'])
            except Exception as e:
                print(f"Failed to send approval email: {e}")
        
        # Add planning metadata
        if 'metadata' not in state:
            state['metadata'] = {}
        state['metadata']['planning'] = {
            'plan_id': plan_record['plan_id'],
            'classification': plan_record['classification'],
            'priority': plan_record['priority'],
            'estimated_duration': plan_record['estimated_duration'],
            'steps_count': len(plan_record['steps']),
            'requires_approval': requires_approval,
            'approval_actors': approval_manager.get_approval_actors(json_data) if requires_approval else [],
            'planning_timestamp': datetime.now().isoformat(),
            'model_used': target_model
        }
        
        return state
        
    except Exception as e:
        # Handle unexpected errors
        error_record = {
            'error_id': f"planning_error_{datetime.now().timestamp()}",
            'timestamp': datetime.now(),
            'error_type': 'planning_error',
            'message': f"Unexpected error in planner node: {str(e)}",
            'stack_trace': None,
            'context': {'node': 'planner', 'state_keys': list(state.keys())},
            'severity': 'critical',
            'resolved': False,
            'resolution_notes': None
        }
        
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(error_record)
        
        # Create emergency fallback plan
        emergency_plan = PlanRecord(
            plan_id=f"emergency_plan_{uuid.uuid4().hex[:8].upper()}",
            request_summary="Emergency plan due to system error",
            classification=DecisionType.REQUIRES_APPROVAL,
            priority=PriorityLevel.CRITICAL,
            estimated_duration=0.0,
            steps=[],
            approval_workflow={'needed': True, 'approvers': ['Emergency_Team'], 'approval_order': 'sequential', 'escalation_path': ['IT_Director', 'CISO'], 'timeout_hours': 1},
            email_draft={'subject': 'EMERGENCY: Manual Review Required', 'recipients': ['emergency@company.com'], 'cc': ['it.director@company.com'], 'body': 'EMERGENCY: Planning system error - immediate manual review required', 'attachments': [], 'urgency_note': 'IMMEDIATE ATTENTION REQUIRED'},
            risk_assessment={'risk_level': 'CRITICAL', 'risks': ['System error', 'Service disruption'], 'mitigation_strategies': ['Immediate manual intervention'], 'rollback_plan': 'Emergency procedures'},
            compliance_checklist=['Emergency_procedures_activated', 'Manual_review_required'],
            success_criteria=['Emergency resolved', 'Manual review completed'],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Persist emergency plan
        ticket_id = state.get('ticket_record', {}).get('ticket_id')
        request_id = state.get('user_request', {}).get('request_id')
        created_by = state.get('employee', {}).get('employee_id', 'system')
        
        emergency_plan_id = plan_repo.persist_plan(emergency_plan, ticket_id, request_id, created_by)
        emergency_plan['plan_id'] = emergency_plan_id
        
        state['plan_record'] = emergency_plan
        
        # Mark ticket as critical and requires approval
        if 'ticket_record' in state and state['ticket_record'].get('ticket_id'):
            ticket_id = state['ticket_record']['ticket_id']
            try:
                update_ticket_status(ticket_id, 'waiting_for_approval', 'EMERGENCY: Planning system error - immediate manual review required')
            except Exception as update_error:
                print(f"Failed to update ticket status: {update_error}")
        
        return state


# Convenience functions for testing and direct usage
def create_plan_record_model(plan_data: Dict[str, Any]) -> PlanRecordModel:
    """Create a PlanRecordModel from dictionary data"""
    return PlanRecordModel(**plan_data)


def create_plan_step_model(step_data: Dict[str, Any]) -> PlanStepModel:
    """Create a PlanStepModel from dictionary data"""
    return PlanStepModel(**step_data)


def test_planner_node():
    """Test function for the planner node"""
    # Create test state
    test_state = {
        'user_request': {
            'request_id': 'REQ_001',
            'title': 'Database Access Request',
            'description': 'Need read access to customer database for analytics',
            'category': 'access_control',
            'priority': 'MEDIUM',
            'department': 'data_science',
            'requested_by': 'emp_001',
            'submitted_at': datetime.now()
        },
        'decision_record': {
            'decision': 'REQUIRES_APPROVAL',
            'citations': [
                {
                    'source': 'IT_ACCESS_POLICY_001',
                    'text': 'Database access requires manager approval',
                    'relevance': 'Directly applicable policy'
                }
            ],
            'confidence': 0.85,
            'needs_human': True,
            'missing_fields': [],
            'justification_brief': 'Database access requires approval per policy'
        },
        'retrieved_docs': [
            {
                'doc_id': 'IT_ACCESS_POLICY_001',
                'title': 'IT Access Control Policy',
                'content': 'Database access requires manager approval...',
                'source': 'IT_Policies',
                'document_type': 'policy',
                'relevance_score': 0.95
            }
        ],
        'router_verdict': {
            'target_model': 'planner_model_v1',
            'reason': 'Standard complexity request'
        },
        'employee': {
            'employee_id': 'emp_001',
            'name': 'John Doe',
            'department': 'data_science'
        },
        'ticket_record': {
            'ticket_id': 'TICKET_001',
            'status': 'open'
        }
    }
    
    # Run planner node
    result_state = planner_node(test_state)
    
    print(f"Plan ID: {result_state['plan_record']['plan_id']}")
    print(f"Classification: {result_state['plan_record']['classification']}")
    print(f"Priority: {result_state['plan_record']['priority']}")
    print(f"Steps: {len(result_state['plan_record']['steps'])}")
    print(f"Requires Approval: {result_state['metadata']['planning']['requires_approval']}")
    
    return result_state


if __name__ == "__main__":
    # Run test if executed directly
    test_planner_node()
