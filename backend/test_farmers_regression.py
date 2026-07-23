import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def run_test():
    print("[INFO] Initializing regression test for 'ban all farmers' dynamic output...")
    
    from agents.rag_orchestrator import RAGEnhancedOrchestratorAgent
    
    orchestrator = RAGEnhancedOrchestratorAgent()
    policy_text = "ban all farmers from owning land or operating agricultural machinery in India."
    
    print(f"Submitting policy text: '{policy_text}'\n")
    
    try:
        # Run graph execution
        result = orchestrator.analyze_policy(policy_text)
        print("[SUCCESS] Pipeline completed successfully.")
        
        frontend_cards = result.get("frontend_cards", {})
        
        # Verify affected groups
        affected_groups_data = frontend_cards.get("affected_groups", {})
        groups = affected_groups_data.get("groups", [])
        
        print("\n=== Affected Groups Output ===")
        print(groups)
        
        # Verify confidence scores
        sections = [
            "policy_summary", "affected_groups", "economic_impact", 
            "timeline", "global_impact", "protest_risk", "improvements"
        ]
        
        confidence_scores = []
        print("\n=== Confidence Scores Output ===")
        for section in sections:
            score = frontend_cards.get(section, {}).get("confidence_score")
            confidence_scores.append(score)
            print(f"Confidence score for '{section}': {score}%")
            
        # Assertions
        assert len(groups) > 0, "Error: affected groups list is empty!"
        
        # Find farmers group
        farmers_group = None
        for g in groups:
            if "farmer" in g.get("group_name", "").lower():
                farmers_group = g
                break
                
        assert farmers_group is not None, "Error: Farmers are not identified in the affected groups!"
        
        print(f"\nFarmers Group details: {farmers_group}")
        status = farmers_group.get("status")
        assert status in ["NEGATIVELY IMPACTED", "OPPRESSED"], f"Error: Status of Farmers is '{status}', expected NEGATIVELY IMPACTED or OPPRESSED!"
        
        # Assert that confidence scores are not all identical (proves they aren't a flat constant)
        unique_scores = set(confidence_scores)
        print(f"\nUnique confidence scores: {unique_scores}")
        assert len(unique_scores) >= 3, f"Error: Confidence scores lack sufficient variance: {confidence_scores}"
        
        print("\n[TEST PASSED] Regression test successfully verified dynamic group status and varied confidence scores!")
        
    except AssertionError as e:
        print(f"\n[TEST FAILED] Assert failed: {e}")
    except Exception as e:
        print(f"\n[TEST FAILED] Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
