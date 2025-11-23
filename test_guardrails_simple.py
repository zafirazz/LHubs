#!/usr/bin/env python3
"""
Simple test script to verify compliance agent guardrail methods work correctly.
Tests guardrail logic without requiring full service initialization.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from agents.compliance.compliance_agent import ComplianceAgent


def test_domain_boundary_logic():
    """Test domain boundary detection logic."""
    print("\n" + "="*70)
    print("GUARDRAIL TEST: Domain Boundary Logic")
    print("="*70)
    
    # Create agent instance (without initializing context service)
    agent = ComplianceAgent.__new__(ComplianceAgent)
    
    # Test non-compliance queries
    non_compliance_queries = [
        "What stocks should I invest in?",
        "Which product should I recommend to clients?",
        "How do I implement a new IT system?",
        "What's the best marketing strategy?",
    ]
    
    print("\nTesting non-compliance queries (should return False):")
    all_passed = True
    for query in non_compliance_queries:
        result = agent._is_compliance_domain(query)
        status = "✓ PASS" if not result else "✗ FAIL"
        print(f"  {status}: '{query}' -> {result}")
        if result:
            all_passed = False
    
    # Test compliance queries
    compliance_queries = [
        "What are the AML compliance requirements?",
        "What is the KYC process for new clients?",
        "Are there any suspicious transactions?",
        "What is the FINMA regulation on transaction monitoring?",
    ]
    
    print("\nTesting compliance queries (should return True):")
    for query in compliance_queries:
        result = agent._is_compliance_domain(query)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: '{query}' -> {result}")
        if not result:
            all_passed = False
    
    return all_passed


def test_insufficient_information_response():
    """Test insufficient information response format."""
    print("\n" + "="*70)
    print("GUARDRAIL TEST: Insufficient Information Response")
    print("="*70)
    
    agent = ComplianceAgent.__new__(ComplianceAgent)
    
    query = "What is the compliance status of client XYZ123?"
    response = agent._get_insufficient_information_response(query)
    
    print(f"\nQuery: {query}")
    print(f"\nResponse generated:")
    print("-" * 70)
    print(response)
    print("-" * 70)
    
    # Check for required elements
    required_elements = [
        "insufficient",
        "cannot provide",
        "missing information",
        "not available",
    ]
    
    found_elements = [elem for elem in required_elements if elem.lower() in response.lower()]
    
    print(f"\nRequired elements found: {len(found_elements)}/{len(required_elements)}")
    for elem in found_elements:
        print(f"  ✓ '{elem}'")
    
    return len(found_elements) >= 2  # At least 2 required elements


def test_domain_refusal_response():
    """Test domain refusal response format."""
    print("\n" + "="*70)
    print("GUARDRAIL TEST: Domain Refusal Response")
    print("="*70)
    
    agent = ComplianceAgent.__new__(ComplianceAgent)
    
    response = agent._get_domain_refusal_response()
    
    print("\nResponse generated:")
    print("-" * 70)
    print(response)
    print("-" * 70)
    
    # Check for required elements
    required_elements = [
        "outside",
        "compliance expertise",
        "regulatory compliance",
        "aml",
        "kyc",
    ]
    
    found_elements = [elem for elem in required_elements if elem.lower() in response.lower()]
    
    print(f"\nRequired elements found: {len(found_elements)}/{len(required_elements)}")
    for elem in found_elements:
        print(f"  ✓ '{elem}'")
    
    return len(found_elements) >= 3  # At least 3 required elements


def test_answer_validation():
    """Test answer validation logic."""
    print("\n" + "="*70)
    print("GUARDRAIL TEST: Answer Validation")
    print("="*70)
    
    agent = ComplianceAgent.__new__(ComplianceAgent)
    
    # Test answer with citations
    answer_with_citations = """
    According to Context 1 - Source: transactions, Type: summary:
    The system processes 10,000 transactions with a total volume of 5,000,000 CHF.
    Based on the retrieved context, high-value transactions require enhanced monitoring.
    """
    
    # Test answer without citations
    answer_without_citations = """
    The system processes many transactions. High-value transactions are monitored.
    Compliance requirements are important.
    """
    
    # Mock context docs
    class MockDoc:
        def __init__(self):
            self.page_content = "Sample context"
            self.metadata = {"source": "test", "type": "test"}
    
    context_docs = [MockDoc(), MockDoc()]
    
    print("\nTesting answer WITH citations:")
    result1 = agent._validate_answer(answer_with_citations, context_docs)
    print(f"  Has citations: {result1['has_citations']}")
    print(f"  Warnings: {result1['warnings']}")
    print(f"  ✓ PASS" if result1['has_citations'] else "  ✗ FAIL")
    
    print("\nTesting answer WITHOUT citations:")
    result2 = agent._validate_answer(answer_without_citations, context_docs)
    print(f"  Has citations: {result2['has_citations']}")
    print(f"  Warnings: {result2['warnings']}")
    print(f"  ✓ PASS" if not result2['has_citations'] and len(result2['warnings']) > 0 else "  ✗ FAIL")
    
    return result1['has_citations'] and not result2['has_citations']


def run_all_tests():
    """Run all guardrail tests."""
    print("\n" + "="*70)
    print("COMPLIANCE AGENT GUARDRAIL TESTS (Simple)")
    print("="*70)
    print("\nTesting guardrail logic without full service initialization:")
    
    tests = [
        ("Domain Boundary Logic", test_domain_boundary_logic),
        ("Insufficient Information Response", test_insufficient_information_response),
        ("Domain Refusal Response", test_domain_refusal_response),
        ("Answer Validation", test_answer_validation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("GUARDRAIL TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<50} {status}")
    
    print(f"\nTotal: {passed}/{total} guardrail tests passed")
    
    if passed == total:
        print("\n✓ ALL GUARDRAIL TESTS PASSED!")
        print("\nThe guardrail logic is working correctly.")
        print("Note: Full integration tests require LLM service and context service initialization.")
    else:
        print(f"\n⚠ {total - passed} guardrail test(s) failed")
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit with error code if any critical guardrail tests failed
    critical_tests = ["Domain Boundary Logic", "Insufficient Information Response"]
    critical_passed = all(results.get(test, False) for test in critical_tests)
    
    sys.exit(0 if critical_passed else 1)

