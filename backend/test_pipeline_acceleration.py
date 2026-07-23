import os
import time
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Set up test variables
test_policy = "The Indian government proposes a 5% GST reduction on electric vehicles and charging infrastructure to accelerate green mobility adoption."

async def run_test():
    print("[INFO] Initializing test run...")
    
    # Import components
    try:
        from agents.rag_agent_orchestrator import RAGAgentOrchestrator
        from rag.gemini_client import clear_gemini_cache
        from rag.tavily_client import clear_search_cache
    except ImportError as e:
        print(f"[ERROR] Failed to import required components: {e}")
        return
        
    # Clear caches
    clear_gemini_cache()
    clear_search_cache()
    
    orchestrator = RAGAgentOrchestrator()
    
    print("\n--- RUN 1: Cold Cache (First Execution) ---")
    start_time = time.time()
    try:
        result_1 = await orchestrator.orchestrate_policy_analysis(test_policy)
        duration_1 = time.time() - start_time
        print(f"[SUCCESS] Run 1 Completed in: {duration_1:.2f} seconds")
        print(f"Result keys: {list(result_1.keys())}")
        print(f"Social impact status: {'error' not in result_1.get('social_impact', {})}")
        print(f"Economic impact status: {'error' not in result_1.get('economic_outlook', {})}")
    except Exception as e:
        print(f"[ERROR] Run 1 failed with error: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n--- RUN 2: Warm Cache (Second Execution, identical query) ---")
    start_time = time.time()
    try:
        result_2 = await orchestrator.orchestrate_policy_analysis(test_policy)
        duration_2 = time.time() - start_time
        print(f"[SUCCESS] Run 2 Completed in: {duration_2:.2f} seconds")
        
        # Expecting sub-second response due to cache
        if duration_2 < 1.0:
            print("[SUCCESS] Response caching works! Warm execution was instant.")
        else:
            print(f"[WARNING] Warm execution took {duration_2:.2f}s, check caching implementation.")
            
    except Exception as e:
        print(f"[ERROR] Run 2 failed with error: {e}")
        return

    # Print summary
    print("\n=== LATENCY COMPARISON SUMMARY ===")
    print(f"Cold Cache execution: {duration_1:.2f}s")
    print(f"Warm Cache execution: {duration_2:.2f}s")
    speedup = duration_1 / duration_2 if duration_2 > 0 else 0
    print(f"Cache Speedup: {speedup:.1f}x faster")
    print("===================================\n")

if __name__ == "__main__":
    # Run the async test main loop
    asyncio.run(run_test())
