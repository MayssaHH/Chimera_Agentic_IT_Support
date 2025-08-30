"""Tools package for external service integrations."""

from .jira import JiraClient
from .emailer import Emailer, EmailTemplate
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

__all__ = [
    "JiraClient",
    "Emailer", 
    "EmailTemplate",
    "HILQueue",
    "HILQuestion",
    "HILStatus",
    "HILPriority",
    "create_hil_question",
    "answer_hil_question",
    "get_pending_hil_questions",
    "get_hil_updates_for_ticket",
    "check_hil_answer_status",
    "get_hil_queue_summary"
]
