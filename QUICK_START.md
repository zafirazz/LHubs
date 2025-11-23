# AML Analysis Agent - Quick Start Guide

## What to Run

### Option 1: Streamlit Web App (Recommended for Demo)

```bash
cd /workspace/LHubs_Zafira
streamlit run streamlit_aml_app.py
```

Then:
1. Open browser to the URL shown (usually http://localhost:8501)
2. Upload Excel file with accounts and transactions
3. Click "Analyze for AML Patterns"
4. View results and download PDF report

### Option 2: Command Line Script

```bash
cd /workspace/LHubs_Zafira
python run_aml_analysis.py <path_to_excel_file.xlsx>
```

Example:
```bash
python run_aml_analysis.py /workspace/data/sample.xlsx
```

### Option 3: Python API

```python
from agents.aml_analysis import AMLAnalysisAgent

agent = AMLAnalysisAgent()
result = agent.process({
    "excel_file_path": "path/to/file.xlsx"
})

print(result["summary"])
print(f"PDF: {result['pdf_report_path']}")
```

## Prerequisites

### Install Dependencies

```bash
cd /workspace/LHubs_Zafira
pip install -r requirements.txt
```

Key dependencies:
- `pandas` - Data processing
- `openpyxl` - Excel file reading
- `networkx` - Graph analysis
- `matplotlib` - Visualizations
- `reportlab` - PDF generation
- `streamlit` - Web interface

### Excel File Format

Your Excel file should have two sheets:

**Sheet 1: Accounts** (name should contain "account")
- `Account ID` or `IBAN` (required)
- `Account Holder` or `Name` (optional)

**Sheet 2: Transactions** (name should contain "transaction")
- `From Account` or `Sender` (required)
- `To Account` or `Receiver` (required)
- `Amount` (required)
- `Date` (optional)
- `Transaction Type` (optional)
- `Currency` (optional)

## What Gets Generated

1. **Pattern Detection**: Graph-based AML pattern detection
2. **Risk Assessment**: Overall risk level and recommendation
3. **PDF Report** with:
   - Executive summary
   - Pattern detections with AML context
   - 4 visualizations:
     - Transaction network graph
     - Pattern-highlighted subgraph
     - Fund flow diagram
     - Risk heatmap

## Example Output

```
Analysis Results:
- Patterns Detected: 15
- Risk Level: HIGH
- Recommendation: Enhanced due diligence required. Consider STR filing.

Pattern Breakdown:
  - Fan Out: 8
  - Fan In: 4
  - Gather Scatter: 2
  - Simple Cycle: 1

PDF Report: /tmp/aml_analysis_report.pdf
```

## Troubleshooting

### "No transactions found"
- Check Excel file has a transactions sheet
- Verify column names match expected format
- Check that From/To Account columns exist

### "Import errors"
- Run: `pip install -r requirements.txt`
- Ensure you're in the correct directory

### "PDF generation failed"
- Check matplotlib backend (should use 'Agg')
- Verify temp directory is writable

## Next Steps

1. **Test with sample data**: Create a simple Excel file with test transactions
2. **Run Streamlit app**: `streamlit run streamlit_aml_app.py`
3. **Upload Excel file** via web interface
4. **Download PDF report** with analysis results

## Files Created

- `streamlit_aml_app.py` - Web interface
- `run_aml_analysis.py` - Command-line script
- `src/agents/aml_analysis/` - Main agent code
- `src/services/excel_loader.py` - Excel data loader
- `src/services/aml_context_rules.py` - AML rules engine
- `src/services/pdf_report_generator.py` - PDF generator

