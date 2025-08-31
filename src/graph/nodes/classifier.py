"""
Classifier Node for IT Support Workflow

This node calls the classifier LLM with the classifier prompt, parses JSON responses,
persists decision records, and sets human-in-the-loop pending when needed.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..state import (
    ITGraphState, DecisionRecord, DecisionRecordModel, RetrievedDocument, Citation,
    HILPending, HILPendingModel, DecisionType
)


@dataclass
class ClassificationInput:
    """Input data for classification"""
    user_request: Dict[str, Any]
    retrieved_docs: List[RetrievedDocument]
    past_tickets_features: List[Dict[str, Any]]
    router_verdict: Dict[str, Any]


@dataclass
class ClassificationResult:
    """Result of classification attempt"""
    success: bool
    decision_record: Optional[DecisionRecord] = None
    hil_pending: Optional[HILPending] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = None


class ClassifierPromptCaller:
    """Calls the classifier LLM with the classifier prompt"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.classifier_prompt_path = "src/prompts/classifier.md"
        self.max_retries = 3
    
    def call_classifier(self, input_data: ClassificationInput, 
                       target_model: str) -> str:
        """Call the classifier LLM with the prompt and input data"""
        # Read classifier prompt
        try:
            with open(self.classifier_prompt_path, 'r') as f:
                classifier_prompt = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Classifier prompt not found at {self.classifier_prompt_path}")
        
        # Prepare prompt input
        prompt_input = self._prepare_prompt_input(input_data)
        
        # Call LLM with retries
        for attempt in range(self.max_retries):
            try:
                if self.llm_client:
                    response = self.llm_client.call(
                        prompt=classifier_prompt,
                        input_data=prompt_input,
                        model=target_model
                    )
                    return response
                else:
                    # Mock response for testing
                    return self._generate_mock_response(input_data)
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                # Retry on failure
                continue
        
        raise Exception("Failed to get classifier response after all retries")
    
    def _prepare_prompt_input(self, input_data: ClassificationInput) -> Dict[str, Any]:
        """Prepare input data for classifier prompt"""
        # Format retrieved documents
        formatted_docs = []
        for doc in input_data.retrieved_docs:
            formatted_docs.append({
                'title': doc.title,
                'content': doc.content[:1000],  # Limit content length
                'source': doc.source,
                'document_type': doc.document_type,
                'relevance_score': doc.relevance_score
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
            'request': {
                'title': input_data.user_request.get('title', ''),
                'description': input_data.user_request.get('description', ''),
                'category': input_data.user_request.get('category', ''),
                'priority': input_data.user_request.get('priority', ''),
                'department': input_data.user_request.get('department', ''),
                'urgency': input_data.user_request.get('urgency', '')
            },
            'retrieved_snippets': formatted_docs,
            'past_ticket_patterns': formatted_tickets,
            'router_verdict': input_data.router_verdict
        }
    
    def _generate_mock_response(self, input_data: ClassificationInput) -> str:
        """Generate mock response for testing without LLM"""
        # Simple mock based on request category
        category = input_data.user_request.get('category', '').lower()
        
        if 'access' in category:
            decision = 'REQUIRES_APPROVAL'
            confidence = 0.85
            needs_human = True
        elif 'password' in category:
            decision = 'ALLOWED'
            confidence = 0.95
            needs_human = False
        else:
            decision = 'ALLOWED'
            confidence = 0.90
            needs_human = False
        
        mock_response = f"""
```json
{{
  "decision": "{decision}",
  "citations": [
    {{
      "source": "IT_Policy_Manual",
      "text": "Standard procedure for {category} requests",
      "relevance": "Directly applicable policy for this request type"
    }}
  ],
  "confidence": {confidence},
  "needs_human": {str(needs_human).lower()},
  "missing_fields": [],
  "justification_brief": "Request classified as {decision} based on standard policies and procedures."
}}
```
"""
        return mock_response


class JSONResponseParser:
    """Parses and validates JSON responses from classifier LLM"""
    
    def __init__(self):
        self.required_fields = ['decision', 'citations', 'confidence', 'needs_human', 'justification_brief']
        self.valid_decisions = ['ALLOWED', 'DENIED', 'REQUIRES_APPROVAL']
    
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
        
        # Validate decision
        if 'decision' in data:
            if data['decision'] not in self.valid_decisions:
                errors.append(f"Invalid decision: {data['decision']}. Must be one of {self.valid_decisions}")
        
        # Validate confidence
        if 'confidence' in data:
            confidence = data['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                errors.append(f"Invalid confidence: {confidence}. Must be float between 0 and 1")
        
        # Validate needs_human
        if 'needs_human' in data:
            if not isinstance(data['needs_human'], bool):
                errors.append(f"Invalid needs_human: {data['needs_human']}. Must be boolean")
        
        # Validate citations
        if 'citations' in data:
            if not isinstance(data['citations'], list):
                errors.append("Citations must be a list")
            elif len(data['citations']) == 0:
                errors.append("At least one citation is required")
            else:
                for i, citation in enumerate(data['citations']):
                    if not isinstance(citation, dict):
                        errors.append(f"Citation {i} must be a dictionary")
                    else:
                        citation_errors = self._validate_citation(citation, i)
                        errors.extend(citation_errors)
        
        return errors
    
    def _validate_citation(self, citation: Dict[str, Any], index: int) -> List[str]:
        """Validate individual citation structure"""
        errors = []
        required_citation_fields = ['source', 'text', 'relevance']
        
        for field in required_citation_fields:
            if field not in citation:
                errors.append(f"Citation {index} missing required field: {field}")
        
        return errors


class DecisionRepository:
    """Repository for persisting decision records"""
    
    def __init__(self, storage_client=None):
        self.storage_client = storage_client
        self.decisions = []  # In-memory storage for testing
    
    def persist_decision(self, decision_record: DecisionRecord) -> str:
        """Persist decision record and return record ID"""
        # Generate unique ID
        decision_id = f"decision_{datetime.now().timestamp()}_{len(self.decisions)}"
        
        # Add metadata
        decision_record['decision_id'] = decision_id
        decision_record['persisted_at'] = datetime.now()
        
        # Store decision
        if self.storage_client:
            # Real storage implementation
            self.storage_client.store('decisions', decision_id, decision_record)
        else:
            # In-memory storage for testing
            self.decisions.append(decision_record)
        
        return decision_id
    
    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """Retrieve decision record by ID"""
        if self.storage_client:
            return self.storage_client.retrieve('decisions', decision_id)
        else:
            # In-memory lookup
            for decision in self.decisions:
                if decision.get('decision_id') == decision_id:
                    return decision
        return None


class HILManager:
    """Manages human-in-the-loop pending items"""
    
    def __init__(self):
        self.hil_items = []
    
    def create_hil_pending(self, decision_record: DecisionRecord, 
                          reason: str) -> HILPending:
        """Create HIL pending item for decision requiring human review"""
        hil_item = HILPending(
            item_id=f"hil_{datetime.now().timestamp()}",
            type="classification_review",
            description=f"Human review required for {decision_record['decision']} decision: {reason}",
            assigned_to="unassigned",
            priority="MEDIUM",
            created_at=datetime.now(),
            due_date=datetime.now().replace(hour=23, minute=59),  # Due by end of day
            status="pending",
            escalation_path=["supervisor", "manager"],
            timeout_hours=24
        )
        
        self.hil_items.append(hil_item)
        return hil_item


def classifier_node(state: ITGraphState) -> ITGraphState:
    """
    Classifier node: calls classifier LLM, parses response, persists decision
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with decision_record and potential hil_pending
    """
    try:
        # Initialize components
        prompt_caller = ClassifierPromptCaller()
        json_parser = JSONResponseParser()
        decision_repo = DecisionRepository()
        hil_manager = HILManager()
        
        # Prepare classification input
        input_data = ClassificationInput(
            user_request=state.get('user_request', {}),
            retrieved_docs=state.get('retrieved_docs', []),
            past_tickets_features=state.get('metadata', {}).get('past_tickets', []),
            router_verdict=state.get('router_verdict', {})
        )
        
        # Get target model from router verdict
        target_model = state.get('router_verdict', {}).get('target_model', 'standard_model_v1')
        
        # Call classifier LLM
        llm_response = prompt_caller.call_classifier(input_data, target_model)
        
        # Parse JSON response
        parse_success, json_data, validation_errors = json_parser.parse_response(llm_response)
        
        if not parse_success:
            # Handle parsing/validation errors
            error_record = {
                'error_id': f"classification_error_{datetime.now().timestamp()}",
                'timestamp': datetime.now(),
                'error_type': 'classification_parsing_error',
                'message': f"Failed to parse classifier response: {validation_errors}",
                'stack_trace': None,
                'context': {
                    'node': 'classifier',
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
            
            # Create fallback decision record
            fallback_decision = DecisionRecord(
                decision='REQUIRES_APPROVAL',
                citations=[],
                confidence=0.0,
                needs_human=True,
                missing_fields=['valid_classification_response'],
                justification_brief='Classification failed due to parsing errors. Manual review required.',
                decision_date=datetime.now(),
                decision_model=target_model,
                policy_references=[],
                risk_assessment={'risk_level': 'HIGH', 'reason': 'Classification parsing failed'}
            )
            
            state['decision_record'] = fallback_decision
            
            # Set HIL pending for manual review
            hil_item = hil_manager.create_hil_pending(
                fallback_decision, 
                "Classification parsing failed - manual review required"
            )
            
            if 'hil_pending' not in state:
                state['hil_pending'] = []
            state['hil_pending'].append(hil_item)
            
            return state
        
        # Create decision record from parsed data
        decision_record = DecisionRecord(
            decision=DecisionType(json_data['decision']),
            citations=[
                Citation(
                    source=citation['source'],
                    text=citation['text'],
                    relevance=citation['relevance'],
                    document_id=citation.get('document_id', ''),
                    page_number=citation.get('page_number'),
                    section=citation.get('section')
                )
                for citation in json_data['citations']
            ],
            confidence=float(json_data['confidence']),
            needs_human=bool(json_data['needs_human']),
            missing_fields=json_data.get('missing_fields', []),
            justification_brief=json_data['justification_brief'],
            decision_date=datetime.now(),
            decision_model=target_model,
            policy_references=[citation['source'] for citation in json_data['citations']],
            risk_assessment={
                'risk_level': 'HIGH' if json_data['decision'] == 'DENIED' else 'MEDIUM',
                'reason': json_data['justification_brief'][:100]
            }
        )
        
        # Persist decision record
        decision_id = decision_repo.persist_decision(decision_record)
        decision_record['decision_id'] = decision_id
        
        # Update state with decision record
        state['decision_record'] = decision_record
        
        # Check if HIL is needed
        needs_hil = (decision_record['needs_human'] or 
                    decision_record['confidence'] < 0.6)
        
        if needs_hil:
            # Create HIL pending item
            hil_reason = "Low confidence" if decision_record['confidence'] < 0.6 else "Human review required"
            hil_item = hil_manager.create_hil_pending(decision_record, hil_reason)
            
            if 'hil_pending' not in state:
                state['hil_pending'] = []
            state['hil_pending'].append(hil_item)
        
        # Add classification metadata
        if 'metadata' not in state:
            state['metadata'] = {}
        state['metadata']['classification'] = {
            'decision': decision_record['decision'],
            'confidence': decision_record['confidence'],
            'needs_human': decision_record['needs_human'],
            'citations_count': len(decision_record['citations']),
            'missing_fields': decision_record['missing_fields'],
            'classification_timestamp': datetime.now().isoformat(),
            'model_used': target_model,
            'hil_pending': needs_hil
        }
        
        return state
        
    except Exception as e:
        # Handle unexpected errors
        error_record = {
            'error_id': f"classification_error_{datetime.now().timestamp()}",
            'timestamp': datetime.now(),
            'error_type': 'classification_error',
            'message': f"Unexpected error in classifier node: {str(e)}",
            'stack_trace': None,
            'context': {'node': 'classifier', 'state_keys': list(state.keys())},
            'severity': 'critical',
            'resolved': False,
            'resolution_notes': None
        }
        
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(error_record)
        
        # Create emergency fallback decision
        emergency_decision = DecisionRecord(
            decision='REQUIRES_APPROVAL',
            citations=[],
            confidence=0.0,
            needs_human=True,
            missing_fields=['classification_system_error'],
            justification_brief='Classification system error occurred. Emergency manual review required.',
            decision_date=datetime.now(),
            decision_model='emergency_fallback',
            policy_references=[],
            risk_assessment={'risk_level': 'CRITICAL', 'reason': 'System error'}
        )
        
        state['decision_record'] = emergency_decision
        
        # Set HIL pending for emergency review
        if 'hil_pending' not in state:
            state['hil_pending'] = []
        
        emergency_hil = HILPending(
            item_id=f"emergency_hil_{datetime.now().timestamp()}",
            type="emergency_classification_review",
            description="EMERGENCY: Classification system error - immediate human review required",
            assigned_to="emergency_team",
            priority="CRITICAL",
            created_at=datetime.now(),
            due_date=datetime.now().replace(hour=1, minute=0),  # Due in 1 hour
            status="urgent",
            escalation_path=["supervisor", "manager", "emergency_team"],
            timeout_hours=1
        )
        
        state['hil_pending'].append(emergency_hil)
        
        return state


# Convenience functions for testing and direct usage
def create_decision_record_model(decision_data: Dict[str, Any]) -> DecisionRecordModel:
    """Create a DecisionRecordModel from dictionary data"""
    return DecisionRecordModel(**decision_data)


def create_hil_pending_model(hil_data: Dict[str, Any]) -> HILPendingModel:
    """Create a HILPendingModel from dictionary data"""
    return HILPendingModel(**hil_data)


def test_classifier_node():
    """Test function for the classifier node"""
    # Create test state
    test_state = {
        'user_request': {
            'title': 'Database Access Request',
            'description': 'Need read access to customer database for analytics',
            'category': 'access_control',
            'priority': 'MEDIUM',
            'department': 'data_science'
        },
        'retrieved_docs': [
            {
                'doc_id': 'IT_ACCESS_POLICY_001',
                'title': 'IT Access Control Policy',
                'content': 'Standard access requests require manager approval...',
                'source': 'IT_Policies',
                'document_type': 'policy',
                'version': '2.1',
                'last_updated': datetime.now(),
                'metadata': {'category': 'security'}
            }
        ],
        'router_verdict': {
            'target_model': 'standard_model_v1',
            'reason': 'Standard complexity request'
        },
        'citations': []
    }
    
    # Run classifier node
    result_state = classifier_node(test_state)
    
    print(f"Decision: {result_state['decision_record']['decision']}")
    print(f"Confidence: {result_state['decision_record']['confidence']}")
    print(f"HIL Pending: {len(result_state.get('hil_pending', []))}")
    
    return result_state


if __name__ == "__main__":
    # Run test if executed directly
    test_classifier_node()
