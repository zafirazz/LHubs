#!/usr/bin/env python3
"""
Create a sample Excel file for testing AML Analysis Agent.
"""

import pandas as pd
from pathlib import Path

def create_sample_excel(output_path: str = "sample_aml_data.xlsx"):
    """Create a sample Excel file with accounts and transactions."""
    
    # Create Accounts sheet
    accounts_data = {
        "Account ID": [
            "ACC001",
            "ACC002", 
            "ACC003",
            "ACC004",
            "ACC005",
            "ACC006",
            "ACC007",
            "ACC008",
            "ACC009",
            "ACC010"
        ],
        "IBAN": [
            "CH1234567890123456789",
            "CH9876543210987654321",
            "CH5555555555555555555",
            "CH1111111111111111111",
            "CH2222222222222222222",
            "CH3333333333333333333",
            "CH4444444444444444444",
            "CH6666666666666666666",
            "CH7777777777777777777",
            "CH8888888888888888888"
        ],
        "Account Holder": [
            "John Doe",
            "Jane Smith",
            "ABC Corporation",
            "XYZ Ltd",
            "Test Company",
            "Sample Business",
            "Demo Account",
            "Example Corp",
            "Sample LLC",
            "Test Holdings"
        ]
    }
    
    df_accounts = pd.DataFrame(accounts_data)
    
    # Create Transactions sheet with some patterns (50 transactions)
    num_tx = 50
    
    # Build transaction lists with proper patterns
    from_accounts = []
    to_accounts = []
    amounts = []
    
    # Fan-out pattern: ACC001 sends to many (10 transactions)
    for i in range(10):
        from_accounts.append("ACC001")
        to_accounts.append(f"ACC{(i % 9) + 2:03d}")  # ACC002 to ACC010
        amounts.append(1000.00 + i * 200)
    
    # Fan-in pattern: Many send to ACC002 (10 transactions)
    for i in range(10):
        from_accounts.append(f"ACC{(i % 8) + 3:03d}")  # ACC003 to ACC010
        to_accounts.append("ACC002")
        amounts.append(2000.00 + i * 300)
    
    # Gather-scatter: ACC002 receives and sends (10 transactions)
    for i in range(5):
        from_accounts.append(f"ACC{(i % 8) + 3:03d}")  # Sources
        to_accounts.append("ACC002")
        amounts.append(3000.00 + i * 200)
    for i in range(5):
        from_accounts.append("ACC002")
        to_accounts.append(f"ACC{(i % 8) + 3:03d}")  # Destinations
        amounts.append(2500.00 + i * 200)
    
    # Simple cycle: ACC003 -> ACC004 -> ACC005 -> ACC003 (4 transactions)
    cycle = ["ACC003", "ACC004", "ACC005", "ACC003"]
    for i in range(4):
        from_accounts.append(cycle[i])
        to_accounts.append(cycle[(i + 1) % 4])
        amounts.append(1500.00 + i * 100)
    
    # More transactions to reach 50 total
    remaining = num_tx - len(from_accounts)
    for i in range(remaining):
        from_accounts.append(f"ACC{(i % 10) + 1:03d}")
        to_accounts.append(f"ACC{((i + 1) % 10) + 1:03d}")
        amounts.append(1000.00 + (i % 20) * 150)
    
    transactions_data = {
        "Transaction ID": [f"TX{i:03d}" for i in range(1, num_tx + 1)],
        "From Account": from_accounts,
        "To Account": to_accounts,
        "Amount": amounts,
        "Date": [f"2024-01-{i%28+1:02d}" for i in range(num_tx)],
        "Transaction Type": ["Transfer" if i % 2 == 0 else "Payment" for i in range(num_tx)],
        "Currency": ["CHF" if i % 3 != 0 else "EUR" for i in range(num_tx)],
        "Description": [f"Transaction {i+1}" for i in range(num_tx)]
    }
    
    df_transactions = pd.DataFrame(transactions_data)
    
    # Write to Excel with two sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_accounts.to_excel(writer, sheet_name='Accounts', index=False)
        df_transactions.to_excel(writer, sheet_name='Transactions', index=False)
    
    print(f"✓ Sample Excel file created: {output_path}")
    print(f"  - Accounts: {len(df_accounts)} accounts")
    print(f"  - Transactions: {len(df_transactions)} transactions")
    print(f"\nThis file contains sample patterns:")
    print("  - Fan-out: ACC001 sends to 10 different accounts")
    print("  - Fan-in: 10 accounts send to ACC002")
    print("  - Gather-scatter: ACC002 receives and sends")
    print("  - Simple cycle: ACC003 → ACC004 → ACC005 → ACC003")
    print(f"\nYou can use this file to test the AML Analysis Agent!")

if __name__ == "__main__":
    import sys
    output_file = sys.argv[1] if len(sys.argv) > 1 else "sample_aml_data.xlsx"
    create_sample_excel(output_file)

