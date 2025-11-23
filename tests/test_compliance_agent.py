#!/usr/bin/env python3
"""
Comprehensive test suite for Compliance Agent implementation.
Tests each component step by step.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add src to path - FIX: Use parent.parent to get to project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Now imports should work
from services.llm_service import LLMService
from services.context_service import ContextService
from agents.compliance.compliance_agent import ComplianceAgent


def test_1_dependencies():
    """Test 1: Check if all required dependencies are installed."""
    print("\n" + "="*70)
    print("TEST 1: Dependencies Check")
    print("="*70)
    
    results = {}
    
    # Check pandas
    try:
        import pandas as pd
        print(f"✓ pandas: {pd.__version__}")
        results["pandas"] = True
    except ImportError:
        print("✗ pandas: NOT INSTALLED")
        results["pandas"] = False
    
    # Check langchain
    try:
        import langchain
        print(f"✓ langchain: {langchain.__version__}")
        results["langchain"] = True
    except ImportError:
        print("✗ langchain: NOT INSTALLED")
        results["langchain"] = False
    
    # Check chromadb
    try:
        import chromadb
        print(f"✓ chromadb: {chromadb.__version__}")
        results["chromadb"] = True
    except ImportError:
        print("✗ chromadb: NOT INSTALLED (install with: pip install chromadb)")
        results["chromadb"] = False
    
    # Check sentence-transformers
    try:
        import sentence_transformers
        print(f"✓ sentence-transformers: {sentence_transformers.__version__}")
        results["sentence_transformers"] = True
    except ImportError:
        print("✗ sentence-transformers: NOT INSTALLED (install with: pip install sentence-transformers)")
        results["sentence_transformers"] = False
    
    all_ok = all(results.values())
    print(f"\n{'✓ ALL DEPENDENCIES OK' if all_ok else '✗ SOME DEPENDENCIES MISSING'}")
    return all_ok, results


def test_2_data_files():
    """Test 2: Check if data files exist."""
    print("\n" + "="*70)
    print("TEST 2: Data Files Check")
    print("="*70)
    
    data_dir = Path("/workspace/data")
    required_files = [
        "client_onboarding_notes.csv",
        "account.csv",
        "transactions.csv",
    ]
    
    results = {}
    for file in required_files:
        file_path = data_dir / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✓ {file}: {size_mb:.2f} MB")
            results[file] = True
        else:
            print(f"✗ {file}: NOT FOUND")
            results[file] = False
    
    all_ok = all(results.values())
    print(f"\n{'✓ ALL DATA FILES FOUND' if all_ok else '✗ SOME FILES MISSING'}")
    return all_ok, results


def test_3_context_service_loading():
    """Test 3: Context Service can load data."""
    print("\n" + "="*70)
    print("TEST 3: Context Service - Data Loading")
    print("="*70)
    
    try:
        context_service = ContextService(data_dir="/workspace/data")
        print("✓ ContextService created")
        
        print("Loading documents...")
        documents = context_service.load_data()
        
        if documents:
            print(f"✓ Loaded {len(documents)} documents")
            for doc in documents[:3]:
                source = doc.metadata.get("source", "unknown")
                doc_type = doc.metadata.get("type", "unknown")
                print(f"  - {source} ({doc_type}): {len(doc.page_content)} chars")
            return True, len(documents)
        else:
            print("✗ No documents loaded")
            return False, 0
            
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def test_4_context_service_chunking():
    """Test 4: Context Service can chunk documents."""
    print("\n" + "="*70)
    print("TEST 4: Context Service - Document Chunking")
    print("="*70)
    
    try:
        context_service = ContextService(data_dir="/workspace/data")
        documents = context_service.load_data()
        
        if not documents:
            print("✗ No documents to chunk")
            return False, 0
        
        print(f"Chunking {len(documents)} documents...")
        chunked_docs = context_service.chunk_documents(documents)
        
        if chunked_docs:
            print(f"✓ Created {len(chunked_docs)} chunks")
            print(f"  Average chunks per document: {len(chunked_docs) / len(documents):.1f}")
            print(f"  Sample chunk length: {len(chunked_docs[0].page_content)} chars")
            return True, len(chunked_docs)
        else:
            print("✗ No chunks created")
            return False, 0
            
    except Exception as e:
        print(f"✗ Error chunking documents: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def test_5_context_service_vector_store():
    """Test 5: Context Service can build vector store."""
    print("\n" + "="*70)
    print("TEST 5: Context Service - Vector Store Building")
    print("="*70)
    
    try:
        context_service = ContextService(
            data_dir="/workspace/data",
            persist_directory="./data/vector_db_test",
        )
        
        print("Building vector store (this may take a few minutes)...")
        context_service.build_vector_store(force_rebuild=True)
        
        if context_service.vector_store is not None:
            print("✓ Vector store built successfully")
            print(f"  Persist directory: {context_service.persist_directory}")
            return True
        else:
            print("✗ Vector store is None")
            return False
            
    except Exception as e:
        print(f"✗ Error building vector store: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_context_service_retrieval():
    """Test 6: Context Service can retrieve relevant context."""
    print("\n" + "="*70)
    print("TEST 6: Context Service - Context Retrieval")
    print("="*70)
    
    try:
        context_service = ContextService(
            data_dir="/workspace/data",
            persist_directory="./data/vector_db_test",
        )
        
        if not context_service._initialized:
            print("Initializing vector store...")
            context_service.build_vector_store(force_rebuild=False)
        
        test_queries = [
            "client onboarding",
            "transaction patterns",
            "account information",
        ]
        
        all_passed = True
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = context_service.retrieve_context(query=query, k=3)
            
            if results:
                print(f"  ✓ Retrieved {len(results)} documents")
                for i, doc in enumerate(results[:2], 1):
                    source = doc.metadata.get("source", "unknown")
                    print(f"    {i}. {source}: {doc.page_content[:80]}...")
            else:
                print(f"  ✗ No results retrieved")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error retrieving context: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_7_llm_service():
    """Test 7: LLM Service can be initialized."""
    print("\n" + "="*70)
    print("TEST 7: LLM Service Initialization")
    print("="*70)
    
    try:
        llm_service = LLMService(
            model_path="/workspace/gpt-oss-20b/gpt-oss-20b-mxfp4.gguf",
            temperature=0.1,
            max_tokens=512,
        )
        
        print("Initializing LLM Service (this may take a moment)...")
        llm_service.initialize()
        print("✓ LLM Service initialized")
        
        # Quick generation test
        print("Testing generation...")
        response = llm_service.generate(
            prompt="Say hello in one sentence:",
            max_new_tokens=20,
        )
        
        if response:
            print(f"✓ Generation works: {response[:50]}...")
            return True
        else:
            print("✗ Generation returned empty")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_8_compliance_agent_creation():
    """Test 8: Compliance Agent can be created."""
    print("\n" + "="*70)
    print("TEST 8: Compliance Agent - Creation")
    print("="*70)
    
    try:
        # Initialize services
        context_service = ContextService(
            data_dir="/workspace/data",
            persist_directory="./data/vector_db_test",
        )
        context_service.initialize()
        
        llm_service = LLMService(
            model_path="/workspace/gpt-oss-20b/gpt-oss-20b-mxfp4.gguf",
            temperature=0.1,
            max_tokens=512,
        )
        llm_service.initialize()
        
        # Create agent
        print("Creating Compliance Agent...")
        agent = ComplianceAgent(
            llm_service=llm_service,
            context_service=context_service,
        )
        
        print("✓ Compliance Agent created")
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Name: {agent.name}")
        print(f"  Required inputs: {agent.get_required_inputs()}")
        
        return True, agent
        
    except Exception as e:
        print(f"✗ Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_9_compliance_agent_query():
    """Test 9: Compliance Agent can answer queries."""
    print("\n" + "="*70)
    print("TEST 9: Compliance Agent - Query Processing")
    print("="*70)
    
    try:
        # Get agent from previous test
        agent_ok, agent = test_8_compliance_agent_creation()
        if not agent_ok or agent is None:
            print("✗ Cannot proceed without agent")
            return False
        
        test_query = "What are the characteristics of clients opening accounts?"
        print(f"Query: {test_query}")
        
        result = agent.execute(
            input_data={"query": test_query},
            task_id="test-query-001"
        )
        
        print(f"\n✓ Query processed successfully")
        print(f"  Answer length: {len(result.get('answer', ''))} chars")
        print(f"  Confidence: {result.get('confidence', 'unknown')}")
        print(f"  Sources: {len(result.get('sources', []))}")
        print(f"\n  Answer preview: {result.get('answer', '')[:200]}...")
        
        # Validate output schema
        required_fields = ["answer", "sources", "confidence", "context_used"]
        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"  ⚠ Missing fields: {missing}")
        else:
            print(f"  ✓ All required fields present")
        
        return True
        
    except Exception as e:
        print(f"✗ Error processing query: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and provide summary."""
    print("\n" + "="*70)
    print("COMPLIANCE AGENT TEST SUITE")
    print("="*70)
    
    tests = [
        ("Dependencies", test_1_dependencies),
        ("Data Files", test_2_data_files),
        ("Context Loading", test_3_context_service_loading),
        ("Document Chunking", test_4_context_service_chunking),
        ("Vector Store", test_5_context_service_vector_store),
        ("Context Retrieval", test_6_context_service_retrieval),
        ("LLM Service", test_7_llm_service),
        ("Agent Creation", test_8_compliance_agent_creation),
        ("Agent Query", test_9_compliance_agent_query),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_name == "Agent Query":
                # Skip if agent creation failed
                if not results.get("Agent Creation", (False, None))[0]:
                    print(f"\n⚠ Skipping {test_name} (prerequisite failed)")
                    results[test_name] = False
                    continue
            
            result = test_func()
            if isinstance(result, tuple):
                results[test_name] = result[0] if len(result) > 0 else False
            else:
                results[test_name] = result
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<50} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Compliance Agent is working!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        print("\nTroubleshooting:")
        if not results.get("Dependencies"):
            print("- Install missing dependencies: pip install chromadb sentence-transformers")
        if not results.get("Data Files"):
            print("- Check that data files exist in /workspace/data")
        if not results.get("LLM Service"):
            print("- Verify model file exists and LLMService can load it")
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit with error code if critical tests failed
    critical_tests = ["Dependencies", "Data Files", "Context Loading", "Vector Store"]
    critical_passed = all(results.get(test, False) for test in critical_tests)
    
    sys.exit(0 if critical_passed else 1)