# Transaction Loading Diagnostic Report

## File Analyzed
`/workspace/LHubs_Zafira/accounts_with_transactions.xlsx`

## 🔴 ROOT CAUSE: Zero Transactions Loaded

### Summary
**0 transactions are loaded because the loader requires BOTH accounts (from & to) to exist in the Excel file, but the transaction data uses a different account ID system.**

### Detailed Analysis

#### 1. Excel File Contents
- **File**: `accounts_with_transactions.xlsx`
- **Sheets**: 1 sheet named "Sheet1"
- **Columns**: `account_id`, `account_iban`
- **Rows**: 3,509 accounts
- **Note**: Despite the filename, this file contains **NO transactions**, only accounts

#### 2. Transaction Data Source
- **File**: `/workspace/data/transactions.csv`
- **Total rows**: 648,894 transactions
- **Columns**:
  - `Transaction ID`: Unique transaction ID
  - `Debit/Credit`: Transaction direction
  - `Account ID`: Account in different UUID system (NOT matching Excel)
  - `Amount`, `Balance`, `Currency`, `Date`, `Transfer_Type`
  - `counterparty_Account_ID`: Internal counterparty (UUID)
  - `ext_counterparty_Account_ID`: External counterparty (IBAN format)
  - `ext_counterparty_country`: Country code

#### 3. The Account ID Mismatch

**Excel accounts use UUIDs like:**
```
d5d0fe77-0d6e-4013-a4c4-af243be66f8d
33293396-7bce-4276-bac4-6e0961adab35
```

**Transaction "Account ID" column uses DIFFERENT UUIDs like:**
```
4e573f24-cd2b-4074-86a8-0b3414cedd57
5c160864-2fda-422d-b8a7-4db39ae3fa43
```

**BUT, the `ext_counterparty_Account_ID` column contains IBANs that DO match Excel:**
```
CH6983510176060328354 ← Matches Excel IBAN
CH9279124677076517552 ← Matches Excel IBAN
```

#### 4. Matching Results (sample of 10,000 transactions)

| Scenario | Count | Percentage |
|----------|-------|------------|
| **Both accounts found** | 0 | 0.0% |
| From account only | 1,782 | 17.8% |
| To account only | 1,825 | 18.2% |
| Neither found | 6,393 | 63.9% |

#### 5. Why Zero Transactions Are Loaded

The loader (`excel_loader.py` line 395) uses this logic:
```python
if from_account and to_account:
    # Only include transaction if BOTH accounts found
    transactions.append(transaction)
```

**Problem**: Since the main `Account ID` in transactions uses a different ID system, the "from" account is never found, even though the "to" account (counterparty) often IS found by IBAN matching.

**Result**: 0 transactions pass the filter.

### Data Model Explanation

The transaction data uses a **Debit/Credit ledger format**:

**For DEBIT transactions:**
- `Account ID` = account being debited (money leaving)
- `ext_counterparty_Account_ID` = recipient IBAN (money arriving)

**For CREDIT transactions:**
- `Account ID` = account being credited (money arriving)
- `ext_counterparty_Account_ID` = sender IBAN (money leaving)

### Why This Design Exists

The Excel file appears to contain a **subset of accounts** (3,509 out of a larger system). The transaction log contains ALL transactions in the system, including:
- Transactions between accounts in the subset
- Transactions from subset accounts to external accounts
- Transactions from external accounts to subset accounts

The different Account ID systems suggest:
- `Account ID` in transactions = Full bank system IDs
- `account_id` in Excel = Risk analysis subset IDs
- IBANs = Common identifier linking both systems

## ✅ SOLUTION

### Option 1: Relaxed Matching (Recommended)
Modify the loader to include transactions where **at least one account** is found, creating placeholder entries for external accounts.

### Option 2: IBAN-Only Matching
Focus only on `ext_counterparty_Account_ID` (IBAN) field and ignore `Account ID` field entirely.

### Option 3: Load All Accounts First
Load the complete account list from `/workspace/data/account.csv` (5,000 accounts) which contains ALL accounts referenced in transactions.

## Recommended Fix

See `excel_loader_fixed.py` for a patched version that implements Option 1.

