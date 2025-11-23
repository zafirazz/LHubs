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
import logging

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="AML Compliance Analysis",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 AML Compliance & Analysis Agent")
st.markdown("""
Upload an Excel file containing accounts and transactions for automated AML pattern detection.
The system will analyze transaction graphs and generate a comprehensive PDF report.
""")

# File upload
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=['xlsx', 'xls'],
    help="Excel file should contain sheets named 'accounts' and 'transactions'"
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
                    "filename": uploaded_file.name
                })
                
                # Display results
                st.success("Analysis completed!")
                
                # Summary
                st.subheader("Analysis Summary")
                st.text(result.get("summary", "No summary available"))
                
                # Risk assessment
                risk_assessment = result.get("risk_assessment", {})
                st.subheader("Risk Assessment")
                risk_level = risk_assessment.get("overall_risk", "unknown").upper()
                
                if "high" in risk_level.lower() or "critical" in risk_level.lower():
                    st.error(f"Risk Level: {risk_level}")
                elif "medium" in risk_level.lower():
                    st.warning(f"Risk Level: {risk_level}")
                else:
                    st.success(f"Risk Level: {risk_level}")
                
                st.text(risk_assessment.get("summary", ""))
                st.text(f"Recommendation: {risk_assessment.get('recommendation', '')}")
                
                # Patterns detected
                patterns = result.get("patterns_detected", [])
                st.subheader(f"Patterns Detected: {len(patterns)}")
                
                if patterns:
                    # Group by type
                    pattern_types = {}
                    for pattern in patterns:
                        ptype = pattern.get("pattern_type", "unknown")
                        if ptype not in pattern_types:
                            pattern_types[ptype] = []
                        pattern_types[ptype].append(pattern)
                    
                    for ptype, pattern_list in pattern_types.items():
                        with st.expander(f"{ptype.replace('_', ' ').title()} ({len(pattern_list)} instances)"):
                            for i, pattern in enumerate(pattern_list[:5], 1):  # Show first 5
                                st.write(f"**Pattern {i}:**")
                                st.write(f"- Severity: {pattern.get('severity', 'unknown')}")
                                st.write(f"- Accounts: {len(pattern.get('accounts_involved', []))}")
                                st.write(f"- Amount: {pattern.get('total_amount', 0):,.2f}")
                                st.write(f"- Description: {pattern.get('description', 'N/A')}")
                else:
                    st.info("No known AML patterns detected.")
                
                # PDF download
                pdf_bytes = result.get("pdf_bytes")
                if pdf_bytes:
                    st.subheader("Download Report")
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_bytes,
                        file_name="aml_analysis_report.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("PDF report could not be generated.")
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.exception(e)

else:
    st.info("👆 Please upload an Excel file to begin analysis.")
    
    # Download example file
    st.markdown("### 📥 Download Example File")
    st.markdown("Not sure about the format? Download this example Excel file to test the feature:")
    
    try:
        example_file_path = Path(__file__).parent / "test_accounts_streamlit.xlsx"
        if example_file_path.exists():
            with open(example_file_path, "rb") as file:
                example_bytes = file.read()
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.download_button(
                    label="📥 Download Example Excel",
                    data=example_bytes,
                    file_name="example_accounts.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                st.markdown("""
                **This example contains:**
                - 10 sample accounts
                - ~22 transactions
                - Correct column format
                """)
        else:
            st.warning("Example file not found. Please check EXCEL_TEST_DATA_FORMAT.md for manual format.")
    except Exception as e:
        st.warning(f"Could not load example file: {e}")
    
    st.markdown("---")
    
    # Show example format
    with st.expander("📋 Expected Excel Format"):
        st.markdown("""
        **Required Columns:**
        - `account_id` - UUID format (e.g., cd2a1d48-f260-497e-8f51-5344b8e81d83)
        - `account_iban` - IBAN format (e.g., CH2774784884043139427)
        
        **Sheet Name:** Any name is fine (e.g., Sheet1, Accounts, etc.)
        
        **Example:**
        ```
        account_id                              account_iban
        cd2a1d48-f260-497e-8f51-5344b8e81d83    CH2774784884043139427
        555add69-5a26-490f-9c42-6859e4da1938    CH3173462741202451725
        ```
        
        **Note:** The system will automatically load related transactions from the database
        based on the IBANs you provide.
        """)

