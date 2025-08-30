"""Example usage of rationale policy utilities."""

from .rationale_policy import (
    StructuredRationale,
    RationaleParser,
    create_structured_rationale,
    validate_rationale,
    parse_llm_output,
    rationale_to_json,
    rationale_from_json
)


def example_llm_parsing():
    """Example of parsing raw LLM thoughts into structured rationale."""
    
    # Sample raw LLM output (chain-of-thought reasoning)
    raw_llm_output = """
    Let me think through this IT support ticket step by step.
    
    Rules: I need to follow the company's hardware replacement policy and ensure user safety.
    Guidelines: Always check warranty status before recommending replacement.
    
    Evidence: The user reports the laptop won't turn on after a power surge.
    Based on: Power surges can damage internal components, especially the motherboard.
    Since: The laptop is 4 years old and out of warranty.
    
    Missing: I need to know if the user has surge protection and what exactly happened during the power surge.
    
    Decision: I recommend replacing the laptop as the motherboard is likely damaged.
    The solution is to provide the user with a new laptop from our standard inventory.
    
    Confidence: 85% confident in this assessment.
    """
    
    print("=== Parsing Raw LLM Output ===")
    print(f"Raw output length: {len(raw_llm_output)} characters")
    
    # Parse using the utility function
    structured_rationale = parse_llm_output(raw_llm_output)
    
    print("\n=== Structured Rationale ===")
    print(f"Rules considered: {structured_rationale.rules_considered}")
    print(f"Evidence: {structured_rationale.evidence}")
    print(f"Decision: {structured_rationale.decision}")
    print(f"Confidence: {structured_rationale.confidence:.2f}")
    print(f"Missing info: {structured_rationale.missing_info}")
    print(f"Reasoning summary: {structured_rationale.reasoning_summary}")
    print(f"Timestamp: {structured_rationale.timestamp}")


def example_manual_creation():
    """Example of manually creating structured rationale."""
    
    print("\n=== Manual Creation Example ===")
    
    # Create rationale manually
    manual_rationale = create_structured_rationale(
        rules=[
            "Hardware replacement policy",
            "User safety guidelines",
            "Warranty assessment procedures"
        ],
        evidence=[
            "Laptop won't power on after power surge",
            "Device is 4 years old and out of warranty",
            "Power surges commonly damage motherboards"
        ],
        decision="Replace laptop with new device from standard inventory",
        confidence=0.85,
        missing_info=[
            "Surge protection status",
            "Exact details of power surge event"
        ],
        reasoning_summary="Power surge damage assessment leading to replacement recommendation"
    )
    
    print(f"Manual rationale created:")
    print(f"- Decision: {manual_rationale.decision}")
    print(f"- Confidence: {manual_rationale.confidence:.2f}")
    print(f"- Rules: {len(manual_rationale.rules_considered)} rules considered")


def example_validation():
    """Example of validating structured rationale."""
    
    print("\n=== Validation Example ===")
    
    # Create a rationale with potential issues
    problematic_rationale = create_structured_rationale(
        rules=[],
        evidence=[],
        decision="Fix it",
        confidence=1.5,  # Invalid confidence
        reasoning_summary="A" * 600  # Too long
    )
    
    # Validate the rationale
    errors = validate_rationale(problematic_rationale)
    
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Rationale is valid")


def example_json_serialization():
    """Example of JSON serialization and deserialization."""
    
    print("\n=== JSON Serialization Example ===")
    
    # Create a rationale
    rationale = create_structured_rationale(
        rules=["Policy A", "Guideline B"],
        evidence=["Fact 1", "Fact 2"],
        decision="Recommend action X",
        confidence=0.75
    )
    
    # Convert to JSON
    json_str = rationale_to_json(rationale)
    print(f"JSON representation ({len(json_str)} characters):")
    print(json_str[:200] + "..." if len(json_str) > 200 else json_str)
    
    # Convert back from JSON
    restored_rationale = rationale_from_json(json_str)
    print(f"\nRestored rationale decision: {restored_rationale.decision}")
    print(f"Restored confidence: {restored_rationale.confidence:.2f}")


def example_parser_customization():
    """Example of customizing the parser for specific use cases."""
    
    print("\n=== Parser Customization Example ===")
    
    # Create a custom parser
    custom_parser = RationaleParser()
    
    # Custom LLM output with specific format
    custom_output = """
    ANALYSIS RESULTS:
    
    APPLICABLE RULES:
    - Rule 1: Always check user permissions first
    - Rule 2: Follow security protocols for access requests
    
    SUPPORTING EVIDENCE:
    - User has valid business justification
    - Request aligns with role responsibilities
    - Manager approval provided
    
    FINAL RECOMMENDATION:
    Grant access to the requested system with standard user permissions.
    
    CONFIDENCE LEVEL: 90%
    
    ADDITIONAL INFORMATION NEEDED:
    - Specific system access requirements
    - Duration of access needed
    """
    
    # Parse with custom parser
    custom_rationale = custom_parser.parse_llm_thoughts(custom_output)
    
    print(f"Custom parser results:")
    print(f"- Rules: {custom_rationale.rules_considered}")
    print(f"- Evidence: {custom_rationale.evidence}")
    print(f"- Decision: {custom_rationale.decision}")
    print(f"- Confidence: {custom_rationale.confidence:.2f}")


def main():
    """Run all examples."""
    print("Rationale Policy Utilities - Examples")
    print("=" * 50)
    
    example_llm_parsing()
    example_manual_creation()
    example_validation()
    example_json_serialization()
    example_parser_customization()
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()
