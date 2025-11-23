"""
Summary Generator - Pre-computes summaries from data for fast retrieval.
Run this once to generate summaries, then use them in ContextService.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generates pre-computed summaries from data files."""
    
    def __init__(self, data_dir: str = "/workspace/data"):
        self.data_dir = Path(data_dir)
        self.summaries: List[Dict[str, Any]] = []
    
    def generate_client_summaries(self) -> List[Dict[str, Any]]:
        """Generate summaries from client onboarding notes."""
        summaries = []
        notes_file = self.data_dir / "client_onboarding_notes.csv"
        
        if not notes_file.exists():
            logger.warning(f"Client notes file not found: {notes_file}")
            return summaries
        
        try:
            df = pd.read_csv(notes_file)
            logger.info(f"Processing {len(df)} client onboarding notes...")
            
            # Create summary categories
            age_groups = {}
            regions = {}
            communication_prefs = {}
            service_needs = {}
            
            for _, row in df.iterrows():
                note = str(row.get("Onboarding_Note", "")).lower()
                partner_id = row.get("Partner_ID", "unknown")
                
                # Extract age information
                if "year-old" in note or "years old" in note:
                    # Try to extract age
                    import re
                    age_match = re.search(r'(\d+)[-‑]?year[-‑]?old', note)
                    if age_match:
                        age = int(age_match.group(1))
                        age_group = f"{(age // 10) * 10}s"
                        if age_group not in age_groups:
                            age_groups[age_group] = []
                        age_groups[age_group].append(partner_id)
                
                # Extract region/location
                if "zurich" in note:
                    if "zurich" not in regions:
                        regions["zurich"] = []
                    regions["zurich"].append(partner_id)
                elif "aargau" in note:
                    if "aargau" not in regions:
                        regions["aargau"] = []
                    regions["aargau"].append(partner_id)
                elif "german border" in note:
                    if "northern_switzerland" not in regions:
                        regions["northern_switzerland"] = []
                    regions["northern_switzerland"].append(partner_id)
                
                # Extract communication preferences
                if "phone" in note or "telephone" in note:
                    if "phone" not in communication_prefs:
                        communication_prefs["phone"] = []
                    communication_prefs["phone"].append(partner_id)
                if "mobile app" in note or "mobile banking" in note:
                    if "mobile_app" not in communication_prefs:
                        communication_prefs["mobile_app"] = []
                    communication_prefs["mobile_app"].append(partner_id)
                
                # Extract service needs
                if "retirement" in note or "retirement planning" in note:
                    if "retirement_planning" not in service_needs:
                        service_needs["retirement_planning"] = []
                    service_needs["retirement_planning"].append(partner_id)
                if "investment" in note:
                    if "investment" not in service_needs:
                        service_needs["investment"] = []
                    service_needs["investment"].append(partner_id)
                if "savings" in note:
                    if "savings" not in service_needs:
                        service_needs["savings"] = []
                    service_needs["savings"].append(partner_id)
            
            # Create summary documents
            if age_groups:
                for age_group, clients in age_groups.items():
                    summaries.append({
                        "content": f"Client Demographics - Age Group {age_group}: {len(clients)} clients in this age group. Typical characteristics include professional backgrounds, stable income, and interest in long-term financial planning.",
                        "category": "client_demographics",
                        "subcategory": f"age_{age_group}",
                        "client_count": len(clients),
                        "metadata": {"age_group": age_group}
                    })
            
            if regions:
                for region, clients in regions.items():
                    summaries.append({
                        "content": f"Geographic Distribution - {region.title()}: {len(clients)} clients located in {region}. Clients in this region typically seek comprehensive banking services including day-to-day banking, savings, and investment options.",
                        "category": "geographic",
                        "subcategory": region,
                        "client_count": len(clients),
                        "metadata": {"region": region}
                    })
            
            if communication_prefs:
                for pref, clients in communication_prefs.items():
                    summaries.append({
                        "content": f"Communication Preferences - {pref.replace('_', ' ').title()}: {len(clients)} clients prefer {pref.replace('_', ' ')}. These clients value convenient and responsive service through their preferred channels.",
                        "category": "communication",
                        "subcategory": pref,
                        "client_count": len(clients),
                        "metadata": {"preference": pref}
                    })
            
            if service_needs:
                for need, clients in service_needs.items():
                    summaries.append({
                        "content": f"Service Needs - {need.replace('_', ' ').title()}: {len(clients)} clients require {need.replace('_', ' ')} services. These clients are looking for tailored solutions to support their financial goals.",
                        "category": "services",
                        "subcategory": need,
                        "client_count": len(clients),
                        "metadata": {"service": need}
                    })
            
            # Overall client profile summary
            total_clients = len(df)
            summaries.append({
                "content": f"Overall Client Profile: The bank serves {total_clients} clients with diverse needs. Most clients are professionals seeking comprehensive banking relationships including daily banking, savings strategies, and investment guidance. Common characteristics include stable income, preference for digital banking options, and interest in long-term financial planning including retirement and real estate investments.",
                "category": "overview",
                "subcategory": "client_profile",
                "client_count": total_clients,
                "metadata": {}
            })
            
            logger.info(f"Generated {len(summaries)} client summaries")
            
        except Exception as e:
            logger.error(f"Error generating client summaries: {e}")
            import traceback
            traceback.print_exc()
        
        return summaries
    
    def generate_transaction_summaries(self) -> List[Dict[str, Any]]:
        """Generate summaries from transaction data."""
        summaries = []
        transactions_file = self.data_dir / "transactions.csv"
        
        if not transactions_file.exists():
            logger.warning(f"Transactions file not found: {transactions_file}")
            return summaries
        
        try:
            # Read sample of transactions for analysis (first 10000 rows for speed)
            df = pd.read_csv(transactions_file, nrows=10000)
            logger.info(f"Analyzing {len(df)} transactions...")
            
            # Transaction type summary
            transfer_types = df["Transfer_Type"].value_counts()
            for transfer_type, count in transfer_types.head(10).items():
                type_df = df[df["Transfer_Type"] == transfer_type]
                avg_amount = type_df["Amount"].mean()
                total_amount = type_df["Amount"].sum()
                
                summaries.append({
                    "content": f"Transaction Type - {transfer_type}: {count:,} transactions of this type. Average transaction amount: {avg_amount:,.2f} {type_df['Currency'].iloc[0] if len(type_df) > 0 else 'CHF'}. Total volume: {total_amount:,.2f}. This transaction type represents a significant portion of bank activity.",
                    "category": "transactions",
                    "subcategory": f"type_{transfer_type}",
                    "transaction_count": count,
                    "metadata": {
                        "transfer_type": transfer_type,
                        "avg_amount": float(avg_amount),
                        "total_volume": float(total_amount)
                    }
                })
            
            # Currency summary
            currencies = df["Currency"].value_counts()
            for currency, count in currencies.items():
                currency_df = df[df["Currency"] == currency]
                avg_amount = currency_df["Amount"].mean()
                
                summaries.append({
                    "content": f"Currency Distribution - {currency}: {count:,} transactions in {currency}. Average transaction size: {avg_amount:,.2f} {currency}. This currency is actively used in the banking system.",
                    "category": "transactions",
                    "subcategory": f"currency_{currency}",
                    "transaction_count": count,
                    "metadata": {
                        "currency": currency,
                        "avg_amount": float(avg_amount)
                    }
                })
            
            # High-value transaction summary
            high_value = df[df["Amount"] > 10000]
            if len(high_value) > 0:
                summaries.append({
                    "content": f"High-Value Transactions: {len(high_value):,} transactions exceed 10,000. These transactions require enhanced due diligence and monitoring for AML compliance. Average high-value transaction: {high_value['Amount'].mean():,.2f}.",
                    "category": "compliance",
                    "subcategory": "high_value_transactions",
                    "transaction_count": len(high_value),
                    "metadata": {
                        "threshold": 10000,
                        "avg_amount": float(high_value['Amount'].mean())
                    }
                })
            
            # External counterparty summary
            external = df[df["ext_counterparty_country"].notna()]
            if len(external) > 0:
                countries = external["ext_counterparty_country"].value_counts()
                top_countries = countries.head(5)
                
                country_list = ", ".join([f"{country} ({count})" for country, count in top_countries.items()])
                summaries.append({
                    "content": f"Cross-Border Transactions: {len(external):,)} transactions involve external counterparties. Top countries: {country_list}. These transactions require additional compliance checks and monitoring for regulatory compliance.",
                    "category": "compliance",
                    "subcategory": "cross_border",
                    "transaction_count": len(external),
                    "metadata": {
                        "top_countries": top_countries.to_dict()
                    }
                })
            
            # Overall transaction summary
            total_tx = len(df)
            total_volume = df["Amount"].sum()
            summaries.append({
                "content": f"Transaction Overview: The system processes {total_tx:,} transactions with a total volume of {total_volume:,.2f}. Transaction patterns show diverse activity including domestic transfers, international payments, and various transaction types. Regular monitoring is essential for AML compliance.",
                "category": "overview",
                "subcategory": "transaction_overview",
                "transaction_count": total_tx,
                "metadata": {
                    "total_volume": float(total_volume)
                }
            })
            
            logger.info(f"Generated {len(summaries)} transaction summaries")
            
        except Exception as e:
            logger.error(f"Error generating transaction summaries: {e}")
            import traceback
            traceback.print_exc()
        
        return summaries
    
    def generate_account_summaries(self) -> List[Dict[str, Any]]:
        """Generate summaries from account data."""
        summaries = []
        account_file = self.data_dir / "account.csv"
        
        if not account_file.exists():
            logger.warning(f"Account file not found: {account_file}")
            return summaries
        
        try:
            df = pd.read_csv(account_file)
            logger.info(f"Processing {len(df)} accounts...")
            
            # Currency distribution
            currencies = df["account_currency"].value_counts()
            for currency, count in currencies.items():
                currency_df = df[df["account_currency"] == currency]
                summaries.append({
                    "content": f"Account Currency - {currency}: {count:,} accounts in {currency}. These accounts support transactions and services in {currency}, serving clients with international banking needs.",
                    "category": "accounts",
                    "subcategory": f"currency_{currency}",
                    "account_count": count,
                    "metadata": {"currency": currency}
                })
            
            # Account status summary
            active_accounts = df[df["account_close_date"].isna()]
            closed_accounts = df[df["account_close_date"].notna()]
            
            if len(active_accounts) > 0:
                summaries.append({
                    "content": f"Active Accounts: {len(active_accounts):,} accounts are currently active. These accounts are actively used for daily banking operations, transactions, and client services.",
                    "category": "accounts",
                    "subcategory": "active_accounts",
                    "account_count": len(active_accounts),
                    "metadata": {"status": "active"}
                })
            
            # Overall account summary
            summaries.append({
                "content": f"Account Overview: The bank manages {len(df):,} accounts across multiple currencies. Account services include standard banking operations, international transfers, and specialized financial products. Account management requires ongoing monitoring for compliance and risk assessment.",
                "category": "overview",
                "subcategory": "account_overview",
                "account_count": len(df),
                "metadata": {}
            })
            
            logger.info(f"Generated {len(summaries)} account summaries")
            
        except Exception as e:
            logger.error(f"Error generating account summaries: {e}")
            import traceback
            traceback.print_exc()
        
        return summaries
    
    def generate_graph_pattern_summaries(self) -> List[Dict[str, Any]]:
        """Generate summaries from graph pattern detection."""
        summaries = []
        
        try:
            from services.graph_analysis_service import GraphAnalysisService
            
            logger.info("Running graph pattern detection for summaries...")
            graph_service = GraphAnalysisService(data_dir=str(self.data_dir))
            patterns = graph_service.detect_patterns(force_recompute=False)
            
            if not patterns:
                logger.warning("No graph patterns detected")
                return summaries
            
            # Group patterns by type
            by_type = {}
            by_severity = {"high": [], "medium": [], "low": []}
            
            for pattern in patterns:
                ptype = pattern.get("pattern_type", "unknown")
                if ptype not in by_type:
                    by_type[ptype] = []
                by_type[ptype].append(pattern)
                
                severity = pattern.get("severity", "low")
                by_severity[severity].append(pattern)
            
            # Create summary for each pattern type
            for ptype, pattern_list in by_type.items():
                total_amount = sum(p.get("total_amount", 0) for p in pattern_list)
                total_accounts = set()
                for p in pattern_list:
                    total_accounts.update(p.get("accounts_involved", []))
                
                summaries.append({
                    "content": f"Graph Pattern - {ptype.replace('_', ' ').title()}: {len(pattern_list)} instances detected. Total amount involved: {total_amount:,.2f} CHF. Accounts involved: {len(total_accounts)}. This pattern type indicates potential money laundering structures in the transaction network.",
                    "category": "graph_patterns",
                    "subcategory": f"pattern_{ptype}",
                    "pattern_count": len(pattern_list),
                    "metadata": {
                        "pattern_type": ptype,
                        "total_amount": float(total_amount),
                        "account_count": len(total_accounts),
                        "instances": len(pattern_list)
                    }
                })
            
            # Create severity summary
            for severity, pattern_list in by_severity.items():
                if pattern_list:
                    summaries.append({
                        "content": f"Graph Pattern Severity - {severity.upper()}: {len(pattern_list)} {severity}-severity laundering patterns detected. These patterns require immediate compliance review and may indicate structured money movement designed to evade detection.",
                        "category": "compliance",
                        "subcategory": f"graph_severity_{severity}",
                        "pattern_count": len(pattern_list),
                        "metadata": {
                            "severity": severity,
                            "pattern_count": len(pattern_list)
                        }
                    })
            
            # Overall graph analysis summary
            summaries.append({
                "content": f"Graph-Based AML Analysis: {len(patterns)} laundering patterns detected across {len(by_type)} pattern types. Graph analysis reveals complex transaction structures including fan patterns, cycles, layered structures, and bipartite networks. These patterns are algorithmically detected and represent actual transaction graph structures that require compliance investigation.",
                "category": "overview",
                "subcategory": "graph_analysis_overview",
                "pattern_count": len(patterns),
                "metadata": {
                    "total_patterns": len(patterns),
                    "pattern_types": list(by_type.keys())
                }
            })
            
            logger.info(f"Generated {len(summaries)} graph pattern summaries")
            
        except Exception as e:
            logger.error(f"Error generating graph pattern summaries: {e}")
            import traceback
            traceback.print_exc()
        
        return summaries
    
    def generate_all_summaries(self) -> List[Dict[str, Any]]:
        """Generate all summaries from all data sources."""
        logger.info("Generating pre-computed summaries...")
        
        all_summaries = []
        
        # Generate summaries from each data source
        all_summaries.extend(self.generate_client_summaries())
        all_summaries.extend(self.generate_transaction_summaries())
        all_summaries.extend(self.generate_account_summaries())
        all_summaries.extend(self.generate_graph_pattern_summaries())  # Add graph patterns
        
        logger.info(f"Total summaries generated: {len(all_summaries)}")
        return all_summaries
    
    def save_summaries(self, summaries: List[Dict[str, Any]], output_file: str = "./data/compliance_summaries.json"):
        """Save summaries to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(summaries)} summaries to {output_path}")
        return output_path
    
    def load_summaries(self, summary_file: str = "./data/compliance_summaries.json") -> List[Dict[str, Any]]:
        """Load summaries from JSON file."""
        summary_path = Path(summary_file)
        
        if not summary_path.exists():
            logger.warning(f"Summary file not found: {summary_path}. Generating summaries...")
            summaries = self.generate_all_summaries()
            self.save_summaries(summaries, summary_file)
            return summaries
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        logger.info(f"Loaded {len(summaries)} summaries from {summary_path}")
        return summaries


if __name__ == "__main__":
    """Generate summaries when run directly."""
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    data_dir = "/workspace/data"
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    
    generator = SummaryGenerator(data_dir=data_dir)
    summaries = generator.generate_all_summaries()
    
    output_file = "./data/compliance_summaries.json"
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    generator.save_summaries(summaries, output_file)
    print(f"\n✓ Generated {len(summaries)} summaries")
    print(f"✓ Saved to: {output_file}")

