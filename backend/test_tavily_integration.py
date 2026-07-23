import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
load_dotenv()

from rag.tavily_client import get_tavily_client, get_cached_web_context, _search_cache
from agents.social import social_agent
from agents.economic import economic_agent

def run_tests():
    print("=" * 60)
    print("TAVILY INTEGRATION & PIPELINE TESTING")
    print("=" * 60)

    # 1. Check API Key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY is not set in environment.")
        print("Please check your backend/.env file and ensure TAVILY_API_KEY is present.")
        sys.exit(1)
    
    print(f"TAVILY_API_KEY connected (prefix: {api_key[:6]}...)")

    # 2. Test Client Singleton
    try:
        client = get_tavily_client()
        print("Tavily client singleton initialized successfully.")
    except Exception as e:
        print(f"Failed to get Tavily client: {e}")
        sys.exit(1)

    # 3. Test Caching
    test_policy = "Implement a nationwide scheme to provide direct income support to small and marginal farmers in India."
    
    print("\nStep A: Running Tavily Search for 'economic' (cache miss)...")
    start_time = time.time()
    context_1 = get_cached_web_context(test_policy, "economic")
    duration_1 = time.time() - start_time
    print(f"Completed in {duration_1:.2f}s.")
    print(f"Context Preview (length {len(context_1)} chars): {context_1[:150]}...")
    
    # Check cache exists
    assert len(_search_cache) >= 1, "Cache should have entries"

    print("\nStep B: Running same search again (should be cache hit)...")
    start_time = time.time()
    context_2 = get_cached_web_context(test_policy, "economic")
    duration_2 = time.time() - start_time
    print(f"Completed in {duration_2:.6f}s (Cache Hit!).")
    
    assert context_1 == context_2, "Cached context should be identical"
    assert duration_2 < 0.05, "Cache lookup should be near-instantaneous"
    print("Caching verification successful!")

    # 4. Test Agent Invocations
    print("\nStep C: Testing economic_agent with web context...")
    state = {
        "policy_text": test_policy,
        "region": "India",
        "rag_context": "Sample RAG context from DB"
    }
    
    try:
        econ_res = economic_agent(state, web_context=context_2)
        print("economic_agent run successful!")
        print(f"GDP Impact: {econ_res.get('gdp_impact')}")
        print(f"Inflation Impact: {econ_res.get('inflation_impact')}")
        print(f"Employment Impact: {econ_res.get('employment_impact')}")
    except Exception as e:
        print(f"economic_agent invocation failed: {e}")

    print("\nStep D: Testing social_agent with news/conflict context...")
    try:
        news_context = get_cached_web_context(test_policy, "news_conflict")
        social_res = social_agent(state, web_context=news_context)
        print("social_agent run successful!")
        print(f"Middle Class Impact: {social_res.get('middle_class_impact')}")
        print(f"Lower Income Impact: {social_res.get('lower_income_impact')}")
        print(f"Lifestyle Changes: {social_res.get('lifestyle_changes')}")
    except Exception as e:
        print(f"social_agent invocation failed: {e}")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
