"""
Router Node for IT Support Workflow

This node evaluates request complexity, calls the router prompt for model selection,
and updates the state with router verdict and selected LLM handle.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..state import (
    ITGraphState, RouterVerdict, RouterVerdictModel, RetrievedDocument, Citation
)


@dataclass
class ComplexityMetrics:
    """Complexity assessment metrics"""
    token_count: int
    policy_conflicts: int
    novelty_score: float
    complexity_level: str
    reasoning_required: bool
    risk_level: str


@dataclass
class PolicyConflict:
    """Represents a policy conflict"""
    conflict_id: str
    policy_a: str
    policy_b: str
    conflict_description: str
    severity: str
    resolution_approach: str


class ComplexityEvaluator:
    """Evaluates request complexity based on multiple factors"""
    
    def __init__(self):
        self.complexity_thresholds = {
            'SIMPLE': {'max_tokens': 100, 'max_conflicts': 0, 'max_novelty': 0.3},
            'MODERATE': {'max_tokens': 300, 'max_conflicts': 1, 'max_novelty': 0.6},
            'COMPLEX': {'max_tokens': float('inf'), 'max_conflicts': float('inf'), 'max_novelty': float('inf')}
        }
        
        self.policy_keywords = [
            'policy', 'procedure', 'guideline', 'rule', 'requirement', 'standard',
            'compliance', 'regulation', 'audit', 'security', 'access', 'permission'
        ]
    
    def evaluate_complexity(self, state: ITGraphState) -> ComplexityMetrics:
        """Evaluate overall request complexity"""
        # Count tokens in request
        token_count = self._count_tokens(state)
        
        # Detect policy conflicts
        policy_conflicts = self._detect_policy_conflicts(state)
        conflict_count = len(policy_conflicts)
        
        # Calculate novelty score
        novelty_score = self._calculate_novelty_score(state)
        
        # Determine complexity level
        complexity_level = self._determine_complexity_level(token_count, conflict_count, novelty_score)
        
        # Assess reasoning requirements
        reasoning_required = self._assess_reasoning_requirements(state, complexity_level)
        
        # Assess risk level
        risk_level = self._assess_risk_level(state, complexity_level)
        
        return ComplexityMetrics(
            token_count=token_count,
            policy_conflicts=conflict_count,
            novelty_score=novelty_score,
            complexity_level=complexity_level,
            reasoning_required=reasoning_required,
            risk_level=risk_level
        )
    
    def _count_tokens(self, state: ITGraphState) -> int:
        """Count approximate tokens in the request"""
        user_request = state.get('user_request', {})
        
        # Combine title and description
        text = f"{user_request.get('title', '')} {user_request.get('description', '')}"
        
        # Simple token approximation (words + punctuation)
        words = len(text.split())
        punctuation = len(re.findall(r'[^\w\s]', text))
        
        return words + punctuation
    
    def _detect_policy_conflicts(self, state: ITGraphState) -> List[PolicyConflict]:
        """Detect conflicts between retrieved policies"""
        conflicts = []
        retrieved_docs = state.get('retrieved_docs', [])
        citations = state.get('citations', [])
        
        if len(retrieved_docs) < 2:
            return conflicts
        
        # Compare policies for conflicts
        for i, doc_a in enumerate(retrieved_docs):
            for j, doc_b in enumerate(retrieved_docs[i+1:], i+1):
                conflict = self._compare_policies_for_conflicts(doc_a, doc_b)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _compare_policies_for_conflicts(self, doc_a, doc_b) -> Optional[PolicyConflict]:
        """Compare two policies for potential conflicts"""
        # Handle both TypedDict and dict objects
        if hasattr(doc_a, 'content'):
            content_a = doc_a.content
            title_a = doc_a.title
            doc_id_a = doc_a.doc_id
        else:
            content_a = doc_a.get('content', '')
            title_a = doc_a.get('title', '')
            doc_id_a = doc_a.get('doc_id', '')
            
        if hasattr(doc_b, 'content'):
            content_b = doc_b.content
            title_b = doc_b.title
            doc_id_b = doc_b.doc_id
        else:
            content_b = doc_b.get('content', '')
            title_b = doc_b.get('title', '')
            doc_id_b = doc_b.get('doc_id', '')
        
        # Extract key policy statements
        statements_a = self._extract_policy_statements(content_a)
        statements_b = self._extract_policy_statements(content_b)
        
        # Look for conflicting requirements
        for stmt_a in statements_a:
            for stmt_b in statements_b:
                if self._statements_conflict(stmt_a, stmt_b):
                    conflict_id = f"conflict_{hash(f'{doc_id_a}_{doc_id_b}_{stmt_a[:20]}')}"
                    
                    return PolicyConflict(
                        conflict_id=conflict_id,
                        policy_a=title_a,
                        policy_b=title_b,
                        conflict_description=f"Conflict between '{stmt_a[:100]}' and '{stmt_b[:100]}'",
                        severity="medium",
                        resolution_approach="Requires policy reconciliation or exception approval"
                    )
        
        return None
    
    def _extract_policy_statements(self, content: str) -> List[str]:
        """Extract key policy statements from content"""
        statements = []
        
        # Look for policy-like sentences
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Minimum length for meaningful policy statement
                # Check if sentence contains policy keywords
                if any(keyword in sentence.lower() for keyword in self.policy_keywords):
                    statements.append(sentence)
        
        return statements
    
    def _statements_conflict(self, stmt_a: str, stmt_b: str) -> bool:
        """Check if two policy statements conflict"""
        # Simple conflict detection based on opposing terms
        opposing_pairs = [
            ('require', 'prohibit'), ('allow', 'deny'), ('must', 'cannot'),
            ('mandatory', 'optional'), ('always', 'never'), ('enable', 'disable')
        ]
        
        stmt_a_lower = stmt_a.lower()
        stmt_b_lower = stmt_b.lower()
        
        for term_a, term_b in opposing_pairs:
            if term_a in stmt_a_lower and term_b in stmt_b_lower:
                return True
            if term_b in stmt_a_lower and term_a in stmt_b_lower:
                return True
        
        return False
    
    def _calculate_novelty_score(self, state: ITGraphState) -> float:
        """Calculate how novel this request is compared to past patterns"""
        # This would integrate with past ticket analysis
        # For now, use a simple heuristic based on request content
        
        user_request = state.get('user_request', {})
        title = user_request.get('title', '').lower()
        description = user_request.get('description', '').lower()
        
        # Common request patterns
        common_patterns = [
            'password reset', 'software install', 'access request', 'email setup',
            'hardware request', 'account creation', 'permission change'
        ]
        
        # Check how many common patterns match
        matches = sum(1 for pattern in common_patterns if pattern in title or pattern in description)
        
        # Novelty is inverse of pattern matches
        novelty_score = 1.0 - (matches / len(common_patterns))
        
        return max(0.0, min(1.0, novelty_score))
    
    def _determine_complexity_level(self, token_count: int, conflict_count: int, 
                                  novelty_score: float) -> str:
        """Determine overall complexity level"""
        # Check against thresholds
        for level, thresholds in self.complexity_thresholds.items():
            if (token_count <= thresholds['max_tokens'] and 
                conflict_count <= thresholds['max_conflicts'] and 
                novelty_score <= thresholds['max_novelty']):
                return level
        
        return 'COMPLEX'
    
    def _assess_reasoning_requirements(self, state: ITGraphState, complexity_level: str) -> bool:
        """Assess if advanced reasoning is required"""
        if complexity_level == 'COMPLEX':
            return True
        
        # Check for specific indicators
        user_request = state.get('user_request', {})
        description = user_request.get('description', '').lower()
        
        reasoning_indicators = [
            'exception', 'special case', 'unusual', 'complex', 'multiple systems',
            'cross-department', 'high risk', 'security', 'compliance', 'audit'
        ]
        
        return any(indicator in description for indicator in reasoning_indicators)
    
    def _assess_risk_level(self, state: ITGraphState, complexity_level: str) -> str:
        """Assess risk level of the request"""
        user_request = state.get('user_request', {})
        category = user_request.get('category', '').lower()
        priority = user_request.get('priority', '').lower()
        
        # High-risk categories
        high_risk_categories = ['security', 'access', 'admin', 'privilege', 'system']
        if any(risk_cat in category for risk_cat in high_risk_categories):
            return 'HIGH'
        
        # High-risk priorities
        if priority in ['high', 'critical']:
            return 'HIGH'
        
        # Complexity-based risk
        if complexity_level == 'COMPLEX':
            return 'MEDIUM'
        
        return 'LOW'


class ModelSelector:
    """Selects appropriate model based on complexity and requirements"""
    
    def __init__(self):
        self.available_models = {
            'basic': {
                'name': 'basic_model_v1',
                'capabilities': 'LOW',
                'resource_cost': 'LOW',
                'max_complexity': 'SIMPLE',
                'confidence_threshold': 0.90
            },
            'standard': {
                'name': 'standard_model_v1',
                'capabilities': 'MEDIUM',
                'resource_cost': 'MEDIUM',
                'max_complexity': 'MODERATE',
                'confidence_threshold': 0.85
            },
            'advanced': {
                'name': 'advanced_model_v1',
                'capabilities': 'HIGH',
                'resource_cost': 'HIGH',
                'max_complexity': 'COMPLEX',
                'confidence_threshold': 0.80
            }
        }
    
    def select_model(self, complexity_metrics: ComplexityMetrics, 
                    policy_conflicts: List[PolicyConflict]) -> Dict[str, Any]:
        """Select the most appropriate model"""
        # Determine required capability level
        if complexity_metrics.complexity_level == 'COMPLEX' or complexity_metrics.reasoning_required:
            required_capability = 'HIGH'
        elif complexity_metrics.complexity_level == 'MODERATE':
            required_capability = 'MEDIUM'
        else:
            required_capability = 'LOW'
        
        # Check for mandatory escalation conditions
        escalation_needed = False
        escalation_reason = None
        
        if policy_conflicts:
            escalation_needed = True
            escalation_reason = f"Policy conflicts detected: {len(policy_conflicts)} conflicts found"
        elif complexity_metrics.risk_level == 'HIGH':
            escalation_needed = True
            escalation_reason = "High-risk request requiring advanced model"
        elif complexity_metrics.complexity_level == 'COMPLEX':
            escalation_needed = True
            escalation_reason = "Complex request requiring advanced reasoning"
        
        # Select model based on requirements
        if required_capability == 'HIGH' or escalation_needed:
            selected_model = self.available_models['advanced']
        elif required_capability == 'MEDIUM':
            selected_model = self.available_models['standard']
        else:
            selected_model = self.available_models['basic']
        
        return {
            'model_name': selected_model['name'],
            'capability_level': selected_model['capabilities'],
            'resource_cost': selected_model['resource_cost'],
            'escalation_needed': escalation_needed,
            'escalation_reason': escalation_reason,
            'confidence_threshold': selected_model['confidence_threshold']
        }


class RouterPromptCaller:
    """Calls the router prompt for model selection"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.router_prompt_path = "src/prompts/router.md"
    
    def call_router_prompt(self, state: ITGraphState, complexity_metrics: ComplexityMetrics,
                          model_selection: Dict[str, Any]) -> RouterVerdict:
        """Call the router prompt to get final routing decision"""
        # Read router prompt
        try:
            with open(self.router_prompt_path, 'r') as f:
                router_prompt = f.read()
        except FileNotFoundError:
            # Fallback if prompt file not found
            return self._create_fallback_verdict(state, complexity_metrics, model_selection)
        
        # Prepare input for router prompt
        prompt_input = self._prepare_prompt_input(state, complexity_metrics, model_selection)
        
        # Call LLM with router prompt
        if self.llm_client:
            try:
                response = self.llm_client.call(
                    prompt=router_prompt,
                    input_data=prompt_input,
                    model=model_selection['model_name']
                )
                
                # Parse response
                return self._parse_router_response(response)
            except Exception as e:
                # Fallback on LLM error
                return self._create_fallback_verdict(state, complexity_metrics, model_selection)
        else:
            # No LLM client, use fallback
            return self._create_fallback_verdict(state, complexity_metrics, model_selection)
    
    def _prepare_prompt_input(self, state: ITGraphState, complexity_metrics: ComplexityMetrics,
                             model_selection: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input data for router prompt"""
        user_request = state.get('user_request', {})
        retrieved_docs = state.get('retrieved_docs', [])
        
        return {
            'request_details': {
                'title': user_request.get('title', ''),
                'description': user_request.get('description', ''),
                'category': user_request.get('category', ''),
                'priority': user_request.get('priority', ''),
                'department': user_request.get('department', '')
            },
            'complexity_analysis': {
                'level': complexity_metrics.complexity_level,
                'token_count': complexity_metrics.token_count,
                'policy_conflicts': complexity_metrics.policy_conflicts,
                'novelty_score': complexity_metrics.novelty_score,
                'reasoning_required': complexity_metrics.reasoning_required,
                'risk_level': complexity_metrics.risk_level
            },
            'retrieval_results': {
                'document_count': len(retrieved_docs),
                'sources': [doc.get('source', 'unknown') for doc in retrieved_docs],
                'document_types': [doc.get('document_type', 'unknown') for doc in retrieved_docs]
            },
            'model_selection': model_selection
        }
    
    def _parse_router_response(self, response: str) -> RouterVerdict:
        """Parse LLM response into RouterVerdict"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                
                return RouterVerdict(
                    target_model=data.get('target_model', 'standard_model_v1'),
                    reason=data.get('reason', 'Model selected based on complexity analysis'),
                    escalation_needed=data.get('escalation_needed', False),
                    escalation_reason=data.get('escalation_reason'),
                    model_capabilities=data.get('model_capabilities', {}),
                    request_analysis=data.get('request_analysis', {}),
                    routing_decision=data.get('routing_decision', {}),
                    quality_metrics=data.get('quality_metrics', {})
                )
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Fallback to default verdict
        return RouterVerdict(
            target_model='standard_model_v1',
            reason='Fallback model selection due to parsing error',
            escalation_needed=False,
            escalation_reason=None,
            model_capabilities={},
            request_analysis={},
            routing_decision={},
            quality_metrics={}
        )
    
    def _create_fallback_verdict(self, state: ITGraphState, complexity_metrics: ComplexityMetrics,
                                model_selection: Dict[str, Any]) -> RouterVerdict:
        """Create fallback router verdict when prompt call fails"""
        return RouterVerdict(
            target_model=model_selection['model_name'],
            reason=f"Fallback selection: {complexity_metrics.complexity_level} complexity requires {model_selection['capability_level']} capabilities",
            escalation_needed=model_selection['escalation_needed'],
            escalation_reason=model_selection['escalation_reason'],
            model_capabilities={
                'complexity_handling': model_selection['capability_level'],
                'policy_knowledge': 'COMPREHENSIVE' if model_selection['capability_level'] == 'HIGH' else 'BASIC',
                'reasoning_ability': 'ADVANCED' if model_selection['capability_level'] == 'HIGH' else 'SIMPLE',
                'resource_cost': model_selection['resource_cost']
            },
            request_analysis={
                'complexity': complexity_metrics.complexity_level,
                'policy_requirements': 'ADVANCED' if complexity_metrics.reasoning_required else 'BASIC',
                'confidence_required': model_selection['confidence_threshold'],
                'retrieval_quality': 'HIGH' if state.get('retrieved_docs') else 'LOW'
            },
            routing_decision={
                'primary_model': model_selection['model_name'],
                'fallback_model': 'human_review' if model_selection['escalation_needed'] else 'standard_model_v1',
                'escalation_path': ['human_review'] if model_selection['escalation_needed'] else [],
                'timeout_seconds': 60 if model_selection['escalation_needed'] else 30
            },
            quality_metrics={
                'expected_accuracy': model_selection['confidence_threshold'],
                'response_time_estimate': '5_seconds' if model_selection['capability_level'] == 'HIGH' else '2_seconds',
                'resource_efficiency': 'LOW' if model_selection['capability_level'] == 'HIGH' else 'HIGH'
            }
        )


def router_node(state: ITGraphState) -> ITGraphState:
    """
    Router node: evaluates complexity, calls router prompt, sets router_verdict
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with router_verdict and selected model
    """
    print("\n" + "="*80)
    print("🔄 ROUTER NODE: STARTING EXECUTION")
    print("="*80)
    
    try:
        print(f"🔄 ROUTER: Starting router node execution")
        print(f"🔄 ROUTER: State keys: {list(state.keys())}")
        
        # Initialize components
        complexity_evaluator = ComplexityEvaluator()
        model_selector = ModelSelector()
        router_caller = RouterPromptCaller()
        
        # Evaluate complexity
        complexity_metrics = complexity_evaluator.evaluate_complexity(state)
        
        # Detect policy conflicts
        policy_conflicts = complexity_evaluator._detect_policy_conflicts(state)
        
        # Select appropriate model
        model_selection = model_selector.select_model(complexity_metrics, policy_conflicts)
        
        # Call router prompt for final decision
        router_verdict = router_caller.call_router_prompt(state, complexity_metrics, model_selection)
        
        # Update state with router verdict
        state['router_verdict'] = router_verdict
        
        # Add routing metadata
        if 'metadata' not in state:
            state['metadata'] = {}
        state['metadata']['routing'] = {
            'complexity_metrics': {
                'level': complexity_metrics.complexity_level,
                'token_count': complexity_metrics.token_count,
                'policy_conflicts': complexity_metrics.policy_conflicts,
                'novelty_score': complexity_metrics.novelty_score,
                'reasoning_required': complexity_metrics.reasoning_required,
                'risk_level': complexity_metrics.risk_level
            },
            'model_selection': model_selection,
            'routing_timestamp': datetime.now().isoformat(),
            'policy_conflicts': [
                {
                    'conflict_id': conflict.conflict_id,
                    'description': conflict.conflict_description,
                    'severity': conflict.severity
                }
                for conflict in policy_conflicts
            ]
        }
        
        return state
        
    except Exception as e:
        # Handle errors gracefully
        error_record = {
            'error_id': f"routing_error_{datetime.now().timestamp()}",
            'timestamp': datetime.now(),
            'error_type': 'routing_error',
            'message': f"Error in router node: {str(e)}",
            'stack_trace': None,
            'context': {'node': 'router', 'state_keys': list(state.keys())},
            'severity': 'high',
            'resolved': False,
            'resolution_notes': None
        }
        
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(error_record)
        
        # Return state with fallback router verdict
        fallback_verdict = RouterVerdict(
            target_model='standard_model_v1',
            reason='Fallback model due to routing error',
            escalation_needed=True,
            escalation_reason='Routing error occurred, defaulting to standard model',
            model_capabilities={},
            request_analysis={},
            routing_decision={},
            quality_metrics={}
        )
        
        state['router_verdict'] = fallback_verdict
        return state


# Convenience functions for testing and direct usage
def create_router_verdict_model(verdict_data: Dict[str, Any]) -> RouterVerdictModel:
    """Create a RouterVerdictModel from dictionary data"""
    return RouterVerdictModel(**verdict_data)


def test_router_node():
    """Test function for the router node"""
    # Create test state
    test_state = {
        'user_request': {
            'title': 'Administrative Database Access',
            'description': 'Need elevated access to production database for data analysis project',
            'category': 'access_control',
            'priority': 'HIGH',
            'department': 'data_science'
        },
        'retrieved_docs': [
            {
                'doc_id': 'IT_ACCESS_POLICY_001',
                'title': 'IT Access Control Policy',
                'content': 'Administrative access requires manager approval...',
                'source': 'IT_Policies',
                'document_type': 'policy',
                'version': '2.1',
                'last_updated': datetime.now(),
                'metadata': {'category': 'security'}
            }
        ],
        'citations': []
    }
    
    # Run router node
    result_state = router_node(test_state)
    
    print(f"Router verdict: {result_state['router_verdict']['target_model']}")
    print(f"Escalation needed: {result_state['router_verdict']['escalation_needed']}")
    
    return result_state


if __name__ == "__main__":
    # Run test if executed directly
    test_router_node()
