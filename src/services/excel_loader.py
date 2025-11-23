"""
Excel Loader - Loads accounts from Excel files and transactions from CSV files.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import io

logger = logging.getLogger(__name__)


class ExcelLoader:
    """
    Loads account data from Excel files and transaction data from CSV files.
    
    Only requires Accounts sheet in Excel. Transactions are loaded from CSV files
    and matched to accounts by account_id or IBAN.
    """
    
    def __init__(self, transactions_csv_path: Optional[str] = None):
        """
        Initialize Excel loader.
        
        Args:
            transactions_csv_path: Path to transactions CSV file. 
                                 If None, looks for transactions.csv in data directory.
        """
        self.accounts: List[Dict[str, Any]] = []
        self.transactions: List[Dict[str, Any]] = []
        self.transactions_csv_path = Path(transactions_csv_path) if transactions_csv_path else None
    
    def load_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load data from Excel file.
        
        Expected sheets:
        - 'accounts' or 'Accounts': Account data with IBANs
        - 'transactions' or 'Transactions': Transaction data
        
        Returns:
            Dict with 'accounts' and 'transactions' lists
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            logger.info(f"Excel sheets found: {sheet_names}")
            
            accounts = []
            transactions = []
            
            # Try to find accounts and transactions by sheet name first
            accounts_sheet = None
            transactions_sheet = None
            
            for sheet in sheet_names:
                sheet_lower = sheet.lower()
                if 'account' in sheet_lower and not accounts_sheet:
                    accounts_sheet = sheet
                if 'transaction' in sheet_lower and not transactions_sheet:
                    transactions_sheet = sheet
            
            # If no named sheets found, try to detect by column content
            if not accounts_sheet or not transactions_sheet:
                for sheet in sheet_names:
                    try:
                        df_test = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
                        columns_lower = [col.lower() for col in df_test.columns]
                        
                        # Check if this looks like accounts data
                        has_account_id = any('account' in col and 'id' in col for col in columns_lower)
                        has_iban = any('iban' in col for col in columns_lower)
                        if (has_account_id or has_iban) and not accounts_sheet:
                            accounts_sheet = sheet
                            logger.info(f"Detected accounts sheet by columns: '{sheet}'")
                        
                        # Check if this looks like transactions data
                        has_from = any('from' in col or 'sender' in col or 'debit' in col for col in columns_lower)
                        has_to = any('to' in col or 'receiver' in col or 'credit' in col or 'recipient' in col for col in columns_lower)
                        has_amount = any('amount' in col for col in columns_lower)
                        if has_from and has_to and has_amount and not transactions_sheet:
                            transactions_sheet = sheet
                            logger.info(f"Detected transactions sheet by columns: '{sheet}'")
                    except Exception as e:
                        logger.debug(f"Error checking sheet {sheet}: {e}")
                        continue
            
            # Load accounts
            if accounts_sheet:
                df_accounts = pd.read_excel(file_path, sheet_name=accounts_sheet)
                logger.info(f"Loading accounts from sheet '{accounts_sheet}'")
                accounts = self._normalize_accounts(df_accounts)
                logger.info(f"Loaded {len(accounts)} accounts")
            else:
                logger.warning("No accounts sheet found - trying all sheets...")
                # Try all sheets as accounts
                for sheet in sheet_names:
                    try:
                        df_test = pd.read_excel(file_path, sheet_name=sheet)
                        accounts_temp = self._normalize_accounts(df_test)
                        if accounts_temp:
                            accounts = accounts_temp
                            logger.info(f"Found accounts in sheet '{sheet}': {len(accounts)} accounts")
                            break
                    except:
                        continue
            
            # Load transactions from CSV file (not from Excel)
            transactions = self._load_transactions_from_csv(accounts)
            logger.info(f"Loaded {len(transactions)} transactions from CSV")
            
            return {
                "accounts": accounts,
                "transactions": transactions,
                "metadata": {
                    "file_path": str(file_path),
                    "sheets": sheet_names,
                    "accounts_count": len(accounts),
                    "transactions_count": len(transactions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            raise
    
    def load_from_bytes(self, file_bytes: bytes, filename: str = "upload.xlsx") -> Dict[str, Any]:
        """Load data from Excel file bytes (for Streamlit uploads)."""
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet_names = excel_file.sheet_names
            logger.info(f"Excel sheets found: {sheet_names}")
            
            accounts = []
            transactions = []
            
            # Try to find accounts and transactions by sheet name first
            accounts_sheet = None
            transactions_sheet = None
            
            for sheet in sheet_names:
                sheet_lower = sheet.lower()
                if 'account' in sheet_lower and not accounts_sheet:
                    accounts_sheet = sheet
                if 'transaction' in sheet_lower and not transactions_sheet:
                    transactions_sheet = sheet
            
            # If no named sheets found, try to detect by column content
            if not accounts_sheet or not transactions_sheet:
                for sheet in sheet_names:
                    try:
                        df_test = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet, nrows=5)
                        columns_lower = [col.lower().replace('_', ' ') for col in df_test.columns]
                        
                        # Check if this looks like accounts data
                        has_account_id = any('account' in col and 'id' in col for col in columns_lower)
                        has_iban = any('iban' in col for col in columns_lower)
                        if (has_account_id or has_iban) and not accounts_sheet:
                            accounts_sheet = sheet
                            logger.info(f"Detected accounts sheet by columns: '{sheet}'")
                        
                        # Check if this looks like transactions data
                        has_from = any('from' in col or 'sender' in col or 'debit' in col for col in columns_lower)
                        has_to = any('to' in col or 'receiver' in col or 'credit' in col or 'recipient' in col for col in columns_lower)
                        has_amount = any('amount' in col for col in columns_lower)
                        if has_from and has_to and has_amount and not transactions_sheet:
                            transactions_sheet = sheet
                            logger.info(f"Detected transactions sheet by columns: '{sheet}'")
                    except Exception as e:
                        logger.debug(f"Error checking sheet {sheet}: {e}")
                        continue
            
            # Load accounts
            if accounts_sheet:
                df_accounts = pd.read_excel(io.BytesIO(file_bytes), sheet_name=accounts_sheet)
                logger.info(f"Loading accounts from sheet '{accounts_sheet}'")
                accounts = self._normalize_accounts(df_accounts)
                logger.info(f"Loaded {len(accounts)} accounts")
            else:
                logger.warning("No accounts sheet found - trying all sheets...")
                # Try all sheets as accounts
                for sheet in sheet_names:
                    try:
                        df_test = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet)
                        accounts_temp = self._normalize_accounts(df_test)
                        if accounts_temp:
                            accounts = accounts_temp
                            logger.info(f"Found accounts in sheet '{sheet}': {len(accounts)} accounts")
                            break
                    except:
                        continue
            
            # Load transactions
            if transactions_sheet:
                df_transactions = pd.read_excel(io.BytesIO(file_bytes), sheet_name=transactions_sheet)
                logger.info(f"Loading transactions from sheet '{transactions_sheet}'")
                transactions = self._normalize_transactions(df_transactions)
                logger.info(f"Loaded {len(transactions)} transactions")
            else:
                logger.warning("No transactions sheet found - trying all sheets...")
                # Try all sheets as transactions
                for sheet in sheet_names:
                    try:
                        df_test = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet)
                        transactions_temp = self._normalize_transactions(df_test)
                        if transactions_temp:
                            transactions = transactions_temp
                            logger.info(f"Found transactions in sheet '{sheet}': {len(transactions)} transactions")
                            break
                    except:
                        continue
            
            return {
                "accounts": accounts,
                "transactions": transactions,
                "metadata": {
                    "filename": filename,
                    "sheets": sheet_names,
                    "accounts_count": len(accounts),
                    "transactions_count": len(transactions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading Excel from bytes: {e}")
            raise
    
    def _normalize_accounts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Normalize account data to standard format."""
        accounts = []
        
        for _, row in df.iterrows():
            # Try to find Account ID (handles account_id, Account ID, etc.)
            account_id = None
            for col in df.columns:
                col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                if 'account' in col_lower and 'id' in col_lower:
                    val = str(row[col]).strip()
                    if val and val != "nan" and val.lower() != "none":
                        account_id = val
                        break
            
            # Try to find IBAN (handles account_iban, Account IBAN, etc.)
            iban = None
            for col in df.columns:
                col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                if 'iban' in col_lower:
                    val = str(row[col]).strip()
                    if val and val != "nan" and val.lower() != "none":
                        iban = val
                        break
            
            # Use IBAN as account_id if Account ID not found
            if not account_id and iban:
                account_id = iban
            
            # Account is valid if we have either Account ID or IBAN
            if account_id:
                # Try to find account holder (optional)
                holder = None
                for col in df.columns:
                    col_lower = col.lower()
                    if ('holder' in col_lower or 'name' in col_lower or 'owner' in col_lower) and \
                       'account' not in col_lower:  # Avoid matching "Account ID"
                        val = str(row[col]).strip()
                        if val and val != "nan":
                            holder = val
                            break
                
                account = {
                    "account_id": str(account_id),
                    "iban": iban if iban and iban != "nan" else None,
                    "holder": holder if holder and holder != "nan" else None,
                    "metadata": {}
                }
                accounts.append(account)
        
        return accounts
    
    def _load_transactions_from_csv(self, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Load transactions from CSV file and match to accounts by account_id or IBAN.
        
        Args:
            accounts: List of accounts loaded from Excel
            
        Returns:
            List of transactions matched to accounts
        """
        # Build lookup maps for account matching
        account_id_map = {}  # account_id -> account
        iban_map = {}  # iban -> account
        
        for acc in accounts:
            acc_id = acc.get("account_id")
            iban = acc.get("iban")
            if acc_id:
                account_id_map[acc_id] = acc
            if iban:
                iban_map[iban] = acc
        
        # Find transactions CSV file
        transactions_file = None
        if self.transactions_csv_path and self.transactions_csv_path.exists():
            transactions_file = self.transactions_csv_path
        else:
            # Try common locations
            possible_paths = [
                Path("/workspace/data/transactions.csv"),
                Path("./data/transactions.csv"),
                Path("../data/transactions.csv"),
            ]
            for path in possible_paths:
                if path.exists():
                    transactions_file = path
                    break
        
        if not transactions_file:
            logger.warning("No transactions CSV file found. Returning empty transactions list.")
            return []
        
        logger.info(f"Loading transactions from CSV: {transactions_file}")
        
        try:
            # Load transactions CSV
            df = pd.read_csv(transactions_file, nrows=50000)  # Limit for performance
            logger.info(f"Loaded {len(df)} transaction rows from CSV")
            
            transactions = []
            
            for _, row in df.iterrows():
                # Try to find account identifiers in transaction
                from_account_id = None
                to_account_id = None
                
                # Check various column name patterns
                for col in df.columns:
                    col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                    
                    # From account
                    if not from_account_id:
                        if ('from' in col_lower and 'account' in col_lower) or \
                           ('debit' in col_lower and 'account' in col_lower) or \
                           ('account' in col_lower and 'id' in col_lower and 'counterparty' not in col_lower):
                            val = str(row[col]).strip()
                            if val and val != "nan" and val.lower() != "none":
                                from_account_id = val
                    
                    # To account
                    if not to_account_id:
                        if ('to' in col_lower and 'account' in col_lower) or \
                           ('credit' in col_lower and 'account' in col_lower) or \
                           ('counterparty' in col_lower and 'account' in col_lower):
                            val = str(row[col]).strip()
                            if val and val != "nan" and val.lower() != "none":
                                to_account_id = val
                
                # Handle Debit/Credit pattern (like in existing transactions.csv)
                if 'Debit/Credit' in df.columns:
                    debit_credit = str(row.get('Debit/Credit', '')).lower()
                    account_id_col = str(row.get('Account ID', '')).strip()
                    
                    if debit_credit == 'debit' and account_id_col:
                        from_account_id = account_id_col
                        # Try to get counterparty
                        to_account_id = str(row.get('counterparty_Account_ID', '')).strip()
                        if not to_account_id or to_account_id == "nan":
                            to_account_id = str(row.get('ext_counterparty_Account_ID', '')).strip()
                    elif debit_credit == 'credit' and account_id_col:
                        to_account_id = account_id_col
                        # Try to get counterparty
                        from_account_id = str(row.get('counterparty_Account_ID', '')).strip()
                        if not from_account_id or from_account_id == "nan":
                            from_account_id = str(row.get('ext_counterparty_Account_ID', '')).strip()
                
                # Match accounts
                from_account = None
                to_account = None
                from_account_found = False
                to_account_found = False
                
                if from_account_id:
                    # Try account_id first, then IBAN
                    from_account = account_id_map.get(from_account_id) or iban_map.get(from_account_id)
                    if from_account:
                        from_account_found = True
                
                if to_account_id:
                    # Try account_id first, then IBAN
                    to_account = account_id_map.get(to_account_id) or iban_map.get(to_account_id)
                    if to_account:
                        to_account_found = True
                
                # Only include transactions where at least one account is in our Excel dataset
                if (from_account_found or to_account_found) and from_account_id and to_account_id:
                    # Create placeholder for missing external accounts
                    if not from_account and from_account_id:
                        from_account = {
                            "account_id": from_account_id,
                            "iban": None,
                            "holder": "External Account",
                            "is_external": True
                        }
                    else:
                        from_account["is_external"] = False
                    
                    if not to_account and to_account_id:
                        to_account = {
                            "account_id": to_account_id,
                            "iban": None,
                            "holder": "External Account",
                            "is_external": True
                        }
                    else:
                        to_account["is_external"] = False
                    # Get amount
                    amount = None
                    for col in df.columns:
                        if 'amount' in col.lower():
                            try:
                                val = row[col]
                                if pd.notna(val):
                                    amount = float(val)
                                    break
                            except:
                                pass
                    
                    if amount:
                        transaction = {
                            "transaction_id": str(row.get("Transaction ID", f"tx_{len(transactions)}")),
                            "from_account": from_account.get("account_id"),
                            "to_account": to_account.get("account_id"),
                            "amount": amount,
                            "currency": str(row.get("Currency", "CHF")),
                            "date": str(row.get("Date", "")),
                            "type": str(row.get("Transfer_Type", "")),
                            "description": f"Transaction from {from_account.get('account_id')} to {to_account.get('account_id')}",
                            "is_external_from": from_account.get("is_external", False),
                            "is_external_to": to_account.get("is_external", False),
                        }
                        transactions.append(transaction)
            
            logger.info(f"Matched {len(transactions)} transactions to accounts")
            return transactions
            
        except Exception as e:
            logger.error(f"Error loading transactions from CSV: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _normalize_transactions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Normalize transaction data to standard format."""
        transactions = []
        
        for idx, row in df.iterrows():
            # Find amount (handles underscores, spaces, etc.)
            amount = None
            for col in df.columns:
                col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                if 'amount' in col_lower:
                    try:
                        val = row[col]
                        # Handle NaN
                        if pd.isna(val):
                            continue
                        amount = float(val)
                        break
                    except:
                        pass
            
            # Find from_account (handles underscores, spaces, etc.)
            from_account = None
            for col in df.columns:
                col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                if ('from' in col_lower and 'account' in col_lower) or \
                   'sender' in col_lower or \
                   ('debit' in col_lower and 'account' in col_lower):
                    val = str(row[col]).strip()
                    if val and val != "nan" and val.lower() != "none":
                        from_account = val
                        break
            
            # Find to_account (handles underscores, spaces, etc.)
            to_account = None
            for col in df.columns:
                col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                if ('to' in col_lower and 'account' in col_lower) or \
                   'receiver' in col_lower or \
                   ('credit' in col_lower and 'account' in col_lower) or \
                   'recipient' in col_lower:
                    val = str(row[col]).strip()
                    if val and val != "nan" and val.lower() != "none":
                        to_account = val
                        break
            
            # Find date
            date = None
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    date = str(row[col])
                    break
            
            # Find transaction type
            tx_type = None
            for col in df.columns:
                if 'type' in col.lower() or 'category' in col.lower():
                    tx_type = str(row[col])
                    break
            
            # Find currency
            currency = None
            for col in df.columns:
                if 'currency' in col.lower() or 'curr' in col.lower():
                    currency = str(row[col])
                    break
            
            # Find transaction ID
            tx_id = None
            for col in df.columns:
                if 'transaction' in col.lower() and 'id' in col.lower():
                    tx_id = str(row[col])
                    break
            
            if not tx_id:
                tx_id = f"tx_{idx}"
            
            # Only add if we have essential fields
            if from_account and to_account and amount is not None:
                tx = {
                    "transaction_id": tx_id,
                    "from_account": from_account,
                    "to_account": to_account,
                    "amount": float(amount),
                    "currency": currency if currency and currency != "nan" else "USD",
                    "date": date if date and date != "nan" else None,
                    "type": tx_type if tx_type and tx_type != "nan" else "unknown",
                    "description": f"Transaction {tx_id}"
                }
                transactions.append(tx)
        
        return transactions

