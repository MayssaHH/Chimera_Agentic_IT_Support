"""Human-in-the-Loop queue for managing pending human questions and answers."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from ..store.db import get_db_session, init_db
from ..store.rationale_policy import StructuredRationale


logger = logging.getLogger(__name__)


class HILStatus(Enum):
    """Status of human-in-the-loop questions."""
    PENDING = "pending"
    ANSWERED = "answered"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class HILPriority(Enum):
    """Priority levels for HIL questions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HILQuestion:
    """Human-in-the-Loop question record."""
    
    id: str
    ticket_id: str
    question_text: str
    context: str
    ai_rationale: StructuredRationale
    status: HILStatus
    priority: HILPriority
    assigned_to: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    answered_at: Optional[datetime] = None
    answer: Optional[str] = None
    approver: Optional[str] = None
    justification: Optional[str] = None
    expires_at: Optional[datetime] = None
    tags: Optional[str] = None
    
    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.answered_at:
            data['answered_at'] = self.answered_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        if self.ai_rationale:
            data['ai_rationale'] = self.ai_rationale.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HILQuestion':
        """Create instance from dictionary."""
        # Convert string status/priority back to enums
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = HILStatus(data['status'])
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = HILPriority(data['priority'])
        
        # Convert timestamp strings back to datetime
        for field in ['created_at', 'updated_at', 'answered_at', 'expires_at']:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert AI rationale if present
        if 'ai_rationale' in data and isinstance(data['ai_rationale'], dict):
            data['ai_rationale'] = StructuredRationale.from_dict(data['ai_rationale'])
        
        return cls(**data)


class HILQueue:
    """Human-in-the-Loop queue manager."""
    
    def __init__(self):
        """Initialize the HIL queue."""
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure HIL tables exist in the database."""
        # This would typically create the HIL tables
        # For now, we'll use the existing store infrastructure
        init_db()
    
    def add_question(
        self,
        ticket_id: str,
        question_text: str,
        context: str,
        ai_rationale: StructuredRationale,
        priority: HILPriority = HILPriority.MEDIUM,
        assigned_to: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        tags: Optional[str] = None
    ) -> HILQuestion:
        """
        Add a new human-in-the-loop question to the queue.
        
        Args:
            ticket_id: Associated ticket ID
            question_text: The question that needs human input
            context: Additional context about the question
            ai_rationale: AI's reasoning and decision
            priority: Priority level for the question
            assigned_to: Employee ID to assign the question to
            expires_at: When the question expires
            tags: Optional tags for categorization
            
        Returns:
            Created HIL question
        """
        import uuid
        
        question = HILQuestion(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            question_text=question_text,
            context=context,
            ai_rationale=ai_rationale,
            status=HILStatus.PENDING,
            priority=priority,
            assigned_to=assigned_to,
            expires_at=expires_at,
            tags=tags
        )
        
        # Store in database (simplified for now)
        with get_db_session() as session:
            # In a real implementation, you'd have a HILQuestion table
            # For now, we'll store in a JSON field or similar
            logger.info(f"Added HIL question {question.id} for ticket {ticket_id}")
        
        return question
    
    def get_question(self, question_id: str) -> Optional[HILQuestion]:
        """
        Get a specific HIL question by ID.
        
        Args:
            question_id: Question ID to retrieve
            
        Returns:
            HIL question or None if not found
        """
        # This would query the database for the specific question
        # For now, return None as placeholder
        logger.debug(f"Retrieving HIL question {question_id}")
        return None
    
    def get_pending_questions(
        self,
        assigned_to: Optional[str] = None,
        priority: Optional[HILPriority] = None,
        limit: int = 50
    ) -> List[HILQuestion]:
        """
        Get pending questions with optional filtering.
        
        Args:
            assigned_to: Filter by assigned employee
            priority: Filter by priority level
            limit: Maximum number of questions to return
            
        Returns:
            List of pending HIL questions
        """
        # This would query the database for pending questions
        # For now, return empty list as placeholder
        logger.debug(f"Retrieving pending HIL questions (limit: {limit})")
        return []
    
    def get_questions_for_ticket(self, ticket_id: str) -> List[HILQuestion]:
        """
        Get all HIL questions for a specific ticket.
        
        Args:
            ticket_id: Ticket ID to get questions for
            
        Returns:
            List of HIL questions for the ticket
        """
        # This would query the database for questions by ticket
        logger.debug(f"Retrieving HIL questions for ticket {ticket_id}")
        return []
    
    def record_hil_answer(
        self,
        ticket_id: str,
        answer: str,
        approver: str,
        justification: str
    ) -> bool:
        """
        Record a human answer to a HIL question.
        
        Args:
            ticket_id: Ticket ID the question is associated with
            answer: Human's answer/decision
            approver: Employee ID who provided the answer
            justification: Reasoning for the answer
            
        Returns:
            True if answer recorded successfully, False otherwise
        """
        try:
            # Find the pending question for this ticket
            questions = self.get_questions_for_ticket(ticket_id)
            pending_questions = [q for q in questions if q.status == HILStatus.PENDING]
            
            if not pending_questions:
                logger.warning(f"No pending HIL questions found for ticket {ticket_id}")
                return False
            
            # Update the first pending question (assuming one question per ticket)
            question = pending_questions[0]
            question.answer = answer
            question.approver = approver
            question.justification = justification
            question.status = HILStatus.ANSWERED
            question.answered_at = datetime.utcnow()
            question.updated_at = datetime.utcnow()
            
            # Store the updated question
            with get_db_session() as session:
                # In a real implementation, update the database record
                logger.info(f"Recorded HIL answer for ticket {ticket_id} by {approver}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record HIL answer for ticket {ticket_id}: {e}")
            return False
    
    def approve_answer(self, question_id: str, approver: str) -> bool:
        """
        Approve a recorded HIL answer.
        
        Args:
            question_id: Question ID to approve
            approver: Employee ID who is approving
            
        Returns:
            True if approved successfully, False otherwise
        """
        try:
            question = self.get_question(question_id)
            if not question:
                logger.warning(f"HIL question {question_id} not found")
                return False
            
            if question.status != HILStatus.ANSWERED:
                logger.warning(f"Cannot approve question {question_id} with status {question.status}")
                return False
            
            question.status = HILStatus.APPROVED
            question.updated_at = datetime.utcnow()
            
            # Store the updated question
            with get_db_session() as session:
                # In a real implementation, update the database record
                logger.info(f"Approved HIL answer {question_id} by {approver}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve HIL answer {question_id}: {e}")
            return False
    
    def reject_answer(self, question_id: str, rejector: str, reason: str) -> bool:
        """
        Reject a recorded HIL answer.
        
        Args:
            question_id: Question ID to reject
            rejector: Employee ID who is rejecting
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully, False otherwise
        """
        try:
            question = self.get_question(question_id)
            if not question:
                logger.warning(f"HIL question {question_id} not found")
                return False
            
            if question.status != HILStatus.ANSWERED:
                logger.warning(f"Cannot reject question {question_id} with status {question.status}")
                return False
            
            question.status = HILStatus.REJECTED
            question.justification = f"Rejected by {rejector}: {reason}"
            question.updated_at = datetime.utcnow()
            
            # Store the updated question
            with get_db_session() as session:
                # In a real implementation, update the database record
                logger.info(f"Rejected HIL answer {question_id} by {rejector}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject HIL answer {question_id}: {e}")
            return False
    
    def expire_question(self, question_id: str) -> bool:
        """
        Mark a question as expired.
        
        Args:
            question_id: Question ID to expire
            
        Returns:
            True if expired successfully, False otherwise
        """
        try:
            question = self.get_question(question_id)
            if not question:
                logger.warning(f"HIL question {question_id} not found")
                return False
            
            question.status = HILStatus.EXPIRED
            question.updated_at = datetime.utcnow()
            
            # Store the updated question
            with get_db_session() as session:
                # In a real implementation, update the database record
                logger.info(f"Expired HIL question {question_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to expire HIL question {question_id}: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the HIL queue.
        
        Returns:
            Dictionary with queue statistics
        """
        try:
            # This would query the database for statistics
            # For now, return placeholder data
            stats = {
                "total_questions": 0,
                "pending": 0,
                "answered": 0,
                "approved": 0,
                "rejected": 0,
                "expired": 0,
                "by_priority": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "critical": 0
                }
            }
            
            logger.debug("Retrieved HIL queue statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue statistics: {e}")
            return {}
    
    def cleanup_expired_questions(self) -> int:
        """
        Clean up expired questions.
        
        Returns:
            Number of questions cleaned up
        """
        try:
            # This would query for expired questions and update their status
            # For now, return 0 as placeholder
            logger.info("Cleaned up expired HIL questions")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired questions: {e}")
            return 0


# Polling functions for agents
def get_pending_hil_questions(
    assigned_to: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get pending HIL questions for agent polling.
    
    Args:
        assigned_to: Filter by assigned employee
        priority: Filter by priority level
        limit: Maximum number of questions to return
        
    Returns:
        List of pending questions as dictionaries
    """
    queue = HILQueue()
    questions = queue.get_pending_questions(
        assigned_to=assigned_to,
        priority=HILPriority(priority) if priority else None,
        limit=limit
    )
    
    return [q.to_dict() for q in questions]


def get_hil_updates_for_ticket(ticket_id: str) -> List[Dict[str, Any]]:
    """
    Get HIL updates for a specific ticket.
    
    Args:
        ticket_id: Ticket ID to check for updates
        
    Returns:
        List of HIL updates as dictionaries
    """
    queue = HILQueue()
    questions = queue.get_questions_for_ticket(ticket_id)
    
    return [q.to_dict() for q in questions]


def check_hil_answer_status(ticket_id: str) -> Optional[Dict[str, Any]]:
    """
    Check if a HIL question has been answered for a ticket.
    
    Args:
        ticket_id: Ticket ID to check
        
    Returns:
        Answer details if available, None otherwise
    """
    queue = HILQueue()
    questions = queue.get_questions_for_ticket(ticket_id)
    
    # Find answered questions
    answered_questions = [q for q in questions if q.status == HILStatus.ANSWERED]
    
    if answered_questions:
        question = answered_questions[0]
        return {
            "question_id": question.id,
            "answer": question.answer,
            "approver": question.approver,
            "justification": question.justification,
            "answered_at": question.answered_at.isoformat() if question.answered_at else None,
            "status": question.status.value
        }
    
    return None


def get_hil_queue_summary() -> Dict[str, Any]:
    """
    Get a summary of the HIL queue for agent monitoring.
    
    Returns:
        Queue summary as dictionary
    """
    queue = HILQueue()
    return queue.get_queue_stats()


# Convenience functions for common operations
def create_hil_question(
    ticket_id: str,
    question_text: str,
    context: str,
    ai_rationale: StructuredRationale,
    priority: str = "medium",
    assigned_to: Optional[str] = None,
    expires_in_hours: Optional[int] = None
) -> str:
    """
    Create a new HIL question with simplified parameters.
    
    Args:
        ticket_id: Associated ticket ID
        question_text: The question that needs human input
        context: Additional context about the question
        ai_rationale: AI's reasoning and decision
        priority: Priority level (low, medium, high, critical)
        assigned_to: Employee ID to assign the question to
        expires_in_hours: Hours until question expires
        
    Returns:
        Question ID
    """
    from datetime import timedelta
    
    queue = HILQueue()
    
    # Convert priority string to enum
    priority_enum = HILPriority(priority.lower())
    
    # Calculate expiration time
    expires_at = None
    if expires_in_hours:
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    question = queue.add_question(
        ticket_id=ticket_id,
        question_text=question_text,
        context=context,
        ai_rationale=ai_rationale,
        priority=priority_enum,
        assigned_to=assigned_to,
        expires_at=expires_at
    )
    
    return question.id


def answer_hil_question(
    ticket_id: str,
    answer: str,
    approver: str,
    justification: str
) -> bool:
    """
    Answer a HIL question with simplified parameters.
    
    Args:
        ticket_id: Ticket ID the question is associated with
        answer: Human's answer/decision
        approver: Employee ID who provided the answer
        justification: Reasoning for the answer
        
    Returns:
        True if answer recorded successfully, False otherwise
    """
    queue = HILQueue()
    return queue.record_hil_answer(ticket_id, answer, approver, justification)
