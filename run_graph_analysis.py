#!/usr/bin/env python3
"""
Standalone script to run graph pattern detection.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

import logging
from services.graph_analysis_service import GraphAnalysisService

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    data_dir = "/workspace/data"
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    
    print("=" * 70)
    print("Graph Pattern Detection")
    print("=" * 70)
    
    service = GraphAnalysisService(data_dir=data_dir)
    patterns = service.detect_patterns(force_recompute=True)
    
    print(f"\n✓ Detected {len(patterns)} graph patterns")
    print(f"✓ Saved to: {service.patterns_file}")
    
    # Print summary
    by_type = {}
    by_severity = {"high": 0, "medium": 0, "low": 0}
    
    for pattern in patterns:
        ptype = pattern.get("pattern_type", "unknown")
        by_type[ptype] = by_type.get(ptype, 0) + 1
        severity = pattern.get("severity", "low")
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    print("\nPattern Summary:")
    print(f"  By Type: {by_type}")
    print(f"  By Severity: {by_severity}")
    
    if patterns:
        print("\nTop Patterns:")
        for i, pattern in enumerate(patterns[:5], 1):
            print(f"  {i}. {pattern.get('pattern_type')} - {pattern.get('severity')} severity")
            print(f"     {pattern.get('description')[:80]}...")


