"""Tests for rationale policy utilities."""

import pytest
from datetime import datetime
from .rationale_policy import (
    StructuredRationale,
    RationaleParser,
    create_structured_rationale,
    validate_rationale,
    parse_llm_output,
    rationale_to_json,
    rationale_from_json
)


class TestStructuredRationale:
    """Test the StructuredRationale dataclass."""
    
    def test_creation(self):
        """Test creating a StructuredRationale instance."""
        rationale = StructuredRationale(
            rules_considered=["Rule 1", "Rule 2"],
            evidence=["Evidence 1"],
            decision="Test decision",
            confidence=0.8,
            missing_info=["Info 1"],
            reasoning_summary="Test reasoning",
            timestamp=datetime.utcnow()
        )
        
        assert len(rationale.rules_considered) == 2
        assert len(rationale.evidence) == 1
        assert rationale.decision == "Test decision"
        assert rationale.confidence == 0.8
        assert len(rationale.missing_info) == 1
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        timestamp = datetime.utcnow()
        rationale = StructuredRationale(
            rules_considered=["Rule 1"],
            evidence=["Evidence 1"],
            decision="Test decision",
            confidence=0.7,
            missing_info=[],
            reasoning_summary="Test reasoning",
            timestamp=timestamp
        )
        
        data = rationale.to_dict()
        assert isinstance(data, dict)
        assert data['decision'] == "Test decision"
        assert data['confidence'] == 0.7
        assert data['timestamp'] == timestamp.isoformat()
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        timestamp = datetime.utcnow()
        data = {
            'rules_considered': ["Rule 1"],
            'evidence': ["Evidence 1"],
            'decision': "Test decision",
            'confidence': 0.7,
            'missing_info': [],
            'reasoning_summary': "Test reasoning",
            'timestamp': timestamp.isoformat()
        }
        
        rationale = StructuredRationale.from_dict(data)
        assert rationale.decision == "Test decision"
        assert rationale.confidence == 0.7
        assert rationale.timestamp == timestamp


class TestRationaleParser:
    """Test the RationaleParser class."""
    
    def setup_method(self):
        """Setup parser for each test."""
        self.parser = RationaleParser()
    
    def test_extract_rules(self):
        """Test extracting rules from text."""
        text = """
        Rules: Follow company policy
        Guidelines: Check warranty first
        Following: Safety protocols
        """
        
        rules = self.parser._extract_rules(text)
        assert len(rules) >= 2
        assert "Follow company policy" in rules
        assert "Check warranty first" in rules
    
    def test_extract_evidence(self):
        """Test extracting evidence from text."""
        text = """
        Evidence: User reported issue
        Based on: Previous similar cases
        Because: Hardware failure detected
        """
        
        evidence = self.parser._extract_evidence(text)
        assert len(evidence) >= 2
        assert "User reported issue" in evidence
        assert "Previous similar cases" in evidence
    
    def test_extract_decision(self):
        """Test extracting decision from text."""
        text = """
        Decision: Replace the hardware
        Conclusion: Device needs replacement
        Therefore: Order new part
        """
        
        decision = self.parser._extract_decision(text)
        assert "Replace the hardware" in decision or "Device needs replacement" in decision
    
    def test_extract_confidence_numeric(self):
        """Test extracting numeric confidence scores."""
        text = "Confidence: 85%"
        confidence = self.parser._extract_confidence(text)
        assert confidence == 0.85
    
    def test_extract_confidence_text(self):
        """Test extracting confidence from text indicators."""
        text = "I am very confident in this assessment"
        confidence = self.parser._extract_confidence(text)
        assert confidence == 0.9
    
    def test_extract_missing_info(self):
        """Test extracting missing information."""
        text = """
        Missing: User contact details
        Need more: System specifications
        Unclear: Exact error message
        """
        
        missing = self.parser._extract_missing_info(text)
        assert len(missing) >= 2
        assert "User contact details" in missing
    
    def test_parse_llm_thoughts(self):
        """Test complete parsing of LLM thoughts."""
        raw_thoughts = """
        Rules: Follow IT policy
        Evidence: Hardware failure
        Decision: Replace device
        Confidence: 90%
        Missing: Warranty info
        """
        
        rationale = self.parser.parse_llm_thoughts(raw_thoughts)
        
        assert isinstance(rationale, StructuredRationale)
        assert len(rationale.rules_considered) > 0
        assert len(rationale.evidence) > 0
        assert rationale.decision != "No clear decision identified"
        assert rationale.confidence > 0.8
        assert len(rationale.missing_info) > 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_structured_rationale(self):
        """Test manually creating rationale."""
        rationale = create_structured_rationale(
            rules=["Rule 1"],
            evidence=["Evidence 1"],
            decision="Test decision",
            confidence=0.8
        )
        
        assert isinstance(rationale, StructuredRationale)
        assert rationale.decision == "Test decision"
        assert rationale.confidence == 0.8
        assert rationale.timestamp is not None
    
    def test_validate_rationale_valid(self):
        """Test validation of valid rationale."""
        rationale = create_structured_rationale(
            rules=["Rule 1"],
            evidence=["Evidence 1"],
            decision="Valid decision with sufficient length",
            confidence=0.8
        )
        
        errors = validate_rationale(rationale)
        assert len(errors) == 0
    
    def test_validate_rationale_invalid(self):
        """Test validation of invalid rationale."""
        rationale = create_structured_rationale(
            rules=[],
            evidence=[],
            decision="Short",
            confidence=1.5
        )
        
        errors = validate_rationale(rationale)
        assert len(errors) > 0
        assert any("rules" in error.lower() for error in errors)
        assert any("evidence" in error.lower() for error in errors)
        assert any("confidence" in error.lower() for error in errors)
    
    def test_rationale_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        original = create_structured_rationale(
            rules=["Rule 1"],
            evidence=["Evidence 1"],
            decision="Test decision",
            confidence=0.8
        )
        
        json_str = rationale_to_json(original)
        restored = rationale_from_json(json_str)
        
        assert restored.decision == original.decision
        assert restored.confidence == original.confidence
        assert len(restored.rules_considered) == len(original.rules_considered)
    
    def test_parse_llm_output_quick(self):
        """Test the quick parse function."""
        raw_output = """
        Rules: Test rule
        Evidence: Test evidence
        Decision: Test decision
        Confidence: 75%
        """
        
        rationale = parse_llm_output(raw_output)
        assert isinstance(rationale, StructuredRationale)
        assert rationale.decision == "Test decision"
        assert rationale.confidence == 0.75


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_text(self):
        """Test parsing empty text."""
        parser = RationaleParser()
        rationale = parser.parse_llm_thoughts("")
        
        assert rationale.decision == "No clear decision identified"
        assert rationale.confidence == 0.5
        assert len(rationale.rules_considered) == 0
    
    def test_very_long_text(self):
        """Test parsing very long text."""
        long_text = "Rules: Test rule\n" * 1000 + "Decision: Final decision"
        parser = RationaleParser()
        rationale = parser.parse_llm_thoughts(long_text)
        
        assert rationale.decision == "Final decision"
        assert len(rationale.reasoning_summary) <= 203  # 200 + "..."
    
    def test_malformed_confidence(self):
        """Test handling malformed confidence values."""
        text = "Confidence: invalid_value"
        parser = RationaleParser()
        confidence = parser._extract_confidence(text)
        
        # Should fall back to text analysis
        assert 0.0 <= confidence <= 1.0
    
    def test_duplicate_extraction(self):
        """Test that duplicates are removed during extraction."""
        text = """
        Rules: Same rule
        Rules: Same rule
        Evidence: Same evidence
        Evidence: Same evidence
        """
        
        parser = RationaleParser()
        rationale = parser.parse_llm_thoughts(text)
        
        # Should have only unique values
        assert len(rationale.rules_considered) == 1
        assert len(rationale.evidence) == 1


if __name__ == "__main__":
    pytest.main([__file__])
