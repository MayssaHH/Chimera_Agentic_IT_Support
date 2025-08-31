"""
IT Agent Node for IT Support Workflow

This node executes what is executable from the plan:
- Send approval emails via email tool
- Post user guides for manual steps
- Update ticket fields via Jira tool
- Return execution outcome status
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..state import (
    ITGraphState, PlanRecord, PlanStep, TicketRecord, DecisionType, ActorType
)
# Mock clients for testing without full configuration
class MockEmailClient:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
    
    def send_email(self, **kwargs):
        return {"success": True, "message": "Mock email sent", "dry_run": self.dry_run}

class MockJiraClient:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
    
    def update_ticket(self, **kwargs):
        return {"success": True, "message": "Mock ticket updated", "dry_run": self.dry_run}
    
    def add_comment(self, **kwargs):
        return {"success": True, "message": "Mock comment added", "dry_run": self.dry_run}

# Use mock clients for now - can be replaced with real clients when configuration is available
EmailClient = MockEmailClient
JiraClient = MockJiraClient
TOOLS_AVAILABLE = False


logger = logging.getLogger(__name__)


class ExecutionOutcome(str, Enum):
    """Possible execution outcomes"""
    EXECUTED = "executed"
    AWAITING_EMPLOYEE = "awaiting_employee"
    AWAITING_MANAGER = "awaiting_manager"


@dataclass
class ExecutableAction:
    """Represents an action that can be executed"""
    step_id: str
    action_type: str
    tool: str
    parameters: Dict[str, Any]
    preconditions_met: bool
    estimated_duration: int
    automation_level: str


@dataclass
class UserGuide:
    """User guide for manual steps"""
    title: str
    introduction: str
    steps: List[Dict[str, Any]]
    completion_criteria: List[str]
    next_steps: str


class ExecutionEngine:
    """Engine for executing automated actions"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run or not TOOLS_AVAILABLE
        self.email_client = EmailClient(dry_run=self.dry_run)
        self.jira_client = JiraClient(dry_run=self.dry_run)
        
    def execute_action(self, action: ExecutableAction, state: ITGraphState) -> Dict[str, Any]:
        """Execute a single action using the appropriate tool"""
        try:
            if action.tool == "email":
                return self._execute_email_action(action, state)
            elif action.tool == "jira":
                return self._execute_jira_action(action, state)
            elif action.tool == "system":
                return self._execute_system_action(action, state)
            else:
                logger.warning(f"Unknown tool type: {action.tool}")
                return {"success": False, "error": f"Unknown tool: {action.tool}"}
                
        except Exception as e:
            logger.error(f"Error executing action {action.step_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_email_action(self, action: ExecutableAction, state: ITGraphState) -> Dict[str, Any]:
        """Execute email-related actions"""
        params = action.parameters
        
        try:
            # Send email using email client
            email_result = self.email_client.send_email(
                subject=params.get("subject", "IT Support Notification"),
                body=params.get("body", ""),
                recipients=params.get("recipients", []),
                cc=params.get("cc", []),
                attachments=params.get("attachments", []),
                priority=params.get("priority", "MEDIUM")
            )
            
            return {
                "success": True,
                "action_id": action.step_id,
                "result": email_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email action failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_jira_action(self, action: ExecutableAction, state: ITGraphState) -> Dict[str, Any]:
        """Execute Jira-related actions"""
        params = action.parameters
        action_type = params.get("action_type", "update")
        
        try:
            if action_type == "update":
                # Update ticket fields
                ticket_id = params.get("ticket_id")
                if not ticket_id:
                    return {"success": False, "error": "No ticket ID provided"}
                
                update_fields = params.get("fields", {})
                comment = params.get("comment", "")
                
                # Update ticket via Jira client
                update_result = self.jira_client.update_ticket(
                    ticket_id=ticket_id,
                    fields=update_fields,
                    comment=comment
                )
                
                return {
                    "success": True,
                    "action_id": action.step_id,
                    "result": update_result,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif action_type == "comment":
                # Add comment to ticket
                ticket_id = params.get("ticket_id")
                comment = params.get("comment", "")
                
                if not ticket_id or not comment:
                    return {"success": False, "error": "Missing ticket ID or comment"}
                
                comment_result = self.jira_client.add_comment(
                    ticket_id=ticket_id,
                    comment=comment
                )
                
                return {
                    "success": True,
                    "action_id": action.step_id,
                    "result": comment_result,
                    "timestamp": datetime.now().isoformat()
                }
                
            else:
                return {"success": False, "error": f"Unknown Jira action type: {action_type}"}
                
        except Exception as e:
            logger.error(f"Jira action failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_system_action(self, action: ExecutableAction, state: ITGraphState) -> Dict[str, Any]:
        """Execute system-related actions"""
        # For now, just log system actions
        logger.info(f"System action {action.step_id} would execute: {action.parameters}")
        
        return {
            "success": True,
            "action_id": action.step_id,
            "result": "System action logged (dry run mode)",
            "timestamp": datetime.now().isoformat()
        }


class UserGuideGenerator:
    """Generates user guides for manual steps"""
    
    def generate_user_guide(self, manual_steps: List[PlanStep], state: ITGraphState) -> UserGuide:
        """Generate a user guide for manual steps"""
        if not manual_steps:
            return None
            
        # Group steps by actor type
        employee_steps = [step for step in manual_steps if step.get("actor") == ActorType.EMPLOYEE]
        manager_steps = [step for step in manual_steps if step.get("actor") == ActorType.MANAGER_APPROVAL]
        
        # Determine guide title based on steps
        if employee_steps and manager_steps:
            title = "Complete Required Steps and Obtain Manager Approval"
        elif employee_steps:
            title = "Complete Required Steps"
        elif manager_steps:
            title = "Manager Approval Required"
        else:
            title = "Action Required"
        
        # Generate introduction
        introduction = self._generate_introduction(employee_steps, manager_steps, state)
        
        # Generate steps
        steps = self._generate_steps(employee_steps + manager_steps)
        
        # Generate completion criteria
        completion_criteria = self._generate_completion_criteria(employee_steps, manager_steps)
        
        # Generate next steps
        next_steps = self._generate_next_steps(state)
        
        return UserGuide(
            title=title,
            introduction=introduction,
            steps=steps,
            completion_criteria=completion_criteria,
            next_steps=next_steps
        )
    
    def _generate_introduction(self, employee_steps: List[PlanStep], 
                             manager_steps: List[PlanStep], state: ITGraphState) -> str:
        """Generate introduction text for the user guide"""
        user_request = state.get("user_request", {})
        request_title = user_request.get("title", "your request")
        
        intro_parts = [f"To proceed with {request_title}, you need to complete the following steps:"]
        
        if employee_steps:
            intro_parts.append(f"• {len(employee_steps)} step(s) that you can complete")
        
        if manager_steps:
            intro_parts.append(f"• {len(manager_steps)} step(s) requiring manager approval")
        
        intro_parts.append("Please complete all steps in the order shown below.")
        
        return " ".join(intro_parts)
    
    def _generate_steps(self, steps: List[PlanStep]) -> List[Dict[str, Any]]:
        """Generate step-by-step instructions"""
        generated_steps = []
        
        for i, step in enumerate(steps, 1):
            step_data = {
                "step_number": i,
                "title": step.get("description", f"Step {i}"),
                "description": step.get("description", ""),
                "estimated_time": f"{step.get('estimated_duration', 30)} minutes",
                "required_materials": step.get("preconditions", []),
                "instructions": self._extract_instructions(step),
                "examples": step.get("actor_details", ""),
                "contact_info": "Contact IT Support if you need assistance",
                "deadline": "Complete as soon as possible"
            }
            generated_steps.append(step_data)
        
        return generated_steps
    
    def _extract_instructions(self, step: PlanStep) -> List[str]:
        """Extract specific instructions from a step"""
        description = step.get("description", "")
        
        # Simple instruction extraction - split by sentences and format
        sentences = description.split(". ")
        instructions = []
        
        for sentence in sentences:
            if sentence.strip():
                # Capitalize first letter and ensure it ends with period
                instruction = sentence.strip().capitalize()
                if not instruction.endswith("."):
                    instruction += "."
                instructions.append(instruction)
        
        return instructions if instructions else ["Follow the step description above."]
    
    def _generate_completion_criteria(self, employee_steps: List[PlanStep], 
                                    manager_steps: List[PlanStep]) -> List[str]:
        """Generate completion criteria"""
        criteria = []
        
        if employee_steps:
            criteria.append("All employee steps completed")
        
        if manager_steps:
            criteria.append("All manager approvals obtained")
        
        criteria.extend([
            "All required documentation submitted",
            "No pending questions or clarifications"
        ])
        
        return criteria
    
    def _generate_next_steps(self, state: ITGraphState) -> str:
        """Generate next steps description"""
        decision_record = state.get("decision_record", {})
        decision = decision_record.get("decision", DecisionType.ALLOWED)
        
        if decision == DecisionType.ALLOWED:
            return "After completing these steps, your request will be processed and access will be provisioned."
        elif decision == DecisionType.REQUIRES_APPROVAL:
            return "After completing these steps, your request will be reviewed by management for final approval."
        else:
            return "After completing these steps, IT Support will review your request and contact you with next steps."


class ITAgentNode:
    """Main IT Agent node for executing plan steps"""
    
    def __init__(self, dry_run: bool = False):
        self.execution_engine = ExecutionEngine(dry_run=dry_run)
        self.user_guide_generator = UserGuideGenerator()
        
    def execute_plan(self, state: ITGraphState) -> Tuple[ITGraphState, ExecutionOutcome]:
        """Execute the plan and return updated state and outcome"""
        try:
            plan_record = state.get("plan_record", {})
            if not plan_record:
                logger.warning("No plan record found in state")
                return state, ExecutionOutcome.EXECUTED
            
            steps = plan_record.get("steps", [])
            if not steps:
                logger.info("No steps to execute")
                return state, ExecutionOutcome.EXECUTED
            
            # Separate executable and manual steps
            executable_steps = self._identify_executable_steps(steps, state)
            manual_steps = self._identify_manual_steps(steps, state)
            
            # Execute automated steps
            execution_results = []
            for step in executable_steps:
                action = self._create_executable_action(step)
                if action.preconditions_met:
                    result = self.execution_engine.execute_action(action, state)
                    execution_results.append(result)
                else:
                    logger.warning(f"Preconditions not met for step {step.get('step_id')}")
            
            # Generate user guide for manual steps
            user_guide = None
            if manual_steps:
                user_guide = self.user_guide_generator.generate_user_guide(manual_steps, state)
            
            # Update ticket status
            ticket_status = self._determine_ticket_status(executable_steps, manual_steps, state)
            
            # Update state with execution results
            state = self._update_state_with_results(state, execution_results, user_guide, ticket_status)
            
            # Determine outcome
            outcome = self._determine_outcome(executable_steps, manual_steps, state)
            
            return state, outcome
            
        except Exception as e:
            logger.error(f"Error in IT Agent execution: {e}")
            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "error_id": f"it_agent_error_{datetime.now().timestamp()}",
                "timestamp": datetime.now(),
                "error_type": "it_agent_execution_error",
                "message": str(e),
                "severity": "high",
                "resolved": False
            })
            return state, ExecutionOutcome.EXECUTED
    
    def _identify_executable_steps(self, steps: List[PlanStep], state: ITGraphState) -> List[PlanStep]:
        """Identify steps that can be executed automatically"""
        executable_steps = []
        
        for step in steps:
            actor = step.get("actor")
            automation_possible = step.get("automation_possible", False)
            
            # Steps that can be automated or use available tools
            if (automation_possible or 
                actor == ActorType.IT_AGENT or 
                actor == ActorType.SYSTEM):
                executable_steps.append(step)
        
        return executable_steps
    
    def _identify_manual_steps(self, steps: List[PlanStep], state: ITGraphState) -> List[PlanStep]:
        """Identify steps that require manual intervention"""
        manual_steps = []
        
        for step in steps:
            actor = step.get("actor")
            automation_possible = step.get("automation_possible", False)
            
            # Steps that require human intervention
            if (not automation_possible and 
                (actor == ActorType.EMPLOYEE or actor == ActorType.MANAGER_APPROVAL)):
                manual_steps.append(step)
        
        return manual_steps
    
    def _create_executable_action(self, step: PlanStep) -> ExecutableAction:
        """Create an executable action from a plan step"""
        # Determine tool based on step requirements
        required_tools = step.get("required_tools", [])
        tool = "system"  # default
        
        if "email" in required_tools:
            tool = "email"
        elif "jira" in required_tools:
            tool = "jira"
        
        # Create parameters based on step details
        parameters = {
            "action_type": "execute",
            "subject": f"IT Support: {step.get('description', 'Action Required')}",
            "body": step.get("description", ""),
            "recipients": [],
            "fields": {},
            "comment": step.get("description", "")
        }
        
        return ExecutableAction(
            step_id=step.get("step_id", ""),
            action_type="execute",
            tool=tool,
            parameters=parameters,
            preconditions_met=True,  # Assume met for now
            estimated_duration=step.get("estimated_duration", 30),
            automation_level="fully_automated" if step.get("automation_possible") else "semi_automated"
        )
    
    def _determine_ticket_status(self, executable_steps: List[PlanStep], 
                                manual_steps: List[PlanStep], state: ITGraphState) -> str:
        """Determine the appropriate ticket status"""
        if not manual_steps:
            return "IN_PROGRESS"
        
        # Check if any steps require manager approval
        has_manager_steps = any(
            step.get("actor") == ActorType.MANAGER_APPROVAL 
            for step in manual_steps
        )
        
        if has_manager_steps:
            return "WAITING_FOR_APPROVAL"
        else:
            return "WAITING_FOR_USER"
    
    def _update_state_with_results(self, state: ITGraphState, execution_results: List[Dict[str, Any]], 
                                  user_guide: Optional[UserGuide], ticket_status: str) -> ITGraphState:
        """Update state with execution results and user guide"""
        # Add execution results to state
        if "execution_results" not in state:
            state["execution_results"] = []
        state["execution_results"].extend(execution_results)
        
        # Add user guide to state if generated
        if user_guide:
            state["user_guide"] = {
                "title": user_guide.title,
                "introduction": user_guide.introduction,
                "steps": user_guide.steps,
                "completion_criteria": user_guide.completion_criteria,
                "next_steps": user_guide.next_steps,
                "generated_at": datetime.now().isoformat()
            }
        
        # Update ticket status
        if "ticket_record" in state:
            state["ticket_record"]["status"] = ticket_status
            state["ticket_record"]["updated_at"] = datetime.now()
        
        return state
    
    def _determine_outcome(self, executable_steps: List[PlanStep], 
                          manual_steps: List[PlanStep], state: ITGraphState) -> ExecutionOutcome:
        """Determine the execution outcome"""
        if not manual_steps:
            return ExecutionOutcome.EXECUTED
        
        # Check if any steps require manager approval
        has_manager_steps = any(
            step.get("actor") == ActorType.MANAGER_APPROVAL 
            for step in manual_steps
        )
        
        if has_manager_steps:
            return ExecutionOutcome.AWAITING_MANAGER
        else:
            return ExecutionOutcome.AWAITING_EMPLOYEE


def it_agent_node(state: ITGraphState) -> ITGraphState:
    """
    IT Agent node: executes what is executable and returns outcome
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with execution results and outcome
    """
    try:
        # Initialize IT Agent
        agent = ITAgentNode(dry_run=False)  # Set to True for testing
        
        # Execute plan
        updated_state, outcome = agent.execute_plan(state)
        
        # Add outcome to state
        updated_state["it_outcome"] = outcome
        
        # Add execution metadata
        if "metadata" not in updated_state:
            updated_state["metadata"] = {}
        updated_state["metadata"]["it_agent_execution"] = {
            "outcome": outcome,
            "execution_timestamp": datetime.now().isoformat(),
            "executed_steps": len([s for s in updated_state.get("execution_results", []) if s.get("success")]),
            "manual_steps_remaining": len(updated_state.get("user_guide", {}).get("steps", []))
        }
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in IT Agent node: {e}")
        
        # Add error to state
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append({
            "error_id": f"it_agent_node_error_{datetime.now().timestamp()}",
            "timestamp": datetime.now(),
            "error_type": "it_agent_node_error",
            "message": str(e),
            "severity": "high",
            "resolved": False
        })
        
        # Set default outcome
        state["it_outcome"] = ExecutionOutcome.EXECUTED
        
        return state


# Convenience functions for testing and direct usage
def test_it_agent_node():
    """Test function for the IT Agent node"""
    # Create test state with a simple plan
    test_state = {
        "plan_record": {
            "steps": [
                {
                    "step_id": "step_1",
                    "description": "Send approval email to manager",
                    "actor": "it_agent",
                    "automation_possible": True,
                    "required_tools": ["email"],
                    "estimated_duration": 5
                },
                {
                    "step_id": "step_2", 
                    "description": "Complete business justification form",
                    "actor": "employee",
                    "automation_possible": False,
                    "estimated_duration": 30
                }
            ]
        },
        "user_request": {
            "title": "Database Access Request",
            "description": "Need access to production database"
        },
        "ticket_record": {
            "status": "NEW"
        }
    }
    
    # Run IT Agent node
    result_state = it_agent_node(test_state)
    
    print(f"IT Outcome: {result_state['it_outcome']}")
    print(f"Execution results: {len(result_state.get('execution_results', []))}")
    print(f"User guide generated: {'user_guide' in result_state}")
    
    return result_state


if __name__ == "__main__":
    # Run test if executed directly
    test_it_agent_node()
