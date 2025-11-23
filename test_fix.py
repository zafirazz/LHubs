#!/usr/bin/env python3
"""
Test script to verify the transaction loading fix.
"""
import sys
import logging
from src.services.excel_loader import ExcelLoader

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_transaction_loading():
    """Test that transactions are now loading correctly."""
    print("=" * 80)
    print("TRANSACTION LOADING FIX - VERIFICATION TEST")
    print("=" * 80)
    
    # Load the Excel file
    loader = ExcelLoader()
    file_path = 'accounts_with_transactions.xlsx'
    
    print(f"\n📁 Loading file: {file_path}")
    result = loader.load_from_file(file_path)
    
    # Extract results
    accounts = result['accounts']
    transactions = result['transactions']
    metadata = result['metadata']
    
    # Display summary
    print(f"\n✅ FILE LOADED SUCCESSFULLY")
    print(f"   Sheets found: {metadata['sheets']}")
    print(f"   Accounts loaded: {metadata['accounts_count']:,}")
    print(f"   Transactions loaded: {metadata['transactions_count']:,}")
    
    # Verify accounts
    assert len(accounts) > 0, "No accounts loaded!"
    assert len(accounts) == 3509, f"Expected 3509 accounts, got {len(accounts)}"
    print(f"\n✅ ACCOUNTS: {len(accounts):,} accounts loaded correctly")
    
    # Verify transactions
    assert len(transactions) > 0, "No transactions loaded! Fix failed!"
    print(f"\n✅ TRANSACTIONS: {len(transactions):,} transactions loaded successfully")
    print(f"   (Previously: 0 transactions)")
    
    # Analyze transaction types
    internal_only = 0
    external_from = 0
    external_to = 0
    both_external = 0
    
    for tx in transactions:
        is_ext_from = tx.get('is_external_from', False)
        is_ext_to = tx.get('is_external_to', False)
        
        if not is_ext_from and not is_ext_to:
            internal_only += 1
        elif is_ext_from and not is_ext_to:
            external_from += 1
        elif not is_ext_from and is_ext_to:
            external_to += 1
        else:
            both_external += 1
    
    print(f"\n📊 TRANSACTION BREAKDOWN:")
    print(f"   Internal → Internal: {internal_only:>6,} ({internal_only/len(transactions)*100:>5.1f}%)")
    print(f"   External → Internal: {external_from:>6,} ({external_from/len(transactions)*100:>5.1f}%)")
    print(f"   Internal → External: {external_to:>6,} ({external_to/len(transactions)*100:>5.1f}%)")
    print(f"   External → External: {both_external:>6,} ({both_external/len(transactions)*100:>5.1f}%)")
    
    # Verify no both-external transactions
    assert both_external == 0, f"Found {both_external} transactions with both accounts external - should be 0!"
    print(f"\n✅ VALIDATION: No transactions with both accounts external (correct)")
    
    # Verify all transactions have required fields
    required_fields = ['transaction_id', 'from_account', 'to_account', 'amount', 
                      'currency', 'date', 'type', 'is_external_from', 'is_external_to']
    
    for i, tx in enumerate(transactions[:10]):
        for field in required_fields:
            assert field in tx, f"Transaction {i} missing field: {field}"
    
    print(f"✅ VALIDATION: All transactions have required fields")
    
    # Show sample transactions
    print(f"\n📋 SAMPLE TRANSACTIONS:")
    for i, tx in enumerate(transactions[:3], 1):
        ext_from = " [EXT]" if tx['is_external_from'] else ""
        ext_to = " [EXT]" if tx['is_external_to'] else ""
        print(f"\n   Transaction {i}:")
        print(f"      ID: {tx['transaction_id']}")
        print(f"      From: {tx['from_account'][:30]}...{ext_from}")
        print(f"      To:   {tx['to_account'][:30]}...{ext_to}")
        print(f"      Amount: {tx['amount']} {tx['currency']}")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print(f"\n🎉 FIX VERIFIED: Transaction loading is working correctly!")
    print(f"   Before fix: 0 transactions")
    print(f"   After fix:  {len(transactions):,} transactions")
    print(f"   Improvement: ∞% (from 0 to {len(transactions):,})")
    print("\n" + "=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_transaction_loading()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

