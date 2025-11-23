#!/usr/bin/env python3
"""
Script to generate pre-computed summaries from data.
Run this once before using the Compliance Agent.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.summary_generator import SummaryGenerator
import logging

logging.basicConfig(level=logging.INFO)

def main():
    data_dir = "/workspace/data"
    output_file = "./data/compliance_summaries.json"
    
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print("="*70)
    print("Generating Pre-computed Summaries")
    print("="*70)
    print(f"Data directory: {data_dir}")
    print(f"Output file: {output_file}")
    print()
    
    generator = SummaryGenerator(data_dir=data_dir)
    summaries = generator.generate_all_summaries()
    
    output_path = generator.save_summaries(summaries, output_file)
    
    print()
    print("="*70)
    print(f"✓ Successfully generated {len(summaries)} summaries")
    print(f"✓ Saved to: {output_path}")
    print("="*70)
    print()
    print("You can now use the Compliance Agent with fast, pre-computed summaries!")

if __name__ == "__main__":
    main()

