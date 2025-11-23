#!/usr/bin/env python3
"""
Quick test script for AML Analysis Agent.
Tests the system with sample data or a provided Excel file.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

import logging
from agents.aml_analysis import AMLAnalysisAgent

logging.basicConfig(level=logging.INFO)

def main():
    print("=" * 70)
    print("AML Analysis Agent - Test Script")
    print("=" * 70)
    
    # Check if Excel file provided
    excel_file = None
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        if not Path(excel_file).exists():
            print(f"Error: File not found: {excel_file}")
            return 1
    else:
        print("\nUsage: python run_aml_analysis.py <excel_file.xlsx>")
        print("\nOr run Streamlit app: streamlit run streamlit_aml_app.py")
        return 1
    
    print(f"\nAnalyzing Excel file: {excel_file}")
    print("-" * 70)
    
    try:
        # Initialize agent
        print("Initializing AML Analysis Agent...")
        agent = AMLAnalysisAgent()
        
        # Process file
        print("Processing Excel file...")
        result = agent.process({
            "excel_file_path": excel_file
        })
        
        # Display results
        print("\n" + "=" * 70)
        print("ANALYSIS RESULTS")
        print("=" * 70)
        
        # Summary
        print("\nSummary:")
        print(result.get("summary", "No summary available"))
        
        # Risk assessment
        risk_assessment = result.get("risk_assessment", {})
        print(f"\nRisk Level: {risk_assessment.get('overall_risk', 'unknown').upper()}")
        print(f"Recommendation: {risk_assessment.get('recommendation', 'N/A')}")
        
        # Patterns
        patterns = result.get("patterns_detected", [])
        print(f"\nPatterns Detected: {len(patterns)}")
        
        if patterns:
            # Group by type
            by_type = {}
            for pattern in patterns:
                ptype = pattern.get("pattern_type", "unknown")
                by_type[ptype] = by_type.get(ptype, 0) + 1
            
            print("\nPattern Breakdown:")
            for ptype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {ptype.replace('_', ' ').title()}: {count}")
        
        # PDF report
        pdf_path = result.get("pdf_report_path")
        if pdf_path and Path(pdf_path).exists():
            print(f"\n✓ PDF Report Generated: {pdf_path}")
            print(f"  File size: {Path(pdf_path).stat().st_size / 1024:.1f} KB")
        else:
            print("\n⚠ PDF report path not available (may be in temp directory)")
        
        print("\n" + "=" * 70)
        print("Analysis Complete!")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

