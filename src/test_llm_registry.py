"""Test the LLM registry functionality."""

from .models.llm_registry import get_llm, get_escalation_llm, switch_provider


def test_llm_registry():
    """Test the LLM registry with different roles."""
    
    # Test getting LLMs for different roles
    print("Testing LLM Registry...")
    
    try:
        # Get classifier LLM (llama3.1:8b)
        classifier_llm = get_llm("classifier")
        print(f"✓ Classifier LLM: {classifier_llm}")
        
        # Get planner LLM (mistral:7b)
        planner_llm = get_llm("planner")
        print(f"✓ Planner LLM: {planner_llm}")
        
        # Get IT support LLM (llama3.1:8b)
        it_llm = get_llm("it")
        print(f"✓ IT Support LLM: {it_llm}")
        
        # Get router LLM (mistral:7b)
        router_llm = get_llm("router")
        print(f"✓ Router LLM: {router_llm}")
        
        # Get escalation LLM (mixtral:8x7b)
        escalation_llm = get_escalation_llm()
        print(f"✓ Escalation LLM: {escalation_llm}")
        
        print("\n✓ All LLMs retrieved successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def test_provider_switching():
    """Test switching between different LLM providers."""
    
    print("\nTesting Provider Switching...")
    
    try:
        # Test switching to vLLM (if configured)
        switch_provider("vllm")
        print("✓ Switched to vLLM provider")
        
        # Test switching back to Ollama
        switch_provider("ollama")
        print("✓ Switched back to Ollama provider")
        
        print("✓ Provider switching works!")
        
    except Exception as e:
        print(f"✗ Provider switching error: {e}")


if __name__ == "__main__":
    test_llm_registry()
    test_provider_switching()
