"""Utilities to convert raw LLM thoughts into structured summaries.

This module provides functions to parse and structure LLM chain-of-thought outputs
into standardized fields for consistent logging and analysis.

Note: We log structured fields only - raw LLM thoughts are not stored in the database.
"""

import json
import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class StructuredRationale:
    """Structured representation of LLM reasoning and decision-making."""
    
    rules_considered: List[str]
    evidence: List[str]
    decision: str
    confidence: float
    missing_info: List[str]
    reasoning_summary: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StructuredRationale':
        """Create instance from dictionary."""
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class RationaleParser:
    """Parser for converting raw LLM thoughts into structured rationale."""
    
    # Common patterns for extracting structured information
    RULES_PATTERNS = [
        r"rules?[:\s]+(.*?)(?=\n|$)",
        r"policies?[:\s]+(.*?)(?=\n|$)",
        r"guidelines?[:\s]+(.*?)(?=\n|$)",
        r"following[:\s]+(.*?)(?=\n|$)",
    ]
    
    EVIDENCE_PATTERNS = [
        r"evidence[:\s]+(.*?)(?=\n|$)",
        r"based on[:\s]+(.*?)(?=\n|$)",
        r"because[:\s]+(.*?)(?=\n|$)",
        r"since[:\s]+(.*?)(?=\n|$)",
        r"given that[:\s]+(.*?)(?=\n|$)",
    ]
    
    DECISION_PATTERNS = [
        r"decision[:\s]+(.*?)(?=\n|$)",
        r"conclusion[:\s]+(.*?)(?=\n|$)",
        r"therefore[:\s]+(.*?)(?=\n|$)",
        r"i recommend[:\s]+(.*?)(?=\n|$)",
        r"the solution is[:\s]+(.*?)(?=\n|$)",
    ]
    
    CONFIDENCE_PATTERNS = [
        r"confidence[:\s]+(\d+(?:\.\d+)?)",
        r"certainty[:\s]+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)%\s*confident",
        r"(\d+(?:\.\d+)?)\s*out of 1",
    ]
    
    MISSING_INFO_PATTERNS = [
        r"missing[:\s]+(.*?)(?=\n|$)",
        r"need more[:\s]+(.*?)(?=\n|$)",
        r"unclear[:\s]+(.*?)(?=\n|$)",
        r"unknown[:\s]+(.*?)(?=\n|$)",
        r"requires[:\s]+(.*?)(?=\n|$)",
    ]
    
    def __init__(self):
        """Initialize the parser with default patterns."""
        pass
    
    def parse_llm_thoughts(self, raw_thoughts: str) -> StructuredRationale:
        """
        Parse raw LLM thoughts into structured rationale.
        
        Args:
            raw_thoughts: Raw text output from LLM chain-of-thought reasoning
            
        Returns:
            StructuredRationale object with parsed fields
        """
        # Extract structured information using patterns
        rules = self._extract_rules(raw_thoughts)
        evidence = self._extract_evidence(raw_thoughts)
        decision = self._extract_decision(raw_thoughts)
        confidence = self._extract_confidence(raw_thoughts)
        missing_info = self._extract_missing_info(raw_thoughts)
        
        # Create reasoning summary (first 200 chars of original thoughts)
        reasoning_summary = raw_thoughts[:200].strip()
        if len(raw_thoughts) > 200:
            reasoning_summary += "..."
        
        return StructuredRationale(
            rules_considered=rules,
            evidence=evidence,
            decision=decision,
            confidence=confidence,
            missing_info=missing_info,
            reasoning_summary=reasoning_summary,
            timestamp=datetime.utcnow()
        )
    
    def _extract_rules(self, text: str) -> List[str]:
        """Extract rules, policies, or guidelines mentioned."""
        rules = []
        for pattern in self.RULES_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            rules.extend([match.strip() for match in matches if match.strip()])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_rules = []
        for rule in rules:
            if rule.lower() not in seen:
                seen.add(rule.lower())
                unique_rules.append(rule)
        
        return unique_rules[:5]  # Limit to 5 most relevant rules
    
    def _extract_evidence(self, text: str) -> List[str]:
        """Extract evidence or reasoning mentioned."""
        evidence = []
        for pattern in self.EVIDENCE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            evidence.extend([match.strip() for match in matches if match.strip()])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_evidence = []
        for ev in evidence:
            if ev.lower() not in seen:
                seen.add(ev.lower())
                unique_evidence.append(ev)
        
        return unique_evidence[:5]  # Limit to 5 most relevant pieces of evidence
    
    def _extract_decision(self, text: str) -> str:
        """Extract the final decision or recommendation."""
        for pattern in self.DECISION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                decision = matches[0].strip()
                if len(decision) > 10:  # Ensure it's substantial
                    return decision
        
        # Fallback: look for conclusion-like statements
        conclusion_patterns = [
            r"in conclusion[:\s]+(.*?)(?=\n|$)",
            r"to summarize[:\s]+(.*?)(?=\n|$)",
            r"the answer is[:\s]+(.*?)(?=\n|$)",
        ]
        
        for pattern in conclusion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                decision = matches[0].strip()
                if len(decision) > 10:
                    return decision
        
        # If no clear decision found, return a summary of the last sentence
        sentences = text.split('.')
        if sentences:
            last_sentence = sentences[-1].strip()
            if len(last_sentence) > 10:
                return last_sentence
        
        return "No clear decision identified"
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from text."""
        for pattern in self.CONFIDENCE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                try:
                    confidence = float(matches[0])
                    # Normalize to 0-1 range
                    if confidence > 1:
                        confidence = confidence / 100
                    return max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    continue
        
        # Fallback: analyze text for confidence indicators
        confidence_indicators = {
            'high': 0.8,
            'very high': 0.9,
            'medium': 0.6,
            'moderate': 0.6,
            'low': 0.3,
            'very low': 0.2,
            'uncertain': 0.4,
            'unsure': 0.4,
            'definitely': 0.9,
            'certainly': 0.9,
            'probably': 0.7,
            'likely': 0.7,
            'possibly': 0.5,
            'maybe': 0.4,
        }
        
        text_lower = text.lower()
        for indicator, score in confidence_indicators.items():
            if indicator in text_lower:
                return score
        
        return 0.5  # Default to medium confidence
    
    def _extract_missing_info(self, text: str) -> List[str]:
        """Extract information that is missing or unclear."""
        missing = []
        for pattern in self.MISSING_INFO_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            missing.extend([match.strip() for match in matches if match.strip()])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_missing = []
        for info in missing:
            if info.lower() not in seen:
                seen.add(info.lower())
                unique_missing.append(info)
        
        return unique_missing[:3]  # Limit to 3 most important missing pieces


def create_structured_rationale(
    rules: List[str],
    evidence: List[str],
    decision: str,
    confidence: float,
    missing_info: Optional[List[str]] = None,
    reasoning_summary: Optional[str] = None
) -> StructuredRationale:
    """
    Create a structured rationale manually.
    
    Use this when you want to create structured rationale without parsing raw LLM output.
    
    Args:
        rules: List of rules, policies, or guidelines considered
        evidence: List of evidence or reasoning points
        decision: The final decision or recommendation
        confidence: Confidence score (0.0 to 1.0)
        missing_info: Optional list of missing information
        reasoning_summary: Optional summary of reasoning
        
    Returns:
        StructuredRationale object
    """
    if missing_info is None:
        missing_info = []
    
    if reasoning_summary is None:
        reasoning_summary = f"Decision: {decision}"
    
    return StructuredRationale(
        rules_considered=rules,
        evidence=evidence,
        decision=decision,
        confidence=max(0.0, min(1.0, confidence)),
        missing_info=missing_info,
        reasoning_summary=reasoning_summary,
        timestamp=datetime.utcnow()
    )


def validate_rationale(rationale: StructuredRationale) -> List[str]:
    """
    Validate a structured rationale and return any issues found.
    
    Args:
        rationale: The rationale to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if not rationale.decision or len(rationale.decision.strip()) < 5:
        errors.append("Decision must be at least 5 characters long")
    
    if rationale.confidence < 0.0 or rationale.confidence > 1.0:
        errors.append("Confidence must be between 0.0 and 1.0")
    
    if not rationale.rules_considered:
        errors.append("At least one rule must be considered")
    
    if not rationale.evidence:
        errors.append("At least one piece of evidence must be provided")
    
    if len(rationale.reasoning_summary) > 500:
        errors.append("Reasoning summary must be 500 characters or less")
    
    return errors


def rationale_to_json(rationale: StructuredRationale) -> str:
    """Convert rationale to JSON string for storage or transmission."""
    return json.dumps(rationale.to_dict(), indent=2)


def rationale_from_json(json_str: str) -> StructuredRationale:
    """Create rationale from JSON string."""
    data = json.loads(json_str)
    return StructuredRationale.from_dict(data)


# Convenience function for quick parsing
def parse_llm_output(raw_output: str) -> StructuredRationale:
    """
    Quick function to parse LLM output into structured rationale.
    
    Args:
        raw_output: Raw LLM output text
        
    Returns:
        StructuredRationale object
    """
    parser = RationaleParser()
    return parser.parse_llm_thoughts(raw_output)
