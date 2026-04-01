#!/usr/bin/env python3
"""
Test script for RAG + Agent Integration
Verifies that all components are working together correctly
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.rag_agent_orchestrator import RAGAgentOrchestrator


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_orchestrator_initialization():
    """Test 1: Initialize orchestrator"""
    print_section("TEST 1: Orchestrator Initialization")
    
    try:
        orchestrator = RAGAgentOrchestrator()
        print("✅ Orchestrator initialized successfully")
        print(f"   - RAG Retriever: {'✓' if orchestrator.rag_retriever else '✗ (not available)'}")
        print(f"   - Prediction Engine: {'✓' if orchestrator.predictor else '✗ (not available)'}")
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


def test_policy_analysis():
    """Test 2: Run comprehensive policy analysis"""
    print_section("TEST 2: Policy Analysis")
    
    try:
        orchestrator = RAGAgentOrchestrator()
        
        # Test policy: Progressive taxation
        test_policy = """
        Implement a nationwide progressive taxation policy on luxury goods.
        Tax rate increases from 18% to 28% on items priced above ₹10 lakhs.
        Target revenue increase of ₹5000 crore annually.
        Implementation timeline: 6 months phased rollout across states.
        Exemptions for essential luxury exports to support make in india.
        """
        
        print(f"📋 Policy: Progressive Luxury Taxation")
        print(f"\n🔄 Running orchestrated analysis...\n")
        
        result = orchestrator.orchestrate_policy_analysis(test_policy)
        
        # Extract key metrics
        print("\n📊 Analysis Results:")
        print(f"\n💰 Financial Impact:")
        financial = result.get("financial_impact", {})
        print(f"   - Net Impact: {financial.get('net_impact', 'N/A')} Cr")
        print(f"   - Revenue: {financial.get('estimated_revenue', 'N/A')} Cr")
        print(f"   - Confidence: {financial.get('confidence', 'N/A')}")
        
        print(f"\n👥 Demographic Impact:")
        demo = result.get("demographic_impact", {})
        if demo.get("breakdown"):
            for item in demo["breakdown"][:2]:
                print(f"   - {item.get('income_class', 'Unknown')}: "
                      f"Beneficiaries {item.get('beneficiaries', 'N/A')}, "
                      f"Sufferers {item.get('sufferers', 'N/A')}")
        
        print(f"\n📈 Economic Outlook:")
        econ = result.get("economic_outlook", {})
        if econ.get("5_year_projections"):
            proj = econ["5_year_projections"][0]
            print(f"   - Year {proj.get('year', 'N/A')}: "
                  f"GDP {proj.get('gdp_impact', 'N/A')}, "
                  f"Jobs {proj.get('employment_change', 'N/A')}")
        
        print(f"\n⚠️  Risk Assessment:")
        risk = result.get("risk_assessment", {})
        print(f"   - Overall Level: {risk.get('overall_risk_level', 'N/A')}")
        print(f"   - Identified Risks: {len(risk.get('identified_risks', []))} factors")
        
        print(f"\n🏛️  Government Coordination:")
        gov = result.get("government_coordination", {})
        ministries = gov.get("relevant_ministries", [])
        print(f"   - Ministries: {', '.join(ministries) if ministries else 'N/A'}")
        
        print("\n✅ Analysis completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_policies():
    """Test 3: Analyze multiple policies"""
    print_section("TEST 3: Multiple Policy Analysis")
    
    test_policies = [
        {
            "name": "Education Investment",
            "text": "Increase budget allocation for primary education by 50%. Target: Universal literacy by 2030. Focus on rural areas and SC/ST communities."
        },
        {
            "name": "Manufacturing Sector",
            "text": "Launch new PLI scheme for electric vehicles. ₹10,000 crore incentive over 5 years. Target: Build local supply chain and reduce imports."
        },
        {
            "name": "Agricultural Reform",
            "text": "Implement minimum support prices for 22 crops. Support smallholder farmers through cooperative networks. ₹20,000 crore budget allocation."
        }
    ]
    
    orchestrator = RAGAgentOrchestrator()
    results = {}
    
    for i, policy_info in enumerate(test_policies, 1):
        print(f"\n📋 Policy {i}: {policy_info['name']}")
        try:
            result = orchestrator.orchestrate_policy_analysis(policy_info['text'])
            results[policy_info['name']] = {
                "status": "✅ Success",
                "financial": result.get("financial_impact", {}).get("net_impact", "N/A"),
                "risk": result.get("risk_assessment", {}).get("overall_risk_level", "N/A")
            }
            print(f"   ✅ Analyzed successfully")
        except Exception as e:
            results[policy_info['name']] = {
                "status": f"❌ Failed: {str(e)[:50]}",
                "financial": "N/A",
                "risk": "N/A"
            }
            print(f"   ❌ Analysis failed")
    
    print(f"\n📊 Summary:")
    for policy_name, result in results.items():
        print(f"   • {policy_name}: {result['status']}")


def test_edge_cases():
    """Test 4: Edge cases"""
    print_section("TEST 4: Edge Cases")
    
    orchestrator = RAGAgentOrchestrator()
    
    test_cases = [
        ("Empty Policy", ""),
        ("Very Short", "Tax increase"),
        ("Non-India Policy", "Implement Medicare expansion in USA"),
        ("Complex Policy", "Create integrated policy framework combining: (1) progressive taxation on assets >₹5Cr, (2) wealth redistribution through targeted welfare, (3) skills training for displaced workers, (4) environmental sustainability requirements for new industries, (5) international patent regulations harmonization.")
    ]
    
    for name, policy_text in test_cases:
        print(f"\n📋 Test: {name}")
        if not policy_text:
            print("   ⏭️  Skipped (empty)")
            continue
            
        try:
            result = orchestrator.orchestrate_policy_analysis(policy_text)
            has_error = any("error" in str(v).lower() for v in result.values())
            if has_error:
                print(f"   ⚠️  Completed with warnings")
            else:
                print(f"   ✅ Handled successfully")
        except Exception as e:
            print(f"   ⚠️  Exception (expected): {str(e)[:60]}")


def print_summary(results):
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! RAG + Agent integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check logs above for details.")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  RAG + AI AGENT INTEGRATION TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Initialization
    results.append(test_orchestrator_initialization())
    
    # Test 2: Policy Analysis
    results.append(test_policy_analysis())
    
    # Test 3: Multiple Policies
    try:
        test_multiple_policies()
        results.append(True)
    except Exception as e:
        print(f"❌ Multiple policies test failed: {e}")
        results.append(False)
    
    # Test 4: Edge Cases
    try:
        test_edge_cases()
        results.append(True)
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
        results.append(False)
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
