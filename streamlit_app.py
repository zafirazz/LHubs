"""
Streamlit UI for AML Casefile Generation System
"""

import streamlit as st
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
import requests
import time
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="AML Casefile Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🔍 AML Casefile Generation System")
st.markdown("Upload client data files to generate automated AML casefiles with risk assessment and SAR recommendations.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API endpoint configuration
    api_host = st.text_input("API Host", value="http://localhost:8000")
    
    st.markdown("---")
    st.markdown("### 📋 Instructions")
    st.markdown("""
    1. Upload CSV files containing transaction data
    2. Files should include columns like:
       - Transaction ID
       - Date
       - Amount
       - Currency
       - Account IDs
       - Transfer Type
    3. Click 'Process Files' to generate casefile
    4. Review results and download report
    """)

# Initialize session state
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "processing_result" not in st.session_state:
    st.session_state.processing_result = None
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = None

# File upload section
st.header("📤 Upload Files")

uploaded_files = st.file_uploader(
    "Upload CSV files",
    type=["csv", "txt", "json"],
    accept_multiple_files=True,
    help="Upload one or more CSV files containing transaction or client data"
)

if uploaded_files:
    st.session_state.uploaded_files = uploaded_files
    
    # Display uploaded files
    st.subheader("📁 Uploaded Files")
    file_info = []
    for file in uploaded_files:
        file_info.append({
            "Filename": file.name,
            "Size (KB)": f"{file.size / 1024:.2f}",
            "Type": file.type or "Unknown"
        })
    
    df_files = pd.DataFrame(file_info)
    st.dataframe(df_files, use_container_width=True)
    
    # Preview first CSV file
    if uploaded_files[0].name.endswith('.csv'):
        st.subheader("📊 File Preview")
        try:
            uploaded_files[0].seek(0)  # Reset file pointer
            preview_df = pd.read_csv(uploaded_files[0], nrows=10)
            st.dataframe(preview_df, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not preview file: {e}")

# Process files button
if st.session_state.uploaded_files:
    col1, col2 = st.columns([1, 4])
    
    with col1:
        process_button = st.button("🚀 Process Files", type="primary", use_container_width=True)
    
    if process_button:
        with st.spinner("Processing files... This may take a few moments."):
            try:
                # Create temporary directory for uploaded files
                temp_dir = tempfile.mkdtemp(prefix="aml_upload_")
                st.session_state.temp_dir = temp_dir
                
                # Save uploaded files to temp directory
                for file in st.session_state.uploaded_files:
                    file_path = os.path.join(temp_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                
                # Call API to process files
                api_url = f"{api_host}/api/v1/process-casefile"
                params = {"client_folder_path": temp_dir}
                
                response = requests.post(api_url, params=params, timeout=300)
                
                if response.status_code == 200:
                    st.session_state.processing_result = response.json()
                    st.success("✅ Files processed successfully!")
                else:
                    st.error(f"❌ Error processing files: {response.status_code}")
                    st.error(response.text)
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to API. Make sure the API server is running.")
                st.info("Start the API server with: `python -m src.main` or `uvicorn src.main:app`")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

# Display results
if st.session_state.processing_result:
    st.header("📊 Processing Results")
    result = st.session_state.processing_result
    
    # Casefile summary
    if "casefile" in result:
        casefile = result["casefile"]
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_score = casefile.get("risk_score", 0)
            risk_color = "🔴" if risk_score > 70 else "🟡" if risk_score > 40 else "🟢"
            st.metric("Risk Score", f"{risk_score}", delta=None)
            st.caption(f"{risk_color} Risk Level")
        
        with col2:
            st.metric("Status", result.get("status", "Unknown"))
        
        with col3:
            exec_time = result.get("execution_time_seconds", 0)
            st.metric("Processing Time", f"{exec_time:.2f}s")
        
        with col4:
            case_id = result.get("case_id", "N/A")
            st.metric("Case ID", case_id[:20] + "..." if len(case_id) > 20 else case_id)
        
        st.markdown("---")
        
        # Executive Summary
        if "executive_summary" in casefile and casefile["executive_summary"]:
            st.subheader("📝 Executive Summary")
            st.write(casefile["executive_summary"])
        
        # Summary details
        if "summary" in casefile and casefile["summary"]:
            st.subheader("📋 Summary Details")
            st.json(casefile["summary"])
        
        # Red Flags
        if "red_flags" in casefile and casefile["red_flags"]:
            st.subheader("🚩 Red Flags")
            red_flags = casefile["red_flags"]
            if isinstance(red_flags, dict):
                st.json(red_flags)
            elif isinstance(red_flags, list):
                for i, flag in enumerate(red_flags, 1):
                    st.write(f"**{i}. {flag.get('title', 'Red Flag')}**")
                    st.write(flag.get('description', ''))
                    st.write(f"Severity: {flag.get('severity', 'Unknown')}")
                    st.markdown("---")
        
        # Inconsistencies
        if "inconsistencies" in casefile and casefile["inconsistencies"]:
            st.subheader("⚠️ Detected Inconsistencies")
            inconsistencies = casefile["inconsistencies"]
            if isinstance(inconsistencies, dict):
                st.json(inconsistencies)
            elif isinstance(inconsistencies, list):
                for i, inc in enumerate(inconsistencies, 1):
                    st.write(f"**{i}. {inc.get('type', 'Inconsistency')}**")
                    st.write(inc.get('description', ''))
                    st.markdown("---")
        
        # SAR Recommendation
        if "sar_recommendation" in casefile and casefile["sar_recommendation"]:
            st.subheader("📋 SAR Recommendation")
            sar_rec = casefile["sar_recommendation"]
            
            if isinstance(sar_rec, dict):
                recommendation = sar_rec.get("recommendation", "Unknown")
                confidence = sar_rec.get("confidence", 0)
                reasoning = sar_rec.get("reasoning", "")
                
                # Display recommendation with color coding
                if recommendation.lower() == "yes":
                    st.error(f"🚨 **Recommendation: FILE SAR** (Confidence: {confidence}%)")
                elif recommendation.lower() == "no":
                    st.success(f"✅ **Recommendation: DO NOT FILE SAR** (Confidence: {confidence}%)")
                else:
                    st.warning(f"⚠️ **Recommendation: REVIEW REQUIRED** (Confidence: {confidence}%)")
                
                if reasoning:
                    st.write("**Reasoning:**")
                    st.write(reasoning)
                
                st.json(sar_rec)
            else:
                st.write(sar_rec)
        
        # Download results
        st.markdown("---")
        st.subheader("💾 Download Results")
        
        # Create JSON download
        json_str = json.dumps(result, indent=2)
        st.download_button(
            label="📥 Download JSON Report",
            data=json_str,
            file_name=f"casefile_{case_id}_{int(time.time())}.json",
            mime="application/json"
        )
    
    else:
        st.warning("No casefile data in response")
        st.json(result)

# Footer
st.markdown("---")
st.markdown("### ℹ️ About")
st.markdown("""
This system uses AI agents to analyze client transaction data and generate comprehensive AML casefiles.
The system performs:
- Data parsing and validation
- Risk assessment
- Inconsistency detection
- Red flag identification
- SAR filing recommendations
""")

# Cleanup temp directory on app restart
if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
    # Note: We don't delete immediately to allow download, but could add cleanup logic
    pass

