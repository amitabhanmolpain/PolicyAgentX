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

def run_tests():
    print("=" * 60)
    print("TAVILY SEARCH & CACHING UNIT TEST")
    print("=" * 60)

    # 1. Check API Key
    api_key = os.getenv("TAVILY_API_KEY")
    print(f"Loaded TAVILY_API_KEY: {api_key}")

    # 2. Test Client Singleton
    try:
        client = get_tavily_client()
        print(f"Tavily client singleton initialized. Client: {client}")
    except Exception as e:
        print(f"Tavily client initialization raised error (Expected if key is dummy/missing): {e}")

    # 3. Test Caching and Fallback behavior (when key is invalid or dummy)
    test_policy = "Implement a nationwide luxury tax policy on high-end goods."
    
    print("\nStep A: Running Tavily Search for 'economic' (cache miss)...")
    start_time = time.time()
    context_1 = get_cached_web_context(test_policy, "economic")
    duration_1 = time.time() - start_time
    print(f"Completed in {duration_1:.4f}s. Context size: {len(context_1)} chars.")
    
    # Check cache exists
    print(f"Cache size: {len(_search_cache)} entries.")
    
    print("\nStep B: Running same search again (should be cache hit)...")
    start_time = time.time()
    context_2 = get_cached_web_context(test_policy, "economic")
    duration_2 = time.time() - start_time
    print(f"Completed in {duration_2:.6f}s (Cache Hit!).")
    
    assert context_1 == context_2, "Cached context should be identical"
    assert duration_2 < 0.01, "Cache lookup should be near-instantaneous"
    print("Caching verification successful!")

    # 4. Test News / Conflict search
    print("\nStep C: Testing news/conflict context query...")
    context_news = get_cached_web_context(test_policy, "news_conflict")
    print(f"News context returned size: {len(context_news)} chars.")

    print("\n" + "=" * 60)
    print("TAVILY UNIT TEST COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
