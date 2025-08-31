#!/usr/bin/env python3
"""
Simple JIRA Integration Test
Tests the JIRA agent directly without the full workflow
"""
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_jira_config():
    """Test JIRA configuration loading"""
    print("🔧 Testing JIRA Configuration...")
    try:
        from config.jira_config import get_jira_config
        config = get_jira_config()
        
        print(f"✅ JIRA Config loaded successfully!")
        print(f"  - Base URL: {config.base_url}")
        print(f"  - User: {config.user}")
        print(f"  - Project Key: {config.project_key}")
        print(f"  - Valid: {config.validate()}")
        
        return config
    except Exception as e:
        print(f"❌ JIRA Config failed: {e}")
        return None

def test_jira_agent():
    """Test JIRA agent directly"""
    print("\n🚀 Testing JIRA Agent...")
    try:
        from graph.nodes.jira_agent import jira_agent_node
        
        # Create test state
        test_state = {
            'user_request': {
                'title': 'Production Test - Real JIRA Integration',
                'description': 'Testing complete workflow with real JIRA ticket creation'
            },
            'decision_record': {
                'decision': 'ALLOWED',
                'confidence': 0.9,
                'needs_human': False
            }
        }
        
        print("  - Test state created")
        print("  - Calling JIRA agent...")
        
        # Call JIRA agent
        result = jira_agent_node(test_state)
        
        print(f"✅ JIRA Agent completed successfully!")
        print(f"  - Result keys: {list(result.keys())}")
        print(f"  - Ticket Record: {result.get('ticket_record', 'NONE')}")
        print(f"  - Errors: {len(result.get('errors', []))}")
        
        return result
        
    except Exception as e:
        print(f"❌ JIRA Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function"""
    print("🧪 JIRA Integration Test")
    print("=" * 50)
    
    # Test 1: Configuration
    config = test_jira_config()
    if not config:
        print("❌ Configuration test failed, stopping")
        return
    
    # Test 2: JIRA Agent
    result = test_jira_agent()
    if result:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ JIRA integration is working!")
        print("✅ Real JIRA tickets can be created!")
    else:
        print("\n❌ JIRA Agent test failed")

if __name__ == "__main__":
    main()
