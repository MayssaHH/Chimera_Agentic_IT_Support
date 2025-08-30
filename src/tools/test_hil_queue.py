"""Tests for HIL queue module functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from .hil_queue import (
    HILQueue,
    HILQuestion,
    HILStatus,
    HILPriority,
    create_hil_question,
    answer_hil_question,
    get_pending_hil_questions,
    get_hil_updates_for_ticket,
    check_hil_answer_status,
    get_hil_queue_summary
)
from ..store.rationale_policy import create_structured_rationale


class TestHILStatus:
    """Test HILStatus enum."""
    
    def test_status_values(self):
        """Test HIL status values."""
        assert HILStatus.PENDING.value == "pending"
        assert HILStatus.ANSWERED.value == "answered"
        assert HILStatus.APPROVED.value == "approved"
        assert HILStatus.REJECTED.value == "rejected"
        assert HILStatus.EXPIRED.value == "expired"


class TestHILPriority:
    """Test HILPriority enum."""
    
    def test_priority_values(self):
        """Test HIL priority values."""
        assert HILPriority.LOW.value == "low"
        assert HILPriority.MEDIUM.value == "medium"
        assert HILPriority.HIGH.value == "high"
        assert HILPriority.CRITICAL.value == "critical"


class TestHILQuestion:
    """Test the HILQuestion dataclass."""
    
    def test_creation(self):
        """Test creating a HILQuestion instance."""
        ai_rationale = create_structured_rationale(
            rules=["Test rule"],
            evidence=["Test evidence"],
            decision="Test decision",
            confidence=0.8
        )
        
        question = HILQuestion(
            id="test-001",
            ticket_id="IT-001",
            question_text="Test question?",
            context="Test context",
            ai_rationale=ai_rationale,
            status=HILStatus.PENDING,
            priority=HILPriority.MEDIUM
        )
        
        assert question.id == "test-001"
        assert question.ticket_id == "IT-001"
        assert question.question_text == "Test question?"
        assert question.status == HILStatus.PENDING
        assert question.priority == HILPriority.MEDIUM
        assert question.created_at is not None
        assert question.updated_at is not None
    
    def test_default_timestamps(self):
        """Test that default timestamps are set."""
        ai_rationale = create_structured_rationale(
            rules=["Test rule"],
            evidence=["Test evidence"],
            decision="Test decision",
            confidence=0.8
        )
        
        question = HILQuestion(
            id="test-002",
            ticket_id="IT-002",
            question_text="Test question?",
            context="Test context",
            ai_rationale=ai_rationale,
            status=HILStatus.PENDING,
            priority=HILPriority.MEDIUM
        )
        
        assert question.created_at is not None
        assert question.updated_at is not None
        assert isinstance(question.created_at, datetime)
        assert isinstance(question.updated_at, datetime)
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        ai_rationale = create_structured_rationale(
            rules=["Test rule"],
            evidence=["Test evidence"],
            decision="Test decision",
            confidence=0.8
        )
        
        question = HILQuestion(
            id="test-003",
            ticket_id="IT-003",
            question_text="Test question?",
            context="Test context",
            ai_rationale=ai_rationale,
            status=HILStatus.PENDING,
            priority=HILPriority.MEDIUM
        )
        
        data = question.to_dict()
        
        assert isinstance(data, dict)
        assert data['id'] == "test-003"
        assert data['status'] == "pending"
        assert data['priority'] == "medium"
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'ai_rationale' in data
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        ai_rationale = create_structured_rationale(
            rules=["Test rule"],
            evidence=["Test evidence"],
            decision="Test decision",
            confidence=0.8
        )
        
        original_question = HILQuestion(
            id="test-004",
            ticket_id="IT-004",
            question_text="Test question?",
            context="Test context",
            ai_rationale=ai_rationale,
            status=HILStatus.PENDING,
            priority=HILPriority.MEDIUM
        )
        
        data = original_question.to_dict()
        restored_question = HILQuestion.from_dict(data)
        
        assert restored_question.id == original_question.id
        assert restored_question.ticket_id == original_question.ticket_id
        assert restored_question.status == original_question.status
        assert restored_question.priority == original_question.priority


class TestHILQueue:
    """Test the HILQueue class."""
    
    def setup_method(self):
        """Setup queue for each test."""
        with patch('src.tools.hil_queue.init_db'):
            self.queue = HILQueue()
    
    def test_initialization(self):
        """Test queue initialization."""
        assert self.queue is not None
    
    def test_add_question(self):
        """Test adding a question to the queue."""
        ai_rationale = create_structured_rationale(
            rules=["Test rule"],
            evidence=["Test evidence"],
            decision="Test decision",
            confidence=0.8
        )
        
        question = self.queue.add_question(
            ticket_id="IT-001",
            question_text="Test question?",
            context="Test context",
            ai_rationale=ai_rationale,
            priority=HILPriority.HIGH,
            assigned_to="test_user"
        )
        
        assert question is not None
        assert question.ticket_id == "IT-001"
        assert question.status == HILStatus.PENDING
        assert question.priority == HILPriority.HIGH
        assert question.assigned_to == "test_user"
    
    def test_get_question(self):
        """Test getting a question by ID."""
        question = self.queue.get_question("test-id")
        # Currently returns None as placeholder
        assert question is None
    
    def test_get_pending_questions(self):
        """Test getting pending questions."""
        questions = self.queue.get_pending_questions(limit=10)
        # Currently returns empty list as placeholder
        assert isinstance(questions, list)
        assert len(questions) == 0
    
    def test_get_questions_for_ticket(self):
        """Test getting questions for a specific ticket."""
        questions = self.queue.get_questions_for_ticket("IT-001")
        # Currently returns empty list as placeholder
        assert isinstance(questions, list)
        assert len(questions) == 0
    
    def test_record_hil_answer(self):
        """Test recording a HIL answer."""
        # Mock the get_questions_for_ticket method
        with patch.object(self.queue, 'get_questions_for_ticket') as mock_get:
            mock_question = Mock()
            mock_question.status = HILStatus.PENDING
            mock_question.answer = None
            mock_question.approver = None
            mock_question.justification = None
            mock_question.answered_at = None
            mock_question.updated_at = None
            
            mock_get.return_value = [mock_question]
            
            success = self.queue.record_hil_answer(
                ticket_id="IT-001",
                answer="Test answer",
                approver="test_user",
                justification="Test justification"
            )
            
            assert success is True
            assert mock_question.answer == "Test answer"
            assert mock_question.approver == "test_user"
            assert mock_question.justification == "Test justification"
            assert mock_question.status == HILStatus.ANSWERED
    
    def test_record_hil_answer_no_pending(self):
        """Test recording answer when no pending questions exist."""
        with patch.object(self.queue, 'get_questions_for_ticket') as mock_get:
            mock_get.return_value = []
            
            success = self.queue.record_hil_answer(
                ticket_id="IT-001",
                answer="Test answer",
                approver="test_user",
                justification="Test justification"
            )
            
            assert success is False
    
    def test_approve_answer(self):
        """Test approving an answer."""
        with patch.object(self.queue, 'get_question') as mock_get:
            mock_question = Mock()
            mock_question.status = HILStatus.ANSWERED
            mock_question.updated_at = None
            
            mock_get.return_value = mock_question
            
            success = self.queue.approve_answer("test-id", "approver_user")
            
            assert success is True
            assert mock_question.status == HILStatus.APPROVED
    
    def test_approve_answer_wrong_status(self):
        """Test approving answer with wrong status."""
        with patch.object(self.queue, 'get_question') as mock_get:
            mock_question = Mock()
            mock_question.status = HILStatus.PENDING
            
            mock_get.return_value = mock_question
            
            success = self.queue.approve_answer("test-id", "approver_user")
            
            assert success is False
    
    def test_reject_answer(self):
        """Test rejecting an answer."""
        with patch.object(self.queue, 'get_question') as mock_get:
            mock_question = Mock()
            mock_question.status = HILStatus.ANSWERED
            mock_question.updated_at = None
            
            mock_get.return_value = mock_question
            
            success = self.queue.reject_answer("test-id", "rejector_user", "Test reason")
            
            assert success is True
            assert mock_question.status == HILStatus.REJECTED
            assert "Test reason" in mock_question.justification
    
    def test_expire_question(self):
        """Test expiring a question."""
        with patch.object(self.queue, 'get_question') as mock_get:
            mock_question = Mock()
            mock_question.updated_at = None
            
            mock_get.return_value = mock_question
            
            success = self.queue.expire_question("test-id")
            
            assert success is True
            assert mock_question.status == HILStatus.EXPIRED
    
    def test_get_queue_stats(self):
        """Test getting queue statistics."""
        stats = self.queue.get_queue_stats()
        
        assert isinstance(stats, dict)
        assert 'total_questions' in stats
        assert 'pending' in stats
        assert 'answered' in stats
        assert 'by_priority' in stats
    
    def test_cleanup_expired_questions(self):
        """Test cleaning up expired questions."""
        count = self.queue.cleanup_expired_questions()
        
        assert isinstance(count, int)
        assert count >= 0


class TestPollingFunctions:
    """Test the polling functions for agents."""
    
    def test_get_pending_hil_questions(self):
        """Test getting pending questions for polling."""
        with patch('src.tools.hil_queue.HILQueue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            mock_queue.get_pending_questions.return_value = []
            
            result = get_pending_hil_questions(limit=10)
            
            assert isinstance(result, list)
            mock_queue.get_pending_questions.assert_called_once()
    
    def test_get_hil_updates_for_ticket(self):
        """Test getting HIL updates for a ticket."""
        with patch('src.tools.hil_queue.HILQueue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            mock_queue.get_questions_for_ticket.return_value = []
            
            result = get_hil_updates_for_ticket("IT-001")
            
            assert isinstance(result, list)
            mock_queue.get_questions_for_ticket.assert_called_once_with("IT-001")
    
    def test_check_hil_answer_status(self):
        """Test checking HIL answer status."""
        with patch('src.tools.hil_queue.HILQueue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            # Mock answered question
            mock_question = Mock()
            mock_question.status = HILStatus.ANSWERED
            mock_question.answer = "Test answer"
            mock_question.approver = "test_user"
            mock_question.justification = "Test justification"
            mock_question.answered_at = datetime.utcnow()
            
            mock_queue.get_questions_for_ticket.return_value = [mock_question]
            
            result = check_hil_answer_status("IT-001")
            
            assert result is not None
            assert result['answer'] == "Test answer"
            assert result['approver'] == "test_user"
    
    def test_check_hil_answer_status_no_answer(self):
        """Test checking HIL answer status when no answer exists."""
        with patch('src.tools.hil_queue.HILQueue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            mock_queue.get_questions_for_ticket.return_value = []
            
            result = check_hil_answer_status("IT-001")
            
            assert result is None
    
    def test_get_hil_queue_summary(self):
        """Test getting queue summary."""
        with patch('src.tools.hil_queue.HILQueue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            mock_queue.get_queue_stats.return_value = {"total": 0}
            
            result = get_hil_queue_summary()
            
            assert isinstance(result, dict)
            mock_queue.get_queue_stats.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_hil_question(self):
        """Test creating HIL question with convenience function."""
        with patch('src.tools.hil_queue.HILQueue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            ai_rationale = create_structured_rationale(
                rules=["Test rule"],
                evidence=["Test evidence"],
                decision="Test decision",
                confidence=0.8
            )
            
            mock_question = Mock()
            mock_question.id = "test-id"
            mock_queue.add_question.return_value = mock_question
            
            question_id = create_hil_question(
                ticket_id="IT-001",
                question_text="Test question?",
                context="Test context",
                ai_rationale=ai_rationale,
                priority="high",
                assigned_to="test_user",
                expires_in_hours=24
            )
            
            assert question_id == "test-id"
            mock_queue.add_question.assert_called_once()
    
    def test_answer_hil_question(self):
        """Test answering HIL question with convenience function."""
        with patch('src.tools.hil_queue.HILQueue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            mock_queue.record_hil_answer.return_value = True
            
            success = answer_hil_question(
                ticket_id="IT-001",
                answer="Test answer",
                approver="test_user",
                justification="Test justification"
            )
            
            assert success is True
            mock_queue.record_hil_answer.assert_called_once_with(
                "IT-001", "Test answer", "test_user", "Test justification"
            )


class TestErrorHandling:
    """Test error handling in HIL operations."""
    
    def test_record_hil_answer_exception(self):
        """Test handling exceptions in record_hil_answer."""
        queue = HILQueue()
        
        with patch.object(queue, 'get_questions_for_ticket') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            success = queue.record_hil_answer(
                ticket_id="IT-001",
                answer="Test answer",
                approver="test_user",
                justification="Test justification"
            )
            
            assert success is False
    
    def test_approve_answer_exception(self):
        """Test handling exceptions in approve_answer."""
        queue = HILQueue()
        
        with patch.object(queue, 'get_question') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            success = queue.approve_answer("test-id", "approver_user")
            
            assert success is False
    
    def test_invalid_priority_enum(self):
        """Test handling invalid priority values."""
        with pytest.raises(ValueError):
            HILPriority("invalid_priority")
    
    def test_invalid_status_enum(self):
        """Test handling invalid status values."""
        with pytest.raises(ValueError):
            HILStatus("invalid_status")


if __name__ == "__main__":
    pytest.main([__file__])
