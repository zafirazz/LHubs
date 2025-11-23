"""
Streamlit App for AML Analysis Agent.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from agents.aml_analysis.aml_analysis_agent import AMLAnalysisAgent
from utils.auth import Authenticator
import logging

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="AML Compliance Analysis",
    page_icon="🔍",
    layout="wide"
)

# Initialize authenticator
if 'authenticator' not in st.session_state:
    st.session_state.authenticator = Authenticator(users_file=str(project_root / "users.json"))

# Initialize authentication state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Login page
if not st.session_state.authenticated:
    st.title("🔐 AML Analysis System - Login")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Please login to continue")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if st.session_state.authenticator.authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        
    
    st.stop()  # Stop execution if not authenticated

# Header with user info and logout
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🔍 AML Compliance & Analysis Agent")
with col2:
    st.markdown(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

st.markdown("""
Upload an Excel file containing **accounts AND transactions** for automated AML pattern detection.

**How it works:**
1. 🎓 **Agent Context**: Trained on regulatory data 
2. 📤 **Upload**: You provide complete CSV/Excel with accounts + transactions to analyze
3. 🔍 **Analysis**: Graph-based pattern detection finds suspicious activity
4. 📄 **Report**: Download comprehensive PDF AML report with findings

""")

# File upload
uploaded_file = st.file_uploader(
    "Upload Excel File (with accounts AND transactions)",
    type=['xlsx', 'xls', 'csv'],
    help="File must contain accounts and transactions."
)

if uploaded_file is not None:
    # Initialize agent
    if 'agent' not in st.session_state:
        with st.spinner("Initializing AML Analysis Agent..."):
            st.session_state.agent = AMLAnalysisAgent()
    
    # Analyze button
    if st.button("Analyze for AML Patterns", type="primary"):
        with st.spinner("Analyzing transaction data..."):
            try:
                # Read file bytes
                file_bytes = uploaded_file.read()
                
                # Process with agent
                result = st.session_state.agent.process({
                    "excel_file_bytes": file_bytes,
                    "filename": uploaded_file.name,
                    "generated_by": st.session_state.username  # Add logged-in user
                })
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                # Get data from result
                summary = result.get("summary", "No summary available")
                risk_assessment = result.get("risk_assessment", {})
                patterns = result.get("patterns_detected", [])
                accounts = result.get("accounts", [])
                transactions = result.get("transactions", [])
                risk_level = risk_assessment.get("overall_risk", "unknown")
                
                # === TOP METRICS ===
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if "high" in risk_level.lower() or "critical" in risk_level.lower():
                        st.metric("Risk Level", risk_level.upper(), delta="Critical", delta_color="inverse")
                    elif "medium" in risk_level.lower():
                        st.metric("Risk Level", risk_level.upper(), delta="Warning", delta_color="inverse")
                    else:
                        st.metric("Risk Level", risk_level.upper())
                with col2:
                    st.metric("Patterns Detected", len(patterns))
                with col3:
                    st.metric("Accounts Analyzed", len(accounts))
                with col4:
                    st.metric("Transactions Processed", len(transactions))
                
                st.markdown("---")
                
                # === VISUALIZATIONS ===
                if patterns and len(patterns) > 0:
                    st.subheader("📊 Analysis Dashboard")
                    
                    import pandas as pd
                    
                    # Create tabs
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📈 Pattern Distribution", 
                        "🎯 Severity Analysis", 
                        "👤 Account Risks", 
                        "💰 Transaction Analysis"
                    ])
                    
                    with tab1:
                        st.markdown("### Pattern Type Distribution")
                        
                        # Group patterns by type
                        pattern_types = {}
                        for pattern in patterns:
                            ptype = pattern.get("pattern_type", "unknown")
                            if ptype not in pattern_types:
                                pattern_types[ptype] = []
                            pattern_types[ptype].append(pattern)
                        
                        # Bar chart
                        pattern_df = pd.DataFrame({
                            'Pattern Type': [p.replace('_', ' ').title() for p in pattern_types.keys()],
                            'Count': [len(v) for v in pattern_types.values()]
                        })
                        st.bar_chart(pattern_df.set_index('Pattern Type'), height=300)
                        
                        # Pattern details
                        st.markdown("#### 📋 Pattern Details:")
                        for ptype, pattern_list in pattern_types.items():
                            with st.expander(f"{ptype.replace('_', ' ').title()} ({len(pattern_list)} detected)"):
                                for i, pattern in enumerate(pattern_list[:5], 1):
                                    st.markdown(f"""
                                    **Instance {i}:**
                                    - **Severity:** {pattern.get('severity', 'unknown').upper()}
                                    - **Accounts Involved:** {len(pattern.get('accounts_involved', []))}
                                    - **Total Amount:** {pattern.get('total_amount', 0):,.2f} CHF
                                    - **Description:** {pattern.get('description', 'N/A')}
                                    """)
                    
                    with tab2:
                        st.markdown("### Severity Distribution")
                        
                        # Count by severity
                        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
                        for pattern in patterns:
                            sev = pattern.get('severity', 'low').lower()
                            if sev in severity_counts:
                                severity_counts[sev] += 1
                        
                        col_a, col_b = st.columns([2, 1])
                        
                        with col_a:
                            # Bar chart
                            severity_df = pd.DataFrame({
                                'Severity': ['🚨 High', '⚠️ Medium', '🟡 Low'],
                                'Count': [severity_counts['high'], severity_counts['medium'], severity_counts['low']]
                            })
                            severity_df = severity_df[severity_df['Count'] > 0]
                            st.bar_chart(severity_df.set_index('Severity'), height=300, color='#FF4B4B')
                        
                        with col_b:
                            st.markdown("#### 📊 Summary")
                            st.metric("🚨 High Severity", severity_counts['high'])
                            st.metric("⚠️ Medium Severity", severity_counts['medium'])
                            st.metric("🟡 Low Severity", severity_counts['low'])
                            
                            total_severity_score = severity_counts['high'] * 3 + severity_counts['medium'] * 2 + severity_counts['low']
                            st.metric("Risk Score", total_severity_score)
                    
                    with tab3:
                        st.markdown("### Account Risk Analysis")
                        
                        # Calculate risk per account
                        account_risk = {}
                        for pattern in patterns:
                            for acc in pattern.get('accounts_involved', []):
                                if acc not in account_risk:
                                    account_risk[acc] = {
                                        'pattern_count': 0,
                                        'total_amount': 0,
                                        'max_severity': 'low',
                                        'patterns': []
                                    }
                                account_risk[acc]['pattern_count'] += 1
                                account_risk[acc]['total_amount'] += pattern.get('total_amount', 0)
                                account_risk[acc]['patterns'].append(pattern.get('pattern_type', 'unknown'))
                                
                                sev = pattern.get('severity', 'low')
                                if sev == 'high':
                                    account_risk[acc]['max_severity'] = 'high'
                                elif sev == 'medium' and account_risk[acc]['max_severity'] != 'high':
                                    account_risk[acc]['max_severity'] = 'medium'
                        
                        # Sort and display top 10
                        sorted_accounts = sorted(account_risk.items(), 
                                               key=lambda x: x[1]['pattern_count'], 
                                               reverse=True)[:10]
                        
                        if sorted_accounts:
                            # Bar chart
                            risk_df = pd.DataFrame({
                                'Account': [acc[:15] + '...' if len(acc) > 15 else acc 
                                          for acc, _ in sorted_accounts],
                                'Pattern Count': [data['pattern_count'] for _, data in sorted_accounts]
                            })
                            st.bar_chart(risk_df.set_index('Account'), height=300, color='#FF6B6B')
                            
                            # Top risky accounts
                            st.markdown("#### 🎯 Highest Risk Accounts:")
                            for i, (acc, data) in enumerate(sorted_accounts[:5], 1):
                                severity_icon = {
                                    'high': '🚨',
                                    'medium': '⚠️',
                                    'low': '🟡'
                                }[data['max_severity']]
                                
                                st.markdown(f"""
                                **{i}. {severity_icon} {acc[:35]}{'...' if len(acc) > 35 else ''}**
                                - Patterns Involved: {data['pattern_count']}
                                - Total Amount: {data['total_amount']:,.2f} CHF
                                - Risk Level: {data['max_severity'].upper()}
                                - Pattern Types: {', '.join(set(data['patterns']))}
                                """)
                    
                    with tab4:
                        st.markdown("### Transaction Volume Analysis")
                        
                        if transactions and len(transactions) > 0:
                            # Calculate statistics
                            total_amount = sum(abs(tx.get('amount', 0)) for tx in transactions)
                            avg_amount = total_amount / len(transactions)
                            flagged_tx_count = sum(len(p.get('transactions_involved', [])) for p in patterns)
                            
                            col_x, col_y, col_z = st.columns(3)
                            with col_x:
                                st.metric("Total Volume", f"{total_amount:,.2f} CHF")
                            with col_y:
                                st.metric("Average Amount", f"{avg_amount:,.2f} CHF")
                            with col_z:
                                st.metric("Flagged Transactions", flagged_tx_count)
                            
                            # Amount distribution over transactions
                            st.markdown("#### 📊 Amount Distribution")
                            amounts = [abs(tx.get('amount', 0)) for tx in transactions[:100]]  # Limit to 100
                            amount_df = pd.DataFrame({
                                'Transaction': range(1, len(amounts) + 1),
                                'Amount (CHF)': amounts
                            })
                            st.line_chart(amount_df.set_index('Transaction'), height=250)
                            
                            # Transaction types breakdown
                            tx_types = {}
                            for tx in transactions:
                                tx_type = tx.get('type', 'Unknown')
                                tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
                            
                            if tx_types:
                                st.markdown("#### 📋 Transaction Type Breakdown")
                                type_df = pd.DataFrame({
                                    'Type': list(tx_types.keys()),
                                    'Count': list(tx_types.values())
                                })
                                st.bar_chart(type_df.set_index('Type'), height=250, color='#4B7BFF')
                        else:
                            st.info("Transaction data not available for visualization.")
                
                else:
                    st.info("✅ No suspicious AML patterns detected. All transactions appear normal.")
                
                st.markdown("---")
                
                # === SUMMARY ===
                st.subheader("📋 Executive Summary")
                st.markdown(f"**Risk Assessment:** {risk_level.upper()}")
                st.text(risk_assessment.get("summary", ""))
                st.markdown(f"**Recommendation:** {risk_assessment.get('recommendation', '')}")
                
                if isinstance(summary, str):
                    st.text(summary)
                else:
                    st.text(summary.get("overview", "No detailed summary available"))
                
                st.markdown("---")
                
                # === PDF DOWNLOAD ===
                pdf_bytes = result.get("pdf_bytes")
                if pdf_bytes:
                    st.subheader("📄 Download Detailed Report")
                    col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 1])
                    with col_pdf2:
                        st.download_button(
                            label="📥 Download Full PDF Report",
                            data=pdf_bytes,
                            file_name=f"aml_analysis_report_{uploaded_file.name.replace('.xlsx', '')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                else:
                    st.warning("PDF report could not be generated.")
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.exception(e)

else:
    st.info("👆 Please upload an Excel file to begin analysis.")
    
    # Download template files
    st.markdown("### 📥 Download Templates")
    st.markdown("Choose a template to get started:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Safe template (no risk)
    with col1:
        st.markdown("#### ✅ Safe Template (No Risk)")
        try:
            safe_template_path = Path("/workspace/aml_template_safe_only.xlsx")
            if safe_template_path.exists():
                with open(safe_template_path, "rb") as file:
                    safe_bytes = file.read()
                
                st.download_button(
                    label="📥 Download Safe Template",
                    data=safe_bytes,
                    file_name="aml_template_safe.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary",
                    use_container_width=True
                )
                st.markdown("""
                **All legitimate transactions:**
                - 10 normal accounts
                - 18 safe transactions
                - No suspicious patterns
                
                *Proves low false positives!*
                """)
            else:
                st.warning("Safe template not found.")
        except Exception as e:
            st.warning(f"Could not load safe template: {e}")
    
    # Mixed template (normal + risky)
    with col2:
        st.markdown("#### 📊 Mixed Template (Normal + Risky)")
        try:
            mixed_template_path = Path("/workspace/aml_template_mixed_normal_and_risky.xlsx")
            if mixed_template_path.exists():
                with open(mixed_template_path, "rb") as file:
                    mixed_bytes = file.read()
                
                st.download_button(
                    label="📥 Download Mixed Template",
                    data=mixed_bytes,
                    file_name="aml_template_mixed.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary",
                    use_container_width=True
                )
                st.markdown("""
                **Realistic data with:**
                - 12 accounts (5 risky, 7 normal)
                - 21 transactions (13 suspicious, 8 normal)
                - Shows detection capability
                
                *Test with realistic mix!*
                """)
            else:
                st.warning("Mixed template not found.")
        except Exception as e:
            st.warning(f"Could not load mixed template: {e}")
    
    # Template with red flags
    with col3:
        st.markdown("#### 🚨 All Red Flags")
        try:
            example_template_path = Path("/workspace/aml_template_with_red_flags.xlsx")
            if example_template_path.exists():
                with open(example_template_path, "rb") as file:
                    example_bytes = file.read()
                
                st.download_button(
                    label="📥 Download Red Flags",
                    data=example_bytes,
                    file_name="aml_template_red_flags.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
                st.markdown("""
                **All suspicious patterns:**
                - 10 risky accounts
                - 14 suspicious transactions
                - All AML patterns
                
                *Stress test!*
                """)
            else:
                st.warning("Red flags template not found.")
        except Exception as e:
            st.warning(f"Could not load red flags template: {e}")
    
    # Template with suspicious descriptions
    with col4:
        st.markdown("#### 💬 Suspicious Descriptions")
        try:
            desc_template_path = Path("/workspace/aml_template_suspicious_descriptions.xlsx")
            if desc_template_path.exists():
                with open(desc_template_path, "rb") as file:
                    desc_bytes = file.read()
                
                st.download_button(
                    label="📥 Download Description Test",
                    data=desc_bytes,
                    file_name="aml_template_descriptions.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
                st.markdown("""
                **Tests keyword detection:**
                - 5 accounts
                - 12 transactions with keywords
                - Tests HIGH/MED/LOW severity
                
                *Tests description analysis!*
                """)
            else:
                st.warning("Description template not found.")
        except Exception as e:
            st.warning(f"Could not load description template: {e}")
    
    st.markdown("---")
    
    # Show example format
    with st.expander("📋 Expected File Format"):
        st.markdown("""
        ### Option 1: Excel with Two Sheets
        
        **Sheet 1 - Accounts:**
        - `account_id` - UUID format (e.g., cd2a1d48-f260-497e-8f51-5344b8e81d83)
        - `account_iban` - IBAN format (e.g., CH2774784884043139427)
        
        **Sheet 2 - Transactions:**
        - `transaction_id` - Unique ID
        - `from_account` - Sender account ID/IBAN
        - `to_account` - Receiver account ID/IBAN
        - `amount` - Transaction amount
        - `currency` - Currency code (e.g., CHF, EUR)
        - `date` - Transaction date
        - `type` - Transaction type (optional)
        
        ### Option 2: Single CSV with Combined Data
        Include all columns from both accounts and transactions in one file.
        
        **Important:** The agent uses `/workspace/data/` as **training context** (FINMA rules, normal patterns),
        then analyzes YOUR uploaded file for red flags. No database lookups!
        """)

